from backend.app.core.config import settings
from backend.app.storage.base import BaseStorageService
from backend.app.storage.local_storage import LocalStorageService
from backend.app.storage.s3_storage import S3StorageService


def get_storage_service() -> BaseStorageService:
    """Returns storage service based on configured backend (S3 or local disk)."""
    if getattr(settings, "STORAGE_BACKEND", "local").lower() == "s3":
        return S3StorageService(bucket=settings.OBJECT_STORAGE_BUCKET)
    return LocalStorageService()


storage_service = get_storage_service()

__all__ = [
    "BaseStorageService",
    "LocalStorageService",
    "S3StorageService",
    "get_storage_service",
    "storage_service",
]

