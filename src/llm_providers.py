from abc import ABC, abstractmethod
from typing import Dict, List
import random
import logging
from livekit.plugins import openai, google
from livekit.agents import llm

from google.genai import types

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    def get_random_voice_for_gender(self, gender: str) -> str:
        """Get a random voice for the specified gender"""
        pass

    @abstractmethod
    def create_model(self, gender: str = "female") -> llm.RealtimeModel:
        """Create and return the LLM model"""
        pass


class GoogleLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider"""

    GENDER_VOICES: Dict[str, List[str]] = {
        "male": ["Puck", "Charon", "Fenrir"],
        "female": ["Aoede", "Kore"],
    }

    DEFAULT_MODEL = "gemini-2.5-flash-preview-native-audio-dialog"
    DEFAULT_TEMPERATURE = 0.8

    def get_random_voice_for_gender(self, gender: str) -> str:
        """Get a random voice for the specified gender"""
        gender = gender.lower()
        voices = self.GENDER_VOICES.get(gender, self.GENDER_VOICES["female"])
        selected_voice = random.choice(voices)
        logger.info(f"Google voice selection: gender='{gender}', available={voices}, selected='{selected_voice}'")
        return selected_voice

    def create_model(self, gender: str = "female") -> llm.RealtimeModel:
        voice = self.get_random_voice_for_gender(gender)

        return google.beta.realtime.RealtimeModel(
            model=self.DEFAULT_MODEL,
            voice=voice,
            temperature=self.DEFAULT_TEMPERATURE,
            _gemini_tools=[
                types.GoogleSearch(),
            ],
        )


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider"""

    GENDER_VOICES: Dict[str, List[str]] = {
        "male": ["onyx", "echo"],  # Removed 'alloy' as it's more neutral
        "female": ["nova", "shimmer"],
    }

    def get_random_voice_for_gender(self, gender: str) -> str:
        """Get a random voice for the specified gender"""
        gender = gender.lower()
        voices = self.GENDER_VOICES.get(gender, self.GENDER_VOICES["female"])
        selected_voice = random.choice(voices)
        logger.info(f"OpenAI voice selection: gender='{gender}', available={voices}, selected='{selected_voice}'")
        return selected_voice

    def create_model(self, gender: str = "female") -> llm.RealtimeModel:
        voice = self.get_random_voice_for_gender(gender)
        
        print(f"OpenAI: Selected voice '{voice}' for gender '{gender}'")

        return openai.realtime.RealtimeModel(
            model="gpt-4o-mini-realtime-preview-2024-12-17",
            voice=voice,
            temperature=0.8,
        )


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
            GoogleLLMProvider,  # Default to Google
        )
        return provider_class()

    @classmethod
    def create_llm(
        cls,
        provider_name: str,
        gender: str = "female",
    ) -> llm.RealtimeModel:
        """Create an LLM model for the given provider and gender"""
        provider = cls.get_provider(provider_name)
        return provider.create_model(gender)
