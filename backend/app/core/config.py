from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Workspace root is two levels up from backend/app/core
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=[
            str(BACKEND_DIR / ".env"),
            str(ROOT_DIR / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Multimodal RAG Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]

    # Storage Paths
    BASE_DATA_DIR: Path = ROOT_DIR / "data"
    UPLOAD_DIR: Path = ROOT_DIR / "data" / "uploads"
    ASSET_DIR: Path = ROOT_DIR / "data" / "assets"
    THUMBNAIL_DIR: Path = ROOT_DIR / "data" / "thumbnails"
    PAGE_DIR: Path = ROOT_DIR / "data" / "pages"

    # Database
    DATABASE_URL: str = Field(
        default=f"sqlite+aiosqlite:///{ROOT_DIR / 'data' / 'multimodal_rag.db'}"
    )
    POSTGRES_VECTOR_EXTENSION: bool = True

    # Vector Storage
    VECTOR_STORE_TYPE: str = "faiss"  # "pgvector" or "faiss"
    VECTOR_DIMENSION: int = 384  # default all-MiniLM-L6-v2 dimension

    # Providers & Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None

    # Embeddings
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # "sentence-transformers", "gemini", "openai"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # LLM & Generation
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", "ollama"
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    FALLBACK_LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5vl:3b"

    # Vision & Image Captioning
    VISION_PROVIDER: str = "gemini"  # "gemini", "openai", "heuristic"
    VISION_MODEL: str = "gemini-3.5-flash-lite"
    AUTO_DESCRIBE_IMAGES: bool = True

    # Image Relevance Scoring Weights
    WEIGHT_DESC_SIM: float = 0.35
    WEIGHT_TEXT_SIM: float = 0.25
    WEIGHT_CAPTION_SIM: float = 0.20
    WEIGHT_PAGE_SIM: float = 0.10
    WEIGHT_CO_OCCURRENCE: float = 0.10
    IMAGE_RELEVANCE_THRESHOLD: float = 0.40
    MAX_RETURNED_VISUALS: int = 3

    # File Ingestion Limits
    MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".pptx", ".docx", ".png", ".jpg", ".jpeg", ".webp"]

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150


settings = Settings()

# Ensure local directories exist
for folder in [settings.BASE_DATA_DIR, settings.UPLOAD_DIR, settings.ASSET_DIR, settings.THUMBNAIL_DIR, settings.PAGE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
