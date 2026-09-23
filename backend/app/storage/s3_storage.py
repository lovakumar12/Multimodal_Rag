from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.storage.base import BaseStorageService
from backend.app.storage.local_storage import LocalStorageService


class S3StorageService(BaseStorageService):
    """S3 / MinIO compatible object storage client."""

    def __init__(self, bucket: str = "multimodal-rag"):
        self.bucket = bucket
        self._fallback = LocalStorageService()
        self._s3_client = None
        # Attempt boto3 initialization if available
        try:
            import boto3
            self._s3_client = boto3.client("s3")
        except Exception:
            logger.info("Boto3 or AWS credentials not configured. S3Storage falling back to LocalStorage.")

    def save_file(self, content: bytes, filename: str, subfolder: str = "uploads") -> str:
        if not self._s3_client:
            return self._fallback.save_file(content, filename, subfolder)

        import uuid
        from pathlib import Path
        key = f"{subfolder}/{uuid.uuid4().hex[:8]}_{Path(filename).name}"
        self._s3_client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return key

    def get_file(self, storage_path: str) -> bytes:
        if not self._s3_client:
            return self._fallback.get_file(storage_path)

        response = self._s3_client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()

    def get_url(self, storage_path: str) -> str:
        if not self._s3_client:
            return self._fallback.get_url(storage_path)

        return self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_path},
            ExpiresIn=3600,
        )

    def delete_file(self, storage_path: str) -> bool:
        if not self._s3_client:
            return self._fallback.delete_file(storage_path)

        self._s3_client.delete_object(Bucket=self.bucket, Key=storage_path)
        return True
