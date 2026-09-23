import io
import re
from typing import List, Optional, Tuple
import pymupdf  # PyMuPDF
import pdfplumber
from PIL import Image

from backend.app.core.logging import logger
from backend.app.extraction.base import (
    BaseExtractor,
    ExtractedImageData,
    ExtractedPageData,
    ExtractedSectionData,
    ExtractedTableData,
    ExtractionResult,
)
from backend.app.extraction.ocr_service import ocr_service
from backend.app.extraction.vision_describer import vision_describer


class PDFExtractor(BaseExtractor):
    """Production PDF extractor extracting text, headings, tables, images, and page renders."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        pages_data: List[ExtractedPageData] = []

        # Open pdfplumber for high-precision table extraction
        plumber_pdf = None
        try:
            plumber_pdf = pdfplumber.open(io.BytesIO(file_bytes))
        except Exception as e:
            logger.warning(f"pdfplumber failed to open {filename}: {e}")

        for page_idx in range(page_count):
            page_num = page_idx + 1
            mu_page = doc[page_idx]

            # 1. Render page image for visual preview (DPI 120 is great balance of quality and size)
            rendered_bytes = None
            try:
                pix = mu_page.get_pixmap(dpi=120)
                rendered_bytes = pix.tobytes("png")
            except Exception as e:
                logger.warning(f"Failed to render page {page_num} of {filename}: {e}")

            # 2. Extract structured text and headings
            page_text = mu_page.get_text() or ""
            sections = self._extract_sections_from_page(mu_page, page_num)

            # 3. Extract tables using pdfplumber
            tables = []
            if plumber_pdf and page_idx < len(plumber_pdf.pages):
                tables = self._extract_tables_from_page(plumber_pdf.pages[page_idx], page_num, page_text)

            # 4. Extract embedded images & diagrams
            images = self._extract_images_from_page(doc, mu_page, page_num, page_text)

            # Build page data
            page_rect = mu_page.rect
            pages_data.append(
                ExtractedPageData(
                    page_number=page_num,
                    text=page_text.strip(),
                    width=float(page_rect.width),
                    height=float(page_rect.height),
                    rendered_image_bytes=rendered_bytes,
                    sections=sections,
                    images=images,
                    tables=tables,
                )
            )

        if plumber_pdf:
            try:
                plumber_pdf.close()
            except Exception:
                pass

        doc.close()

        return ExtractionResult(
            filename=filename,
            file_type="pdf",
            page_count=page_count,
            metadata={
                "title": doc.metadata.get("title", filename) if hasattr(doc, "metadata") and doc.metadata else filename,
                "author": doc.metadata.get("author", "") if hasattr(doc, "metadata") and doc.metadata else "",
            },
            pages=pages_data,
        )

    def _extract_sections_from_page(self, page: pymupdf.Page, page_num: int) -> List[ExtractedSectionData]:
        sections: List[ExtractedSectionData] = []
        try:
            blocks = page.get_text("dict")["blocks"]
            order = 0
            for b in blocks:
                if b.get("type") == 0:  # text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 10.0)
                            flags = span.get("flags", 0)  # bold flag is 2 (bit 1)
                            is_bold = bool(flags & 2)

                            # If text is substantial and has larger font size or bold style
                            if (size >= 13.0 or (size >= 11.5 and is_bold)) and len(text) > 3 and len(text) < 120:
                                level = 1 if size >= 15.0 else 2
                                sections.append(
                                    ExtractedSectionData(
                                        title=text,
                                        level=level,
                                        page_number=page_num,
                                        order_index=order,
                                    )
                                )
                                order += 1
        except Exception as e:
            logger.debug(f"Section extraction fallback on page {page_num}: {e}")
        return sections

    def _extract_tables_from_page(
        self, plumber_page: pdfplumber.page.Page, page_num: int, page_text: str
    ) -> List[ExtractedTableData]:
        tables: List[ExtractedTableData] = []
        try:
            extracted = plumber_page.extract_tables()
            for idx, raw_table in enumerate(extracted):
                if not raw_table or len(raw_table) < 2:
                    continue

                # Clean cells
                cleaned_rows: List[List[str]] = []
                for row in raw_table:
                    cleaned_rows.append([str(c or "").strip().replace("\n", " ") for c in row])

                # Check if table has any non-empty content
                if not any(any(c for c in row) for row in cleaned_rows):
                    continue

                headers = cleaned_rows[0]
                body_rows = cleaned_rows[1:]

                # Build markdown representation
                md_lines = []
                header_str = "| " + " | ".join(headers) + " |"
                separator_str = "| " + " | ".join(["---"] * len(headers)) + " |"
                md_lines.append(header_str)
                md_lines.append(separator_str)
                for r in body_rows:
                    # Pad or truncate row to match header length
                    padded = r + [""] * (len(headers) - len(r)) if len(r) < len(headers) else r[: len(headers)]
                    md_lines.append("| " + " | ".join(padded) + " |")
                markdown = "\n".join(md_lines)

                # Look for table caption in nearby page text
                caption = None
                caption_match = re.search(
                    rf"(Table\s+{idx + 1}[:\.\-][^\n]+|Table\s+[A-Za-z0-9]+[:\.\-][^\n]+)",
                    page_text,
                    re.IGNORECASE,
                )
                if caption_match:
                    caption = caption_match.group(1).strip()

                tables.append(
                    ExtractedTableData(
                        headers=headers,
                        rows=body_rows,
                        markdown=markdown,
                        page_number=page_num,
                        table_index=idx,
                        caption=caption,
                        surrounding_text=page_text[:300],
                    )
                )
        except Exception as e:
            logger.warning(f"Error extracting tables on page {page_num}: {e}")
        return tables

    def _extract_images_from_page(
        self, doc: pymupdf.Document, page: pymupdf.Page, page_num: int, page_text: str
    ) -> List[ExtractedImageData]:
        images: List[ExtractedImageData] = []
        try:
            image_list = page.get_images(full=True)
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                img_ext = base_image.get("ext", "png").upper()
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Filter out tiny icon decorations, spacer lines, bullet points (< 50x50)
                if width < 50 or height < 50:
                    continue

                # Locate image bbox on page if available
                rects = page.get_image_rects(xref)
                bbox = [rects[0].x0, rects[0].y0, rects[0].x1, rects[0].y1] if rects else None

                # Search for caption in surrounding text
                caption = None
                cap_match = re.search(
                    rf"(?:Figure|Fig\.?|Diagram)\s+{img_idx + 1}[:\.\-][^\n]+|(?:Figure|Fig\.?|Diagram)\s+[0-9]+[:\.\-][^\n]+",
                    page_text,
                    re.IGNORECASE,
                )
                if cap_match:
                    caption = cap_match.group(0).strip()

                # Extract OCR text if diagram contains labels
                ocr_text = ocr_service.extract_text_from_image(image_bytes)

                # Context around image
                surrounding = page_text[:400]

                # Semantic description & diagram classification
                semantic_desc, is_chart, final_caption = vision_describer.describe(
                    image_bytes=image_bytes,
                    image_format=img_ext,
                    surrounding_text=surrounding,
                    existing_caption=caption,
                )

                images.append(
                    ExtractedImageData(
                        image_bytes=image_bytes,
                        format=img_ext,
                        width=width,
                        height=height,
                        page_number=page_num,
                        caption=final_caption,
                        ocr_text=ocr_text,
                        semantic_description=semantic_desc,
                        surrounding_text=surrounding,
                        is_diagram_or_chart=is_chart,
                        bbox=bbox,
                    )
                )
        except Exception as e:
            logger.warning(f"Error extracting images from page {page_num}: {e}")
        return images
