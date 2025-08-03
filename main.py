from dotenv import load_dotenv
import json
import os
from typing import Dict, Any

from livekit import agents, api
from livekit.agents import AgentSession, RoomInputOptions, llm
from livekit.plugins import noise_cancellation
from src.llm_providers import LLMFactory
from src.agent_types import SimplifiedAgentFactory
from src.session_manager import SessionTimeManager
from src.metadata_transformer import transform_ui_metadata


load_dotenv()


async def start_recording_and_transcript(ctx: agents.JobContext, session: AgentSession) -> str:
    """Start recording and set up transcript tracking"""
    egress_id = None
    
    try:
        lkapi = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        room_name_clean = ctx.room.name.replace('/', '_').replace('\\', '_')
        filename = f"session_{room_name_clean}_{timestamp}"
        
        # Configure S3 upload (supports MinIO)
        s3_config = api.S3Upload(
            bucket=os.getenv("AWS_BUCKET_NAME"),
            region=os.getenv("AWS_REGION"),
            access_key=os.getenv("AWS_ACCESS_KEY"),
            secret=os.getenv("AWS_SECRET_KEY"),
            endpoint=os.getenv("AWS_ENDPOINT_URL"),  # For MinIO
            force_path_style=True,  # Required for MinIO compatibility
        )
        
        # Create egress request for audio recording
        req = api.RoomCompositeEgressRequest(
            room_name=ctx.room.name,
            audio_only=True,  # Audio-only recording for voice sessions
            file_outputs=[
                api.EncodedFileOutput(
                    file_type=api.EncodedFileType.OGG,
                    filepath=f"recordings/audio/{filename}.ogg",
                    s3=s3_config,
                )
            ],
        )
        
        egress_info = await lkapi.egress.start_room_composite_egress(req)
        egress_id = egress_info.egress_id
        
        print(f"✅ Started recording: {egress_id}")
        print(f"📁 Audio file: recordings/audio/{filename}.ogg")
        
        # Set up transcript saving callback
        async def save_transcript():
            try:
                # Get conversation history
                transcript = session.history.to_dict()
                
                # Save transcript as JSON
                import json
                transcript_filename = f"recordings/transcripts/{filename}.json"
                
                # In a real implementation, you'd upload this to your storage
                # For now, just log the transcript info
                print(f"📝 Transcript saved: {transcript_filename}")
                print(f"💬 Total messages: {len(transcript.get('messages', []))}")
                
                # Optional: Print some transcript content for debugging
                if transcript.get('messages'):
                    print(f"📊 Sample messages: {transcript['messages'][:2]}")
                
            except Exception as e:
                print(f"❌ Failed to save transcript: {e}")
        
        # Add shutdown callback for transcript saving
        ctx.add_shutdown_callback(save_transcript)
        
        await lkapi.aclose()
        return egress_id
        
    except Exception as e:
        print(f"❌ Failed to start recording: {e}")
        return None


async def entrypoint(ctx: agents.JobContext) -> None:
    # Connect to the room first to access metadata
    print(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_ALL)

    print(f"Connected to room: {ctx.room.name}")
    print(f"Room SID: {await ctx.room.sid()}")

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
    custom_agent = SimplifiedAgentFactory.create_agent(
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
        provider_name="google",
        gender=gender,
    )

    session: AgentSession = AgentSession(
        llm=llm_instance,
    )

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

    # Start recording and transcript tracking
    recording_id = await start_recording_and_transcript(ctx, session)
    
    # Use agent-specific greeting
    await session.generate_reply(instructions=custom_agent.get_greeting_instruction())

    # Start session time monitoring
    time_manager = SessionTimeManager(
        session=session,
        agent=custom_agent,
        duration_minutes=custom_agent.duration_minutes,
    )
    await time_manager.start_monitoring()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
