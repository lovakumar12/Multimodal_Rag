from pathlib import Path
import uuid
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.storage.base import BaseStorageService


class LocalStorageService(BaseStorageService):
    """Local disk object storage implementation."""

    def __init__(self, base_dir: Path = settings.BASE_DATA_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, content: bytes, filename: str, subfolder: str = "uploads") -> str:
        folder = self.base_dir / subfolder
        folder.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename).suffix
        stem = Path(filename).stem
        unique_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        target_path = folder / unique_name
        target_path.write_bytes(content)

        relative_path = f"{subfolder}/{unique_name}"
        return relative_path

    def get_file(self, storage_path: str) -> bytes:
        file_path = self.base_dir / storage_path
        if not file_path.exists():
            raise FileNotFoundError(f"Storage file {storage_path} not found")
        return file_path.read_bytes()

    def get_url(self, storage_path: str) -> str:
        # FastAPI serves static assets at /api/v1/assets/{path}
        clean_path = storage_path.replace("\\", "/")
        return f"{settings.API_V1_PREFIX}/assets/{clean_path}"

    def delete_file(self, storage_path: str) -> bool:
        file_path = self.base_dir / storage_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False


storage_service = LocalStorageService()
