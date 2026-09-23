from abc import ABC, abstractmethod
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini generation provider."""

    def __init__(self, model_name: str = settings.LLM_MODEL):
        self.model_name = model_name
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini GenAI client: {e}")

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.client:
            raise RuntimeError("Gemini API key not configured")

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text.strip() if response.text else ""
        except Exception as e:
            logger.warning(f"Primary Gemini model {self.model_name} failed ({e}), attempting fallback model...")
            # If rate-limited or failed on 3.5-flash-lite, try 3.6-flash or 3.5-flash
            alt_model = "gemini-3.6-flash" if "3.5" in self.model_name else "gemini-3.5-flash-lite"
            try:
                response = self.client.models.generate_content(
                    model=alt_model,
                    contents=prompt,
                    config=config,
                )
                return response.text.strip() if response.text else ""
            except Exception as inner_e:
                logger.error(f"Fallback Gemini model {alt_model} also failed: {inner_e}")
                raise inner_e


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI generation provider."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                import openai
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.client:
            raise RuntimeError("OpenAI API key not configured")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()


class LocalFallbackLLMProvider(BaseLLMProvider):
    """Fallback generator for local testing or when external API keys are unavailable."""

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        return (
            "Based on the retrieved document evidence provided in context, the system has extracted "
            "the corresponding sections, tables, and visual artifacts as cited below."
        )


def get_llm_provider() -> BaseLLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()
    try:
        if provider_name == "gemini" and settings.GEMINI_API_KEY:
            return GeminiLLMProvider()
        elif provider_name == "openai" and settings.OPENAI_API_KEY:
            return OpenAILLMProvider()
    except Exception as e:
        logger.warning(f"Failed to initialize primary LLM {provider_name}: {e}. Using fallback.")

    return LocalFallbackLLMProvider()
