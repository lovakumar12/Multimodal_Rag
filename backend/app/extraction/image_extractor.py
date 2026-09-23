import io
from pathlib import Path
from PIL import Image
from backend.app.core.logging import logger
from backend.app.extraction.base import (
    BaseExtractor,
    ExtractedImageData,
    ExtractedPageData,
    ExtractedSectionData,
    ExtractionResult,
)
from backend.app.extraction.ocr_service import ocr_service
from backend.app.extraction.vision_describer import vision_describer


class ImageExtractor(BaseExtractor):
    """Extractor for standalone image documents (diagrams, architecture charts, screenshots)."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size
        img_format = img.format or "PNG"

        # OCR text
        ocr_text = ocr_service.extract_text_from_image(file_bytes) or ""

        # Vision description
        desc, is_chart, caption = vision_describer.describe(
            image_bytes=file_bytes,
            image_format=img_format,
            surrounding_text=ocr_text,
            existing_caption=Path(filename).stem.replace("_", " ").title(),
        )

        full_text = f"# {caption or filename}\n\n"
        if desc:
            full_text += f"{desc}\n\n"
        if ocr_text:
            full_text += f"Text in image:\n{ocr_text}"

        image_data = ExtractedImageData(
            image_bytes=file_bytes,
            format=img_format,
            width=w,
            height=h,
            page_number=1,
            caption=caption or Path(filename).stem,
            ocr_text=ocr_text,
            semantic_description=desc,
            surrounding_text=ocr_text,
            is_diagram_or_chart=is_chart or True,
        )

        page_data = ExtractedPageData(
            page_number=1,
            text=full_text,
            width=float(w),
            height=float(h),
            rendered_image_bytes=file_bytes,
            sections=[ExtractedSectionData(title=caption or filename, level=1, page_number=1)],
            images=[image_data],
            tables=[],
        )

        return ExtractionResult(
            filename=filename,
            file_type="image",
            page_count=1,
            metadata={"title": filename, "width": w, "height": h},
            pages=[page_data],
        )
