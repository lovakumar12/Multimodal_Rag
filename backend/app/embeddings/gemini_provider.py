from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.base import BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini embedding provider using text-embedding-004."""

    def __init__(self, model_name: str = "text-embedding-004"):
        self.model_name = model_name
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize GenAI embedding client: {e}")

    def embed_text(self, text: str) -> List[float]:
        if not self.client:
            raise RuntimeError("Gemini API key not configured")
        clean_text = text.replace("\n", " ").strip() or "empty"
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=clean_text,
        )
        return response.embeddings[0].values

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.client:
            raise RuntimeError("Gemini API key not configured")
        cleaned = [t.replace("\n", " ").strip() or "empty" for t in texts]
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=cleaned,
        )
        return [e.values for e in response.embeddings]

    @property
    def dimension(self) -> int:
        return 768
