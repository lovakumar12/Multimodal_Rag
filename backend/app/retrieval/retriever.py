from typing import Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.embeddings.factory import get_embedding_provider
from backend.app.models.entities import Document, ExtractedImage, ExtractedTable, TextChunk
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.retrieval.image_scorer import image_scorer
from backend.app.retrieval.vector_store import vector_store
from backend.app.schemas.retrieval import (
    SearchResponse,
    SearchResultSource,
    SearchResultTable,
    SearchResultVisual,
)


class MultimodalRetriever:
    """
    Hybrid Multimodal Retriever combining multi-entity vector search,
    relationship graph expansion, and multi-signal visual relevance scoring.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.embedding_provider = get_embedding_provider()

    async def search(
        self,
        query: str,
        kb_id: Optional[str] = None,
        top_k: int = 5,
        include_visuals: bool = True,
        include_tables: bool = True,
    ) -> SearchResponse:
        logger.info(f"Executing multimodal retrieval for query: '{query}' (kb_id: {kb_id})")

        # 1. Generate query embedding
        query_vector = self.embedding_provider.embed_text(query)

        # 2. Retrieve candidate text chunks
        chunk_hits = vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            kb_id=kb_id,
            entity_type="text_chunk",
        )

        sources: List[SearchResultSource] = []
        retrieved_page_ids: Set[str] = set()
        associated_image_ids: Set[str] = set()
        associated_table_ids: Set[str] = set()

        for entry, score in chunk_hits:
            doc_id = entry.document_id
            meta = entry.metadata
            page_num = meta.get("page_number", 1)
            doc_name = meta.get("document_name", "Document")
            snippet = meta.get("snippet", "")
            page_id = meta.get("page_id")

            if page_id:
                retrieved_page_ids.add(page_id)

            for img_id in meta.get("associated_image_ids", []):
                associated_image_ids.add(img_id)
            for tbl_id in meta.get("associated_table_ids", []):
                associated_table_ids.add(tbl_id)

            sources.append(
                SearchResultSource(
                    document_id=doc_id,
                    document_name=doc_name,
                    page=page_num,
                    content_type="text",
                    snippet=snippet,
                    score=round(score, 4),
                )
            )

        # 3. Retrieve and expand tables
        tables: List[SearchResultTable] = []
        if include_tables:
            table_hits = vector_store.search(
                query_vector=query_vector,
                top_k=3,
                kb_id=kb_id,
                entity_type="table",
            )
            table_id_set = {entry.entity_id for entry, _ in table_hits}.union(associated_table_ids)
            for entry, score in table_hits:
                meta = entry.metadata
                tables.append(
                    SearchResultTable(
                        table_id=entry.entity_id,
                        document_id=entry.document_id,
                        document_name=meta.get("document_name", "Document"),
                        page=meta.get("page_number", 1),
                        markdown=meta.get("markdown", ""),
                        headers=meta.get("headers", []),
                        rows=meta.get("rows", []),
                        caption=meta.get("caption"),
                        score=round(score, 4),
                    )
                )

        # 4. Multi-Signal Visual Retrieval & Relationship Expansion
        visuals: List[SearchResultVisual] = []
        if include_visuals:
            # A. Direct vector hits on image descriptions/OCR
            direct_image_hits = vector_store.search(
                query_vector=query_vector,
                top_k=5,
                kb_id=kb_id,
                entity_type="image",
            )

            candidate_image_map: Dict[str, Dict] = {}
            for entry, score in direct_image_hits:
                candidate_image_map[entry.entity_id] = {
                    "entry": entry,
                    "desc_sim": score,
                    "is_co_occurring": False,
                }

            # B. Relationship Graph Expansion: add visuals co-occurring with top chunks
            for img_id in associated_image_ids:
                if img_id not in candidate_image_map:
                    candidate_image_map[img_id] = {
                        "entry": None,
                        "desc_sim": 0.35,  # baseline co-occurrence prior
                        "is_co_occurring": True,
                    }
                else:
                    candidate_image_map[img_id]["is_co_occurring"] = True

            # Resolve image records from DB
            all_candidate_ids = list(candidate_image_map.keys())
            if all_candidate_ids:
                db_images = await self.doc_repo.get_images_by_ids(all_candidate_ids)
                doc_cache: Dict[str, Document] = {}

                for img in db_images:
                    cand_info = candidate_image_map.get(img.id, {})
                    desc_sim = cand_info.get("desc_sim", 0.0)
                    is_co = cand_info.get("is_co_occurring", False)

                    # Check if image page matches any top retrieved text chunk pages
                    page_relevance = 1.0 if img.page_id in retrieved_page_ids else 0.0

                    rel_score = image_scorer.compute_score(
                        image=img,
                        desc_sim=desc_sim,
                        surrounding_sim=desc_sim * 0.8,
                        caption_sim=desc_sim * 0.9,
                        page_relevance=page_relevance,
                        is_co_occurring=is_co,
                    )

                    if image_scorer.is_relevant(rel_score):
                        if img.document_id not in doc_cache:
                            doc = await self.doc_repo.get_by_id(img.document_id)
                            if doc:
                                doc_cache[img.document_id] = doc

                        doc_name = doc_cache[img.document_id].filename if img.document_id in doc_cache else "Document"

                        visuals.append(
                            SearchResultVisual(
                                asset_id=img.id,
                                type="diagram" if img.is_diagram_or_chart else "image",
                                document_id=img.document_id,
                                document_name=doc_name,
                                page=img.page_number or 1,
                                url=img.asset_url,
                                caption=img.caption,
                                semantic_description=img.semantic_description,
                                relevance_score=rel_score,
                            )
                        )

            # Sort visuals by descending relevance score and cap to MAX_RETURNED_VISUALS
            visuals.sort(key=lambda v: v.relevance_score, reverse=True)
            visuals = visuals[: settings.MAX_RETURNED_VISUALS]

        return SearchResponse(
            query=query,
            sources=sources,
            visuals=visuals,
            tables=tables,
        )
