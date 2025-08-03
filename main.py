from dotenv import load_dotenv
import json
from typing import Dict, Any

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, llm
from livekit.plugins import noise_cancellation
from prompts import get_interview_prompt
from llm_providers import LLMFactory

load_dotenv()


async def entrypoint(ctx: agents.JobContext) -> None:
    metadata_str = ctx.room.metadata
    print(f"Room metadata: {metadata_str}")

    # Parse metadata and generate appropriate prompt
    metadata: Dict[str, Any] = {}
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            print("Failed to parse metadata, using default prompt")

    # Generate interview prompt based on metadata
    interview_prompt: str = get_interview_prompt(metadata)
    interviewer_name: str = metadata.get("interviewer", {}).get("name", "John")
    print(f"Interview prompt generated for: {interviewer_name}")

    # Create LLM using the factory
    llm_instance: llm.RealtimeModel = LLMFactory.create_llm("google", interviewer_name)

    session: AgentSession = AgentSession(
        llm=llm_instance,
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=interview_prompt),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Start the interview by introducing yourself and explaining the interview format to the candidate."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
