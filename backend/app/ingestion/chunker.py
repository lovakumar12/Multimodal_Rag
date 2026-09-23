import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.extraction.base import ExtractedPageData


@dataclass
class ChunkOutput:
    chunk_id: str
    page_number: int
    chunk_index: int
    text: str
    heading_context: Optional[str] = None
    associated_image_ids: List[str] = field(default_factory=list)
    associated_table_ids: List[str] = field(default_factory=list)
    token_count: int = 0
    content_type: str = "text"  # text or table


class StructureAwareChunker:
    """
    Structure-aware chunker that:
    1. Respects headings, section boundaries, and paragraph breaks.
    2. Prepends active section/heading breadcrumbs to text chunks for context retention.
    3. Retains bidirectional associations with co-located images, diagrams, and tables.
    """

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_page(
        self,
        page: ExtractedPageData,
        page_image_ids: List[str],
        page_table_ids: List[str],
        start_chunk_idx: int = 0,
    ) -> List[ChunkOutput]:
        chunks: List[ChunkOutput] = []
        raw_text = page.text.strip()
        if not raw_text:
            return chunks

        # Extract current active headings from page sections if available
        active_heading = page.sections[0].title if page.sections else None

        # Split text into paragraphs
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

        current_buffer: List[str] = []
        current_len = 0
        chunk_idx = start_chunk_idx

        for p in paragraphs:
            # Check if this paragraph itself is a heading
            if p.startswith("#") or (len(p) < 80 and any(s.title in p for s in page.sections)):
                # Flush existing buffer before heading
                if current_buffer:
                    chunk_text = "\n\n".join(current_buffer)
                    chunks.append(
                        self._create_chunk(
                            chunk_text=chunk_text,
                            page_num=page.page_number,
                            chunk_idx=chunk_idx,
                            heading=active_heading,
                            image_ids=page_image_ids,
                            table_ids=page_table_ids,
                        )
                    )
                    chunk_idx += 1
                    current_buffer = []
                    current_len = 0

                active_heading = p.lstrip("#").strip()

            p_len = len(p)
            if current_len + p_len > self.chunk_size and current_buffer:
                # Flush current buffer
                chunk_text = "\n\n".join(current_buffer)
                chunks.append(
                    self._create_chunk(
                        chunk_text=chunk_text,
                        page_num=page.page_number,
                        chunk_idx=chunk_idx,
                        heading=active_heading,
                        image_ids=page_image_ids,
                        table_ids=page_table_ids,
                    )
                )
                chunk_idx += 1

                # Keep overlap if possible
                overlap_text = current_buffer[-1] if len(current_buffer[-1]) < self.overlap else ""
                current_buffer = [overlap_text, p] if overlap_text else [p]
                current_len = sum(len(x) for x in current_buffer)
            else:
                current_buffer.append(p)
                current_len += p_len

        # Flush remaining buffer
        if current_buffer:
            chunk_text = "\n\n".join(current_buffer)
            if chunk_text.strip():
                chunks.append(
                    self._create_chunk(
                        chunk_text=chunk_text,
                        page_num=page.page_number,
                        chunk_idx=chunk_idx,
                        heading=active_heading,
                        image_ids=page_image_ids,
                        table_ids=page_table_ids,
                    )
                )

        return chunks

    def _create_chunk(
        self,
        chunk_text: str,
        page_num: int,
        chunk_idx: int,
        heading: Optional[str],
        image_ids: List[str],
        table_ids: List[str],
    ) -> ChunkOutput:
        # Prepend heading breadcrumb if available and not already in text
        augmented_text = chunk_text
        if heading and heading not in chunk_text:
            augmented_text = f"[{heading}]\n{chunk_text}"

        # Approximate token count (1 token ~= 4 chars)
        token_count = max(1, len(augmented_text) // 4)

        return ChunkOutput(
            chunk_id=str(uuid.uuid4()),
            page_number=page_num,
            chunk_index=chunk_idx,
            text=augmented_text,
            heading_context=heading,
            associated_image_ids=image_ids,
            associated_table_ids=table_ids,
            token_count=token_count,
            content_type="text",
        )


chunker = StructureAwareChunker()
