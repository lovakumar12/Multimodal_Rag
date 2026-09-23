import unittest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.extraction.pdf_extractor import PDFExtractor
from backend.app.extraction.pptx_extractor import PPTXExtractor


class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent.parent
        self.pdf_path = self.root / "data" / "uploads" / "king_Ashoka.pdf"
        self.pptx_path = self.root / "Beyond_Text_RAG_Multimodal_RAG.pptx"
        # Disable external vision API during quick unit test
        self.orig_auto = settings.AUTO_DESCRIBE_IMAGES
        settings.AUTO_DESCRIBE_IMAGES = False

    def tearDown(self):
        settings.AUTO_DESCRIBE_IMAGES = self.orig_auto

    def test_pdf_extraction(self):
        if not self.pdf_path.exists():
            self.skipTest(f"{self.pdf_path} not found")

        extractor = PDFExtractor()
        res = extractor.extract(self.pdf_path.read_bytes(), self.pdf_path.name)

        self.assertEqual(res.file_type, "pdf")
        self.assertGreaterEqual(res.page_count, 1)
        self.assertGreater(len(res.pages), 0)

        # Check that page 1 has text and rendered preview
        page1 = res.pages[0]
        self.assertIsNotNone(page1.rendered_image_bytes)
        self.assertGreater(len(page1.text), 0)

    def test_pptx_extraction(self):
        if not self.pptx_path.exists():
            self.skipTest(f"{self.pptx_path} not found")

        extractor = PPTXExtractor()
        res = extractor.extract(self.pptx_path.read_bytes(), self.pptx_path.name)

        self.assertEqual(res.file_type, "pptx")
        self.assertGreaterEqual(res.page_count, 1)
        self.assertGreater(len(res.pages), 0)


if __name__ == "__main__":
    unittest.main()
