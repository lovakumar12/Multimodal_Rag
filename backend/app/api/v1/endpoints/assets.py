import mimetypes
from pathlib import Path
from fastapi import APIRouter, status
from fastapi.responses import Response
from backend.app.core.errors import NotFoundError
from backend.app.storage.local_storage import storage_service

router = APIRouter(tags=["Assets"])


@router.get("/assets/{file_path:path}")
async def get_asset(file_path: str):
    """Serves extracted images, rendered pages, and artifacts securely."""
    try:
        content = storage_service.get_file(file_path)
    except FileNotFoundError:
        raise NotFoundError("Asset", file_path)

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        ext = Path(file_path).suffix.lower()
        if ext == ".png":
            mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif ext == ".webp":
            mime_type = "image/webp"
        elif ext == ".pdf":
            mime_type = "application/pdf"
        else:
            mime_type = "application/octet-stream"

    return Response(
        content=content,
        media_type=mime_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
