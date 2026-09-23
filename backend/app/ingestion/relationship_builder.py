import uuid
from typing import Dict, List, Tuple
from backend.app.extraction.base import ExtractionResult
from backend.app.ingestion.chunker import chunker
from backend.app.models.entities import (
    ContentBlock,
    DocumentPage,
    DocumentSection,
    ExtractedImage,
    ExtractedTable,
    TextChunk,
)
from backend.app.storage.base import BaseStorageService


class RelationshipBuilder:
    """Constructs the Document -> Page -> Section -> ContentBlocks relationship model."""

    def __init__(self, storage_service: BaseStorageService):
        self.storage = storage_service

    def build_entities(
        self, document_id: str, extraction: ExtractionResult
    ) -> Tuple[
        List[DocumentPage],
        List[DocumentSection],
        List[ContentBlock],
        List[TextChunk],
        List[ExtractedTable],
        List[ExtractedImage],
    ]:
        pages: List[DocumentPage] = []
        sections: List[DocumentSection] = []
        blocks: List[ContentBlock] = []
        chunks: List[TextChunk] = []
        tables: List[ExtractedTable] = []
        images: List[ExtractedImage] = []

        global_chunk_idx = 0

        for p_data in extraction.pages:
            page_id = str(uuid.uuid4())
            page_num = p_data.page_number

            # 1. Save rendered page preview if available
            rendered_path = None
            if p_data.rendered_image_bytes:
                rendered_path = self.storage.save_file(
                    content=p_data.rendered_image_bytes,
                    filename=f"{document_id}_p{page_num}.png",
                    subfolder="pages",
                )

            # 2. Extract sections
            page_section_ids = []
            for s_data in p_data.sections:
                sec_id = str(uuid.uuid4())
                sec = DocumentSection(
                    id=sec_id,
                    document_id=document_id,
                    page_number=page_num,
                    title=s_data.title,
                    level=s_data.level,
                    order_index=s_data.order_index,
                )
                sections.append(sec)
                page_section_ids.append(sec_id)

            primary_section_id = page_section_ids[0] if page_section_ids else None

            # 3. Extract & persist images
            page_image_ids = []
            for img_idx, img_data in enumerate(p_data.images):
                img_id = str(uuid.uuid4())
                asset_subfolder = "assets"
                asset_filename = f"{document_id}_p{page_num}_i{img_idx + 1}.{img_data.format.lower()}"
                storage_path = self.storage.save_file(
                    content=img_data.image_bytes,
                    filename=asset_filename,
                    subfolder=asset_subfolder,
                )
                asset_url = self.storage.get_url(storage_path)

                ext_img = ExtractedImage(
                    id=img_id,
                    document_id=document_id,
                    page_id=page_id,
                    section_id=primary_section_id,
                    page_number=page_num,
                    image_index=img_idx,
                    asset_path=storage_path,
                    asset_url=asset_url,
                    width=img_data.width,
                    height=img_data.height,
                    format=img_data.format,
                    caption=img_data.caption,
                    semantic_description=img_data.semantic_description,
                    ocr_text=img_data.ocr_text,
                    surrounding_text=img_data.surrounding_text,
                    is_diagram_or_chart=img_data.is_diagram_or_chart,
                )
                images.append(ext_img)
                page_image_ids.append(img_id)

                # Content block for image
                blocks.append(
                    ContentBlock(
                        document_id=document_id,
                        page_id=page_id,
                        section_id=primary_section_id,
                        block_type="diagram" if img_data.is_diagram_or_chart else "image",
                        content_json={
                            "asset_id": img_id,
                            "asset_url": asset_url,
                            "caption": img_data.caption,
                            "description": img_data.semantic_description,
                        },
                        order_index=len(blocks),
                    )
                )

            # 4. Extract & persist tables
            page_table_ids = []
            for tbl_idx, tbl_data in enumerate(p_data.tables):
                tbl_id = str(uuid.uuid4())
                ext_tbl = ExtractedTable(
                    id=tbl_id,
                    document_id=document_id,
                    page_id=page_id,
                    section_id=primary_section_id,
                    page_number=page_num,
                    table_index=tbl_data.table_index,
                    headers_json=tbl_data.headers,
                    rows_json=tbl_data.rows,
                    markdown_content=tbl_data.markdown,
                    caption=tbl_data.caption,
                    surrounding_text=tbl_data.surrounding_text,
                )
                tables.append(ext_tbl)
                page_table_ids.append(tbl_id)

                # Content block for table
                blocks.append(
                    ContentBlock(
                        document_id=document_id,
                        page_id=page_id,
                        section_id=primary_section_id,
                        block_type="table",
                        content_json={
                            "table_id": tbl_id,
                            "caption": tbl_data.caption,
                            "markdown": tbl_data.markdown,
                            "headers": tbl_data.headers,
                        },
                        order_index=len(blocks),
                    )
                )

            # 5. Chunk page text with bidirectional associations
            page_chunks = chunker.chunk_page(
                page=p_data,
                page_image_ids=page_image_ids,
                page_table_ids=page_table_ids,
                start_chunk_idx=global_chunk_idx,
            )
            for c in page_chunks:
                chunk_ent = TextChunk(
                    id=c.chunk_id,
                    document_id=document_id,
                    page_id=page_id,
                    section_id=primary_section_id,
                    page_number=c.page_number,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    heading_context=c.heading_context,
                    associated_image_ids=c.associated_image_ids,
                    associated_table_ids=c.associated_table_ids,
                    token_count=c.token_count,
                )
                chunks.append(chunk_ent)
                global_chunk_idx += 1

                # Content block for text
                blocks.append(
                    ContentBlock(
                        document_id=document_id,
                        page_id=page_id,
                        section_id=primary_section_id,
                        block_type="text",
                        content_json={"text": c.text, "chunk_id": c.chunk_id},
                        order_index=len(blocks),
                    )
                )

            # 6. Page entity
            page_entity = DocumentPage(
                id=page_id,
                document_id=document_id,
                page_number=page_num,
                text_content=p_data.text,
                width=p_data.width,
                height=p_data.height,
                rendered_image_path=rendered_path,
                summary=f"Page {page_num}: {len(p_data.text)} chars, {len(page_image_ids)} images, {len(page_table_ids)} tables",
            )
            pages.append(page_entity)

        return pages, sections, blocks, chunks, tables, images
