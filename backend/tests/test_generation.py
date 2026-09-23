import unittest
from backend.app.generation.generator import RAGGroundedGenerator
from backend.app.schemas.retrieval import SearchResultSource, SearchResultTable, SearchResultVisual


class TestGeneration(unittest.TestCase):
    def setUp(self):
        self.generator = RAGGroundedGenerator()

    def test_insufficient_evidence_response(self):
        answer, confidence = self.generator.generate_answer(
            query="What was the Q3 revenue in 2024?",
            sources=[],
            visuals=[],
            tables=[],
        )
        self.assertEqual(confidence, 0.0)
        self.assertIn("do not contain enough information", answer.lower())

    def test_context_construction_with_multimodal_evidence(self):
        sources = [
            SearchResultSource(
                document_id="doc-1",
                document_name="architecture.pdf",
                page=2,
                snippet="The model uses multi-head attention with 8 heads.",
                score=0.92,
            )
        ]
        visuals = [
            SearchResultVisual(
                asset_id="asset-1",
                type="diagram",
                document_id="doc-1",
                document_name="architecture.pdf",
                page=2,
                url="/api/v1/assets/fig1.png",
                caption="Figure 1: Multi-Head Attention Mechanism",
                semantic_description="Architecture diagram of Scaled Dot-Product Attention.",
                relevance_score=0.91,
            )
        ]
        tables = [
            SearchResultTable(
                table_id="tbl-1",
                document_id="doc-1",
                document_name="architecture.pdf",
                page=3,
                markdown="| Model | BLEU |\n|---|---|\n| Base | 27.3 |",
                caption="Table 1: BLEU comparison",
                score=0.88,
            )
        ]

        answer, confidence = self.generator.generate_answer(
            query="Explain the multi-head attention architecture",
            sources=sources,
            visuals=visuals,
            tables=tables,
        )
        self.assertGreater(len(answer), 0)
        self.assertGreater(confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
