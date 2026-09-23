from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.entities import (
    Document,
    DocumentPage,
    DocumentSection,
    ContentBlock,
    TextChunk,
    ExtractedTable,
    ExtractedImage,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        kb_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Document:
        doc = Document(
            kb_id=kb_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            status="PENDING",
            metadata_json=metadata_json or {},
        )
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_detail(self, document_id: str) -> Optional[Document]:
        query = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.pages).selectinload(DocumentPage.images),
                selectinload(Document.pages).selectinload(DocumentPage.tables),
                selectinload(Document.sections),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_kb(self, kb_id: Optional[str] = None) -> List[Document]:
        query = select(Document).order_by(Document.created_at.desc())
        if kb_id:
            query = query.where(Document.kb_id == kb_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        document_id: str,
        status: str,
        page_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        doc = await self.get_by_id(document_id)
        if not doc:
            return None
        doc.status = status
        if page_count is not None:
            doc.page_count = page_count
        if error_message is not None:
            doc.error_message = error_message
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def delete(self, document_id: str) -> bool:
        doc = await self.get_by_id(document_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.flush()
        return True

    async def save_extracted_content(
        self,
        document_id: str,
        pages: List[DocumentPage],
        sections: List[DocumentSection],
        blocks: List[ContentBlock],
        chunks: List[TextChunk],
        tables: List[ExtractedTable],
        images: List[ExtractedImage],
    ) -> None:
        """Atomically saves all extracted and chunked entities for a document."""
        for p in pages:
            self.session.add(p)
        for s in sections:
            self.session.add(s)
        for b in blocks:
            self.session.add(b)
        for c in chunks:
            self.session.add(c)
        for t in tables:
            self.session.add(t)
        for img in images:
            self.session.add(img)
        await self.session.flush()

    async def get_chunks_for_retrieval(self, kb_id: Optional[str] = None) -> List[Tuple[TextChunk, Document]]:
        query = (
            select(TextChunk, Document)
            .join(Document, TextChunk.document_id == Document.id)
            .where(Document.status == "COMPLETED")
        )
        if kb_id:
            query = query.where(Document.kb_id == kb_id)
        result = await self.session.execute(query)
        return result.all()

    async def get_tables_for_retrieval(self, kb_id: Optional[str] = None) -> List[Tuple[ExtractedTable, Document]]:
        query = (
            select(ExtractedTable, Document)
            .join(Document, ExtractedTable.document_id == Document.id)
            .where(Document.status == "COMPLETED")
        )
        if kb_id:
            query = query.where(Document.kb_id == kb_id)
        result = await self.session.execute(query)
        return result.all()

    async def get_images_for_retrieval(self, kb_id: Optional[str] = None) -> List[Tuple[ExtractedImage, Document]]:
        query = (
            select(ExtractedImage, Document)
            .join(Document, ExtractedImage.document_id == Document.id)
            .where(Document.status == "COMPLETED")
        )
        if kb_id:
            query = query.where(Document.kb_id == kb_id)
        result = await self.session.execute(query)
        return result.all()

    async def get_images_by_ids(self, image_ids: List[str]) -> List[ExtractedImage]:
        if not image_ids:
            return []
        query = select(ExtractedImage).where(ExtractedImage.id.in_(image_ids))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_images_by_page(self, page_id: str) -> List[ExtractedImage]:
        query = select(ExtractedImage).where(ExtractedImage.page_id == page_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_stats(self) -> Dict[str, int]:
        total_docs = await self.session.scalar(select(func.count(Document.id))) or 0
        processing_docs = await self.session.scalar(
            select(func.count(Document.id)).where(Document.status.in_(["PENDING", "PROCESSING", "INDEXING"]))
        ) or 0
        completed_docs = await self.session.scalar(
            select(func.count(Document.id)).where(Document.status == "COMPLETED")
        ) or 0
        failed_docs = await self.session.scalar(
            select(func.count(Document.id)).where(Document.status == "FAILED")
        ) or 0
        total_images = await self.session.scalar(select(func.count(ExtractedImage.id))) or 0
        total_tables = await self.session.scalar(select(func.count(ExtractedTable.id))) or 0
        total_chunks = await self.session.scalar(select(func.count(TextChunk.id))) or 0

        return {
            "total_documents": total_docs,
            "processing_documents": processing_docs,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "total_images": total_images,
            "total_tables": total_tables,
            "total_chunks": total_chunks,
        }
