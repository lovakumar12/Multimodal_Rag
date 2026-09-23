from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.base import BaseEmbeddingProvider
from backend.app.embeddings.sentence_transformers_provider import SentenceTransformersEmbeddingProvider
from backend.app.embeddings.gemini_provider import GeminiEmbeddingProvider
from backend.app.embeddings.openai_provider import OpenAIEmbeddingProvider

_cached_provider = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Returns the configured embedding provider with graceful local fallback."""
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    provider_name = settings.EMBEDDING_PROVIDER.lower()
    try:
        if provider_name == "gemini" and settings.GEMINI_API_KEY:
            _cached_provider = GeminiEmbeddingProvider()
            return _cached_provider
        elif provider_name == "openai" and settings.OPENAI_API_KEY:
            _cached_provider = OpenAIEmbeddingProvider()
            return _cached_provider
    except Exception as e:
        logger.warning(f"Error initializing {provider_name} embedding provider: {e}. Falling back to SentenceTransformers.")

    _cached_provider = SentenceTransformersEmbeddingProvider()
    return _cached_provider
