from dotenv import load_dotenv
import json
import os
from typing import Dict, Any

import logging

from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, llm, metrics, JobProcess
from livekit.agents.voice import MetricsCollectedEvent

from livekit.plugins import noise_cancellation, silero
from src.llm_providers import LLMFactory
from src.agent_types import AgentFactory
from src.session_manager import SessionTimeManager
from src.metadata_transformer import transform_ui_metadata

logger = logging.getLogger("agent")

load_dotenv()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: agents.JobContext) -> None:
    # Connect to the room first to access metadata
    print(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_ALL)

    print(f"Connected to room: {ctx.room.name}")
    try:
        # Try to get room SID - it might be a property or async method
        if hasattr(ctx.room, "sid"):
            room_sid = ctx.room.sid
            if hasattr(room_sid, "__await__"):
                room_sid = await room_sid
            print(f"Room SID: {room_sid}")
        else:
            print("Room SID: Not available")
    except Exception as e:
        print(f"Room SID: Error accessing ({e})")

    # Now we can access the metadata
    metadata_str = ctx.room.metadata
    print(f"Room metadata: {metadata_str}")

    # Parse metadata
    raw_metadata: Dict[str, Any] = {}
    if metadata_str:
        try:
            raw_metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            print("Failed to parse metadata, using defaults")

    print(f"Raw metadata: {raw_metadata}")

    # Transform UI metadata to our simplified format
    metadata = transform_ui_metadata(raw_metadata)

    print(f"Transformed metadata: {metadata}")

    # Extract configuration
    agent_type: str = metadata["agent_type"]
    description: str = metadata["description"]
    gender: str = metadata["gender"]
    duration_minutes: int = metadata.get("duration_minutes", 30)

    # Create the appropriate agent
    custom_agent = AgentFactory.create_agent(
        agent_type=agent_type,
        description=description,
        gender=gender,
        duration_minutes=duration_minutes,
    )

    print(f"Created {agent_type} agent")
    print(f"Description: {description[:100]}...")
    print(f"Session duration: {custom_agent.duration_minutes} minutes")
    print(f"Gender voice: {gender}")

    # Create LLM with gender-based voice
    llm_instance: llm.RealtimeModel = LLMFactory.create_llm(
        provider_name="openai",
        gender=gender,
    )

    session: AgentSession = AgentSession(
        llm=llm_instance,
    )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=custom_agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Use agent-specific greeting (with retry for API readiness)
    handle = session.generate_reply(
        instructions=custom_agent.get_greeting_instruction()
    )
    await handle

    # Start session time monitoring
    time_manager = SessionTimeManager(
        session=session,
        agent=custom_agent,
        duration_minutes=custom_agent.duration_minutes,
    )
    await time_manager.start_monitoring()


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm)
    )
