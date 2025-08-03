import asyncio
from datetime import datetime, timedelta
from typing import Optional
from livekit.agents import AgentSession


class SessionTimeManager:
    """Manages session timing and automatic termination"""
    
    def __init__(self, session: AgentSession, agent, duration_minutes: int):
        self.session = session
        self.agent = agent
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._warning_sent_5min = False
        self._warning_sent_1min = False
    
    async def start_monitoring(self):
        """Start monitoring session time"""
        self._monitoring_task = asyncio.create_task(self._monitor_time())
    
    async def _monitor_time(self):
        """Monitor time and send warnings/end session"""
        try:
            while True:
                elapsed = datetime.now() - self.start_time
                remaining = timedelta(minutes=self.duration_minutes) - elapsed
                
                # Check if time is up
                if remaining <= timedelta(0):
                    await self._end_session()
                    break
                
                # Send 5 minute warning
                if remaining <= timedelta(minutes=5) and not self._warning_sent_5min:
                    self._warning_sent_5min = True
                    await self.session.generate_reply(
                        instructions="Politely inform that there are about 5 minutes left in the session."
                    )
                
                # Send 1 minute warning
                elif remaining <= timedelta(minutes=1) and not self._warning_sent_1min:
                    self._warning_sent_1min = True
                    await self.session.generate_reply(
                        instructions="Politely inform that there's about 1 minute left, and start wrapping up."
                    )
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
    
    async def _end_session(self):
        """End the session gracefully"""
        await self.session.generate_reply(
            instructions="The session time is up. Thank the user warmly, summarize any key points from the session, and say goodbye."
        )
        # Give time for the goodbye message
        await asyncio.sleep(10)
        # The session will end when the agent's task completes
    
    def stop_monitoring(self):
        """Stop the monitoring task"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()