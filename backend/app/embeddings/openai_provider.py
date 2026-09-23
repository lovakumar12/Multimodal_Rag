from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider using text-embedding-3-small."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                import openai
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI embedding client: {e}")

    def embed_text(self, text: str) -> List[float]:
        if not self.client:
            raise RuntimeError("OpenAI API key not configured")
        clean_text = text.replace("\n", " ").strip() or "empty"
        res = self.client.embeddings.create(input=[clean_text], model=self.model_name)
        return res.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.client:
            raise RuntimeError("OpenAI API key not configured")
        cleaned = [t.replace("\n", " ").strip() or "empty" for t in texts]
        res = self.client.embeddings.create(input=cleaned, model=self.model_name)
        return [item.embedding for item in res.data]

    @property
    def dimension(self) -> int:
        return 1536
