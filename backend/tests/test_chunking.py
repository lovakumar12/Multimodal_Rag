import unittest
from backend.app.extraction.base import ExtractedPageData, ExtractedSectionData
from backend.app.ingestion.chunker import StructureAwareChunker


class TestStructureAwareChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = StructureAwareChunker(chunk_size=300, overlap=50)

    def test_chunking_with_heading_preservation(self):
        page = ExtractedPageData(
            page_number=1,
            text="# Introduction to Multimodal RAG\n\nMultimodal RAG extends traditional text RAG to include visual artifacts such as tables, diagrams, and figures.\n\n# System Architecture\n\nThe architecture incorporates a hybrid retriever and a cross-modal reranker.",
            sections=[
                ExtractedSectionData(title="Introduction to Multimodal RAG", level=1, page_number=1),
                ExtractedSectionData(title="System Architecture", level=1, page_number=1),
            ],
        )
        chunks = self.chunker.chunk_page(
            page=page,
            page_image_ids=["img-123"],
            page_table_ids=["tbl-456"],
        )

        self.assertGreaterEqual(len(chunks), 2)
        # Check that heading context was preserved
        headings = [c.heading_context for c in chunks if c.heading_context]
        self.assertIn("Introduction to Multimodal RAG", headings)
        # Check entity association
        for c in chunks:
            self.assertIn("img-123", c.associated_image_ids)
            self.assertIn("tbl-456", c.associated_table_ids)


if __name__ == "__main__":
    unittest.main()
