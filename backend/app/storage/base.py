from abc import ABC, abstractmethod
from typing import Optional


class BaseStorageService(ABC):
    """Abstract interface for object storage (Local filesystem, S3, MinIO)."""

    @abstractmethod
    def save_file(self, content: bytes, filename: str, subfolder: str = "uploads") -> str:
        """Saves file bytes and returns storage key / path."""
        pass

    @abstractmethod
    def get_file(self, storage_path: str) -> bytes:
        """Reads file bytes from storage."""
        pass

    @abstractmethod
    def get_url(self, storage_path: str) -> str:
        """Returns publicly accessible or static URL for the asset."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage."""
        pass
