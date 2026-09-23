import unittest
from backend.app.models.entities import ExtractedImage
from backend.app.retrieval.image_scorer import MultiSignalImageScorer


class TestImageScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = MultiSignalImageScorer(
            w_desc=0.35,
            w_text=0.25,
            w_caption=0.20,
            w_page=0.10,
            w_co_occurrence=0.10,
            threshold=0.40,
        )

    def test_high_relevance_visual(self):
        img = ExtractedImage(
            id="img-1",
            document_id="doc-1",
            page_id="p-1",
            caption="Transformer Architecture",
            semantic_description="Diagram showing encoder and decoder blocks with multi-head attention",
            is_diagram_or_chart=True,
            asset_path="assets/img1.png",
            asset_url="/api/v1/assets/img1.png",
        )
        score = self.scorer.compute_score(
            image=img,
            desc_sim=0.85,
            surrounding_sim=0.75,
            caption_sim=0.80,
            page_relevance=1.0,
            is_co_occurring=True,
        )
        self.assertGreater(score, 0.70)
        self.assertTrue(self.scorer.is_relevant(score))

    def test_low_relevance_visual_filtered(self):
        img = ExtractedImage(
            id="img-2",
            document_id="doc-1",
            page_id="p-10",
            caption="Decorative Logo",
            semantic_description="Company brand logo watermark",
            is_diagram_or_chart=False,
            asset_path="assets/img2.png",
            asset_url="/api/v1/assets/img2.png",
        )
        score = self.scorer.compute_score(
            image=img,
            desc_sim=0.10,
            surrounding_sim=0.05,
            caption_sim=0.0,
            page_relevance=0.0,
            is_co_occurring=False,
        )
        self.assertLess(score, 0.40)
        self.assertFalse(self.scorer.is_relevant(score))


if __name__ == "__main__":
    unittest.main()
