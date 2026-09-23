from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.retrieval.vector_store import vector_store

router = APIRouter(tags=["Health & Stats"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def ready(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # Check Database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {str(e)}"

    # Check vector index
    vector_count = vector_store.index.ntotal

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "vector_store": {
            "indexed_vectors": vector_count,
            "dimension": vector_store.dimension,
        },
        "storage": "local" if settings.UPLOAD_DIR.exists() else "unreachable",
    }


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    repo = DocumentRepository(db)
    stats = await repo.get_stats()
    stats["total_vectors"] = vector_store.index.ntotal
    return stats
