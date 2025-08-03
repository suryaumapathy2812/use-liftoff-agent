from abc import ABC, abstractmethod
from typing import Dict, Union
from livekit.plugins import openai, google
from livekit.agents import llm


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def get_voice_for_interviewer(self, interviewer_name: str) -> str:
        """Get the appropriate voice for an interviewer"""
        pass
    
    @abstractmethod
    def create_model(self, interviewer_name: str) -> llm.RealtimeModel:
        """Create and return the LLM model"""
        pass


class GoogleLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider"""
    
    VOICE_MAPPING: Dict[str, str] = {
        "John": "Puck",       # Male voice for technical interviewer
        "Richard": "Charon",  # Professional male voice for PM
        "Sarah": "Aoede",     # Female voice for senior interviewer
    }
    
    DEFAULT_MODEL = "gemini-2.5-flash-preview-native-audio-dialog"
    DEFAULT_TEMPERATURE = 0.8
    
    def get_voice_for_interviewer(self, interviewer_name: str) -> str:
        return self.VOICE_MAPPING.get(interviewer_name, "Puck")
    
    def create_model(self, interviewer_name: str) -> llm.RealtimeModel:
        voice = self.get_voice_for_interviewer(interviewer_name)
        return google.beta.realtime.RealtimeModel(
            model=self.DEFAULT_MODEL,
            voice=voice,
            temperature=self.DEFAULT_TEMPERATURE,
        )


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider"""
    
    VOICE_MAPPING: Dict[str, str] = {
        "John": "alloy",      # Neutral male voice for technical
        "Richard": "onyx",    # Deeper male voice for PM
        "Sarah": "nova",      # Female voice for senior
    }
    
    def get_voice_for_interviewer(self, interviewer_name: str) -> str:
        return self.VOICE_MAPPING.get(interviewer_name, "alloy")
    
    def create_model(self, interviewer_name: str) -> llm.RealtimeModel:
        voice = self.get_voice_for_interviewer(interviewer_name)
        return openai.realtime.RealtimeModel(voice=voice)


class LLMFactory:
    """Factory class to create appropriate LLM providers"""
    
    _providers = {
        "google": GoogleLLMProvider,
        "openai": OpenAILLMProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> BaseLLMProvider:
        """Get an instance of the requested provider"""
        provider_class = cls._providers.get(
            provider_name.lower(), 
            GoogleLLMProvider  # Default to Google
        )
        return provider_class()
    
    @classmethod
    def create_llm(cls, provider_name: str, interviewer_name: str = "John") -> llm.RealtimeModel:
        """Create an LLM model for the given provider and interviewer"""
        provider = cls.get_provider(provider_name)
        return provider.create_model(interviewer_name)