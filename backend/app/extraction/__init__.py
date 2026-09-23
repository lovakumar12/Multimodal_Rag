from pathlib import Path
from backend.app.core.errors import UnsupportedMediaTypeError
from backend.app.extraction.base import (
    BaseExtractor,
    ExtractedImageData,
    ExtractedPageData,
    ExtractedSectionData,
    ExtractedTableData,
    ExtractionResult,
)
from backend.app.extraction.pdf_extractor import PDFExtractor
from backend.app.extraction.pptx_extractor import PPTXExtractor
from backend.app.extraction.docx_extractor import DOCXExtractor
from backend.app.extraction.image_extractor import ImageExtractor


def get_extractor_for_file(filename: str) -> BaseExtractor:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return PDFExtractor()
    elif ext == ".pptx":
        return PPTXExtractor()
    elif ext == ".docx":
        return DOCXExtractor()
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return ImageExtractor()
    else:
        raise UnsupportedMediaTypeError(filename, ext)


__all__ = [
    "BaseExtractor",
    "ExtractedImageData",
    "ExtractedPageData",
    "ExtractedSectionData",
    "ExtractedTableData",
    "ExtractionResult",
    "PDFExtractor",
    "PPTXExtractor",
    "DOCXExtractor",
    "ImageExtractor",
    "get_extractor_for_file",
]
