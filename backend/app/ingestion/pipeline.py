import traceback
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.factory import get_embedding_provider
from backend.app.extraction import get_extractor_for_file
from backend.app.ingestion.relationship_builder import RelationshipBuilder
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.retrieval.vector_store import vector_store
from backend.app.storage.local_storage import storage_service


class IngestionPipeline:
    """End-to-end ingestion pipeline: Extract -> Relate -> Chunk -> Embed -> Index -> Persist."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.storage = storage_service
        self.rel_builder = RelationshipBuilder(self.storage)
        self.embed_provider = get_embedding_provider()

    async def process_document(self, document_id: str) -> bool:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found for ingestion")
            return False

        logger.info(f"Starting ingestion for document '{doc.filename}' (ID: {document_id})")

        try:
            # 1. Update status to PROCESSING
            await self.doc_repo.update_status(document_id=document_id, status="PROCESSING")
            await self.session.commit()

            # 2. Retrieve document bytes
            file_bytes = self.storage.get_file(doc.storage_path)

            # 3. Extract content
            extractor = get_extractor_for_file(doc.filename)
            extraction_result = extractor.extract(file_bytes=file_bytes, filename=doc.filename)

            # 4. Update status to INDEXING
            await self.doc_repo.update_status(
                document_id=document_id, status="INDEXING", page_count=extraction_result.page_count
            )
            await self.session.commit()

            # 5. Build entity relationships
            pages, sections, blocks, chunks, tables, images = self.rel_builder.build_entities(
                document_id=document_id, extraction=extraction_result
            )

            # 6. Generate embeddings and index vectors
            # A. Text Chunks
            if chunks:
                chunk_texts = [c.text for c in chunks]
                chunk_vectors = self.embed_provider.embed_batch(chunk_texts)
                for c, v in zip(chunks, chunk_vectors):
                    c.embedding = v

                vector_store.add_vectors(
                    vectors=chunk_vectors,
                    entity_ids=[c.id for c in chunks],
                    entity_types=["text_chunk"] * len(chunks),
                    document_ids=[document_id] * len(chunks),
                    kb_ids=[doc.kb_id] * len(chunks),
                    metadata_list=[
                        {
                            "page_number": c.page_number,
                            "document_name": doc.filename,
                            "snippet": c.text[:300],
                            "page_id": c.page_id,
                            "associated_image_ids": c.associated_image_ids,
                            "associated_table_ids": c.associated_table_ids,
                        }
                        for c in chunks
                    ],
                )

            # B. Tables
            if tables:
                table_texts = [f"Table: {t.caption or 'Data Table'}\n{t.markdown_content}" for t in tables]
                table_vectors = self.embed_provider.embed_batch(table_texts)
                for t, v in zip(tables, table_vectors):
                    t.embedding = v

                vector_store.add_vectors(
                    vectors=table_vectors,
                    entity_ids=[t.id for t in tables],
                    entity_types=["table"] * len(tables),
                    document_ids=[document_id] * len(tables),
                    kb_ids=[doc.kb_id] * len(tables),
                    metadata_list=[
                        {
                            "page_number": t.page_number,
                            "document_name": doc.filename,
                            "markdown": t.markdown_content,
                            "headers": t.headers_json,
                            "rows": t.rows_json,
                            "caption": t.caption,
                        }
                        for t in tables
                    ],
                )

            # C. Images & Diagrams
            if images:
                image_texts = [
                    f"{img.caption or 'Image'}. {img.semantic_description or ''}. {img.ocr_text or ''}".strip()
                    for img in images
                ]
                image_vectors = self.embed_provider.embed_batch(image_texts)
                for img, v in zip(images, image_vectors):
                    img.embedding = v

                vector_store.add_vectors(
                    vectors=image_vectors,
                    entity_ids=[img.id for img in images],
                    entity_types=["image"] * len(images),
                    document_ids=[document_id] * len(images),
                    kb_ids=[doc.kb_id] * len(images),
                    metadata_list=[
                        {
                            "page_number": img.page_number,
                            "document_name": doc.filename,
                            "asset_url": img.asset_url,
                            "caption": img.caption,
                            "description": img.semantic_description,
                            "is_diagram": img.is_diagram_or_chart,
                        }
                        for img in images
                    ],
                )

            # 7. Atomically persist relational records
            await self.doc_repo.save_extracted_content(
                document_id=document_id,
                pages=pages,
                sections=sections,
                blocks=blocks,
                chunks=chunks,
                tables=tables,
                images=images,
            )

            # 8. Mark document as COMPLETED
            await self.doc_repo.update_status(
                document_id=document_id,
                status="COMPLETED",
                page_count=extraction_result.page_count,
            )
            await self.session.commit()

            logger.info(
                f"Document '{doc.filename}' ingestion COMPLETED: {len(pages)} pages, {len(chunks)} chunks, "
                f"{len(images)} images, {len(tables)} tables indexed."
            )
            return True

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ingestion failed for document {document_id}: {e}\n{error_trace}")
            await self.session.rollback()
            await self.doc_repo.update_status(
                document_id=document_id,
                status="FAILED",
                error_message=str(e),
            )
            await self.session.commit()
            return False
