import io
from typing import Optional
from PIL import Image
from backend.app.core.logging import logger


class OCRService:
    """Modular OCR service with graceful fallback."""

    def __init__(self):
        self._tesseract_available = False
        try:
            import pytesseract
            # Quick check
            self._pytesseract = pytesseract
            self._tesseract_available = True
        except Exception:
            self._pytesseract = None

    def extract_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        if not self._tesseract_available:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))
            text = self._pytesseract.image_to_string(img)
            return text.strip() if text and text.strip() else None
        except Exception as e:
            logger.debug(f"Tesseract OCR skipped or not configured: {e}")
            return None


ocr_service = OCRService()
