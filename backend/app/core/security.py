import re
from pathlib import Path
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.errors import FileTooLargeError, UnsupportedMediaTypeError, ValidationError


def sanitize_filename(filename: str) -> str:
    """Sanitizes uploaded filename to prevent directory traversal and injection attacks."""
    # Strip any directory components
    clean_name = Path(filename).name
    # Keep alphanumeric, dashes, underscores, dots
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_name)
    # Remove leading dots or slashes
    clean_name = clean_name.lstrip("._")
    if not clean_name:
        clean_name = "unnamed_document"
    return clean_name


def validate_file_upload(filename: str, file_size: int, content_type: Optional[str] = None) -> str:
    """Validates file upload size, name, and extension."""
    if not filename:
        raise ValidationError("Uploaded file must have a valid name")

    sanitized = sanitize_filename(filename)
    ext = Path(sanitized).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UnsupportedMediaTypeError(filename=sanitized, ext=ext)

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(size=file_size, limit=settings.MAX_FILE_SIZE_BYTES)

    return sanitized
