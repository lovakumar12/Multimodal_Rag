from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.storage.base import BaseStorageService
from backend.app.storage.local_storage import LocalStorageService


class S3StorageService(BaseStorageService):
    """S3 / MinIO compatible object storage client."""

    def __init__(self, bucket: Optional[str] = None):
        self.bucket = bucket or settings.OBJECT_STORAGE_BUCKET
        self._fallback = LocalStorageService()
        self._s3_client = None
        # Attempt boto3 initialization if available
        try:
            import boto3
            client_kwargs = {
                "region_name": settings.AWS_REGION,
            }
            if settings.OBJECT_STORAGE_ENDPOINT:
                client_kwargs["endpoint_url"] = settings.OBJECT_STORAGE_ENDPOINT
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

            self._s3_client = boto3.client("s3", **client_kwargs)
            logger.info(f"Initialized S3StorageService connected to bucket: {self.bucket} ({settings.AWS_REGION})")
        except Exception as e:
            logger.warning(f"Could not initialize S3 client ({e}). S3Storage falling back to LocalStorage.")

    def save_file(self, content: bytes, filename: str, subfolder: str = "uploads") -> str:
        if not self._s3_client:
            return self._fallback.save_file(content, filename, subfolder)

        import uuid
        import mimetypes
        from pathlib import Path

        suffix = Path(filename).suffix
        stem = Path(filename).stem
        key = f"{subfolder}/{uuid.uuid4().hex[:8]}_{stem}{suffix}"

        put_kwargs = {"Bucket": self.bucket, "Key": key, "Body": content}
        mime, _ = mimetypes.guess_type(filename)
        if mime:
            put_kwargs["ContentType"] = mime

        self._s3_client.put_object(**put_kwargs)
        return key

    def get_file(self, storage_path: str) -> bytes:
        if not self._s3_client:
            return self._fallback.get_file(storage_path)

        response = self._s3_client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()

    def get_url(self, storage_path: str) -> str:
        if not self._s3_client:
            return self._fallback.get_url(storage_path)

        try:
            return self._s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_path},
                ExpiresIn=3600,
            )
        except Exception:
            return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{storage_path}"

    def delete_file(self, storage_path: str) -> bool:
        if not self._s3_client:
            return self._fallback.delete_file(storage_path)

        self._s3_client.delete_object(Bucket=self.bucket, Key=storage_path)
        return True
