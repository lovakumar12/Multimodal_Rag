import asyncio
import io
import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.extraction.pdf_extractor import PDFExtractor
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.models.entities import KnowledgeBase
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.kb_repository import KnowledgeBaseRepository
from backend.app.retrieval.retriever import MultimodalRetriever
from backend.app.generation.generator import rag_generator
from backend.app.storage.local_storage import storage_service


@pytest.mark.anyio
async def test_full_multimodal_rag_pipeline_end_to_end():
    # 1. Initialize schema
    await init_db()

    async with AsyncSessionLocal() as session:
        kb_repo = KnowledgeBaseRepository(session)
        doc_repo = DocumentRepository(session)

        # 2. Create Knowledge Base
        kb = await kb_repo.create(name="AI History & Architecture", description="Test KB for End-to-End RAG")
        await session.commit()
        assert kb.id is not None

        # 3. Ingest sample PDF (king_Ashoka.pdf which contains text, tables, and images)
        pdf_path = Path("data/uploads/king_Ashoka.pdf")
        if not pdf_path.exists():
            pytest.skip("king_Ashoka.pdf not found in data/uploads")

        content = pdf_path.read_bytes()
        storage_path = storage_service.save_file(content, pdf_path.name, subfolder="uploads")

        # Disable external vision API call in automated test for fast deterministic execution
        orig_auto = settings.AUTO_DESCRIBE_IMAGES
        settings.AUTO_DESCRIBE_IMAGES = False

        doc = await doc_repo.create(
            kb_id=kb.id,
            filename=pdf_path.name,
            file_type="pdf",
            file_size=len(content),
            storage_path=storage_path,
        )
        await session.commit()

        # 4. Run Ingestion Pipeline
        pipeline = IngestionPipeline(session)
        success = await pipeline.process_document(doc.id)
        assert success is True

        # 5. Verify Document Record & Extraction Status
        refreshed_doc = await doc_repo.get_by_id(doc.id)
        assert refreshed_doc.status == "COMPLETED"
        assert refreshed_doc.page_count > 0

        # 6. Verify Extracted Content & Relationships
        detail = await doc_repo.get_detail(doc.id)
        assert len(detail.pages) > 0
        total_images = sum(len(p.images) for p in detail.pages)
        total_tables = sum(len(p.tables) for p in detail.pages)
        assert total_images > 0
        assert total_tables > 0

        # Check image attributes
        sample_img = detail.pages[0].images[0]
        assert sample_img.asset_url is not None
        assert sample_img.width > 0

        # Check table attributes
        sample_table = None
        for p in detail.pages:
            if p.tables:
                sample_table = p.tables[0]
                break
        assert sample_table is not None
        assert len(sample_table.markdown_content) > 0

        # 7. Ask Document-Related Query (Multimodal Retrieval)
        retriever = MultimodalRetriever(session)
        search_res = await retriever.search(
            query="Ashoka reign and inscriptions",
            kb_id=kb.id,
            top_k=5,
            include_visuals=True,
            include_tables=True,
        )

        # 8. Verify Relevant Retrieval Results
        assert len(search_res.sources) > 0
        # Verify text citations
        top_source = search_res.sources[0]
        assert top_source.document_id == doc.id
        assert top_source.page >= 1
        assert len(top_source.snippet) > 0

        # Verify visual artifacts retrieval
        assert len(search_res.visuals) > 0
        top_visual = search_res.visuals[0]
        assert top_visual.document_id == doc.id
        assert top_visual.relevance_score >= 0.40
        assert top_visual.url.startswith("/api/v1/assets")

        # 9. Grounded Answer Generation
        answer, confidence = rag_generator.generate_answer(
            query="What do the inscriptions and reign of Ashoka discuss?",
            sources=search_res.sources,
            visuals=search_res.visuals,
            tables=search_res.tables,
        )

        assert len(answer) > 0
        assert confidence > 0.0

        # Restore setting
        settings.AUTO_DESCRIBE_IMAGES = orig_auto
