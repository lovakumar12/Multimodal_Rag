from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.base import BaseEmbeddingProvider


class SentenceTransformersEmbeddingProvider(BaseEmbeddingProvider):
    """Local embedding provider using SentenceTransformers with lazy loading."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._dim = 384

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformers model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
        return self._model

    def embed_text(self, text: str) -> List[float]:
        model = self._get_model()
        clean_text = text.replace("\n", " ").strip() or "empty"
        vec = model.encode(clean_text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        cleaned = [t.replace("\n", " ").strip() or "empty" for t in texts]
        vecs = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
        return vecs.tolist()

    @property
    def dimension(self) -> int:
        return self._dim
