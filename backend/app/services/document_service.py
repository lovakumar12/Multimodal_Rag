from pathlib import Path
from typing import List, Optional
from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import NotFoundError
from backend.app.core.security import validate_file_upload
from backend.app.models.entities import Document
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.schemas.document import (
    DocumentDetailResponse,
    DocumentPageResponse,
    DocumentResponse,
    DocumentStatusResponse,
    ExtractedImageResponse,
    ExtractedTableResponse,
)
from backend.app.storage.local_storage import storage_service
from backend.app.workers.ingestion_worker import run_ingestion_task


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DocumentRepository(session)
        self.storage = storage_service

    async def upload_document(
        self,
        kb_id: str,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> DocumentResponse:
        content = await file.read()
        file_size = len(content)

        # 1. Security & File Validation
        sanitized_filename = validate_file_upload(
            filename=file.filename or "unnamed_document",
            file_size=file_size,
            content_type=file.content_type,
        )

        ext = Path(sanitized_filename).suffix.lstrip(".").lower()
        file_type = "image" if ext in ["png", "jpg", "jpeg", "webp"] else ext

        # 2. Persist to storage
        storage_path = self.storage.save_file(
            content=content,
            filename=sanitized_filename,
            subfolder="uploads",
        )

        # 3. Create Document DB record
        doc = await self.repo.create(
            kb_id=kb_id,
            filename=sanitized_filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
        )
        await self.session.commit()

        # 4. Dispatch Async Ingestion Worker
        background_tasks.add_task(run_ingestion_task, doc.id)

        return DocumentResponse.model_validate(doc)

    async def get_document_status(self, document_id: str) -> DocumentStatusResponse:
        doc = await self.repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError("Document", document_id)
        return DocumentStatusResponse.model_validate(doc)

    async def get_document_detail(self, document_id: str) -> DocumentDetailResponse:
        doc = await self.repo.get_detail(document_id)
        if not doc:
            raise NotFoundError("Document", document_id)

        pages_resp = []
        for p in doc.pages:
            images_resp = [
                ExtractedImageResponse(
                    id=img.id,
                    page_id=p.id,
                    page_number=p.page_number,
                    image_index=img.image_index,
                    asset_url=img.asset_url,
                    width=img.width,
                    height=img.height,
                    caption=img.caption,
                    semantic_description=img.semantic_description,
                    ocr_text=img.ocr_text,
                    is_diagram_or_chart=img.is_diagram_or_chart,
                )
                for img in p.images
            ]
            tables_resp = [
                ExtractedTableResponse(
                    id=tbl.id,
                    page_id=p.id,
                    page_number=p.page_number,
                    table_index=tbl.table_index,
                    headers_json=tbl.headers_json,
                    rows_json=tbl.rows_json,
                    markdown_content=tbl.markdown_content,
                    caption=tbl.caption,
                )
                for tbl in p.tables
            ]
            pages_resp.append(
                DocumentPageResponse(
                    id=p.id,
                    page_number=p.page_number,
                    text_content=p.text_content,
                    width=p.width,
                    height=p.height,
                    rendered_image_path=self.storage.get_url(p.rendered_image_path) if p.rendered_image_path else None,
                    summary=p.summary,
                    images=images_resp,
                    tables=tables_resp,
                )
            )

        return DocumentDetailResponse(
            id=doc.id,
            kb_id=doc.kb_id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            page_count=doc.page_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            pages=pages_resp,
            images_count=len(doc.images) if doc.images else 0,
            tables_count=len(doc.tables) if doc.tables else 0,
            chunks_count=len(doc.chunks) if doc.chunks else 0,
        )

    async def list_documents(self, kb_id: Optional[str] = None) -> List[DocumentResponse]:
        docs = await self.repo.list_by_kb(kb_id)
        return [DocumentResponse.model_validate(d) for d in docs]

    async def delete_document(self, document_id: str) -> bool:
        doc = await self.repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError("Document", document_id)
        # Delete original file
        self.storage.delete_file(doc.storage_path)
        success = await self.repo.delete(document_id)
        await self.session.commit()
        return success
