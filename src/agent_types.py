from abc import ABC, abstractmethod
from typing import Optional
from livekit.agents import Agent
from datetime import datetime, timedelta


class BaseSimplifiedAgent(Agent, ABC):
    """Base class for simplified description-based agents"""
    
    def __init__(self, agent_type: str, description: str, gender: str = "female", duration_minutes: int = 15):
        self.agent_type = agent_type
        self.description = description
        self.gender = gender
        # Duration is controlled by UI metadata
        self.duration_minutes = duration_minutes
        self.start_time = None
        
        instructions = self._generate_instructions()
        super().__init__(instructions=instructions)
    
    @abstractmethod
    def _generate_instructions(self) -> str:
        """Generate agent-specific instructions based on description"""
        pass
    
    @abstractmethod
    def get_greeting_instruction(self) -> str:
        """Get the initial greeting instruction"""
        pass
    
    def is_time_up(self) -> bool:
        """Check if session time has expired"""
        if not self.start_time:
            self.start_time = datetime.now()
            return False
        
        elapsed = datetime.now() - self.start_time
        return elapsed > timedelta(minutes=self.duration_minutes)
    
    def get_time_warning(self) -> Optional[str]:
        """Get a warning when approaching end of session"""
        if not self.start_time:
            return None
            
        elapsed = datetime.now() - self.start_time
        remaining = timedelta(minutes=self.duration_minutes) - elapsed
        
        # 5 minute warning
        if remaining <= timedelta(minutes=5) and remaining > timedelta(minutes=4.5):
            return "We have about 5 minutes left in our session."
        # 1 minute warning
        elif remaining <= timedelta(minutes=1) and remaining > timedelta(minutes=0.5):
            return "We're almost at the end of our session - about 1 minute remaining."
        
        return None


class InterviewAgent(BaseSimplifiedAgent):
    """Simplified interview agent"""
    
    def _generate_instructions(self) -> str:
        return f"""You are conducting a job interview based on the following description:

{self.description}

Interview Guidelines:
- Be professional yet friendly
- Ask relevant questions based on the description
- Listen actively and ask follow-up questions
- Provide constructive feedback when appropriate
- Keep track of time (session is {self.duration_minutes} minutes)
- Give time warnings at 5 minutes and 1 minute before end

Important:
- Adapt your interviewing style to match the role and level described
- If it's a technical role, ask technical questions
- If it's behavioral, focus on STAR method questions
- Stay in character throughout"""
    
    def get_greeting_instruction(self) -> str:
        return f"Introduce yourself as an interviewer and explain that you'll be conducting an interview based on: {self.description}. Make the candidate feel comfortable."


class PresentationAgent(BaseSimplifiedAgent):
    """Simplified presentation skills agent"""
    
    def _generate_instructions(self) -> str:
        return f"""You are a presentation skills coach helping a student practice based on:

{self.description}

Your role:
- Help them practice their presentation
- Provide feedback on delivery, clarity, and structure
- Be encouraging and constructive
- Session duration: {self.duration_minutes} minutes
- Give time warnings at 5 minutes and 1 minute before end

Coaching approach:
- Listen to their presentation
- Note strengths and areas for improvement
- Ask clarifying questions if needed
- Provide specific, actionable feedback
- Help build confidence"""
    
    def get_greeting_instruction(self) -> str:
        return f"Introduce yourself as a presentation coach and ask the student to tell you about their presentation topic: {self.description}. Be warm and encouraging."


class EnglishSpeakingAgent(BaseSimplifiedAgent):
    """Simplified English conversation agent"""
    
    def _generate_instructions(self) -> str:
        return f"""You are an English conversation partner helping a student practice speaking based on:

{self.description}

Your approach:
- Have a natural conversation about the topics mentioned
- Speak clearly and at an appropriate pace
- Gently correct major errors without interrupting flow
- Encourage the student to express themselves
- Session duration: {self.duration_minutes} minutes
- Give time warnings at 5 minutes and 1 minute before end

Important:
- Adapt your language complexity to the student's level
- Keep the conversation engaging and relevant
- Be patient and supportive
- Help with vocabulary when needed"""
    
    def get_greeting_instruction(self) -> str:
        return f"Greet the student warmly and suggest having a conversation about: {self.description}. Start with an easy, open-ended question."


class GeneralAgent(BaseSimplifiedAgent):
    """General purpose agent for any description"""
    
    def _generate_instructions(self) -> str:
        return f"""You are an AI assistant helping with the following:

{self.description}

Guidelines:
- Be helpful and professional
- Adapt your approach based on the description
- Provide relevant assistance
- Session duration: {self.duration_minutes} minutes
- Give time warnings at 5 minutes and 1 minute before end

Stay focused on the task described and be supportive throughout."""
    
    def get_greeting_instruction(self) -> str:
        return f"Greet the user and explain that you'll help them with: {self.description}"


class SimplifiedAgentFactory:
    """Factory to create agents based on type and description"""
    
    AGENT_TYPES = {
        "interview": InterviewAgent,
        "presentation": PresentationAgent,
        "english_speaking": EnglishSpeakingAgent,
        "general": GeneralAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, description: str, gender: str = "female", duration_minutes: int = 15) -> BaseSimplifiedAgent:
        """Create an agent based on type and description"""
        agent_class = cls.AGENT_TYPES.get(agent_type, GeneralAgent)
        return agent_class(agent_type, description, gender, duration_minutes)