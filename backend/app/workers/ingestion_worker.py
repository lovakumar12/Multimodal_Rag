import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.logging import logger
from backend.app.ingestion.pipeline import IngestionPipeline


async def run_ingestion_task(document_id: str) -> None:
    """Async background task that processes document ingestion without blocking HTTP requests."""
    logger.info(f"Worker picked up ingestion task for document: {document_id}")
    async with AsyncSessionLocal() as session:
        try:
            pipeline = IngestionPipeline(session)
            success = await pipeline.process_document(document_id)
            if success:
                logger.info(f"Worker completed ingestion for document: {document_id}")
            else:
                logger.warning(f"Worker marked ingestion as failed for document: {document_id}")
        except Exception as e:
            logger.error(f"Worker unexpected failure for document {document_id}: {e}")
        finally:
            await session.close()
