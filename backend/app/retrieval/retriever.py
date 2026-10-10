import re
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

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "what", "which",
    "where", "when", "who", "why", "how", "are", "was", "were", "been",
    "have", "has", "had", "does", "did", "can", "could", "should", "would",
    "about", "some", "any", "more", "most", "into", "over", "such", "there",
}

VISUAL_KEYWORDS = {
    "diagram", "chart", "graph", "architecture", "figure", "fig", "map",
    "image", "visual", "illustration", "flowchart", "photo", "picture", "drawing", "plot",
}


class MultimodalRetriever:
    """
    Hybrid Multimodal Retriever combining multi-entity vector search,
    lexical keyword matching, relationship graph expansion, and multi-signal visual relevance scoring.
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

        # 1. Analyze query intent and extract significant keywords
        clean_words = set(re.findall(r"\b\w+\b", query.lower()))
        query_has_visual_intent = bool(clean_words.intersection(VISUAL_KEYWORDS))
        query_keywords = [w for w in clean_words if len(w) >= 3 and w not in STOPWORDS]

        # 2. Generate query embedding
        query_vector = self.embedding_provider.embed_text(query)

        # 3. Retrieve candidate text chunks (sample broader pool to allow hybrid reranking)
        fetch_k = max(8, top_k * 2)
        chunk_hits = vector_store.search(
            query_vector=query_vector,
            top_k=fetch_k,
            kb_id=kb_id,
            entity_type="text_chunk",
        )

        candidate_sources: List[SearchResultSource] = []
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

            # Compute lexical keyword overlap bonus
            lexical_overlap = 0.0
            if query_keywords and snippet:
                snippet_lower = snippet.lower()
                matched_kw = sum(1 for kw in query_keywords if kw in snippet_lower)
                lexical_overlap = matched_kw / len(query_keywords)

            # Hybrid score: 70% dense vector similarity + 30% exact term overlap
            hybrid_score = round(0.70 * max(0.0, score) + 0.30 * lexical_overlap, 4)

            candidate_sources.append(
                SearchResultSource(
                    document_id=doc_id,
                    document_name=doc_name,
                    page=page_num,
                    content_type="text",
                    snippet=snippet,
                    score=hybrid_score,
                )
            )

        # Sort sources by hybrid score descending and keep top_k
        candidate_sources.sort(key=lambda s: s.score, reverse=True)
        sources = candidate_sources[:top_k]

        # 4. Retrieve and expand tables
        tables: List[SearchResultTable] = []
        if include_tables:
            table_hits = vector_store.search(
                query_vector=query_vector,
                top_k=4,
                kb_id=kb_id,
                entity_type="table",
            )
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

        # 5. Multi-Signal Visual Retrieval with Strict Relevance Filtering
        visuals: List[SearchResultVisual] = []
        if include_visuals:
            # A. Direct vector hits on image descriptions/OCR
            direct_image_hits = vector_store.search(
                query_vector=query_vector,
                top_k=6,
                kb_id=kb_id,
                entity_type="image",
            )

            candidate_image_map: Dict[str, Dict] = {}
            for entry, score in direct_image_hits:
                # Require meaningful minimum similarity to even consider as candidate
                min_initial_sim = 0.28 if query_has_visual_intent else 0.35
                if score >= min_initial_sim:
                    candidate_image_map[entry.entity_id] = {
                        "entry": entry,
                        "desc_sim": score,
                        "is_co_occurring": False,
                    }

            # B. Relationship Graph Expansion:
            # ONLY expand co-occurring images if user explicitly asked for visuals/diagrams
            if query_has_visual_intent:
                for img_id in associated_image_ids:
                    if img_id not in candidate_image_map:
                        candidate_image_map[img_id] = {
                            "entry": None,
                            "desc_sim": 0.25,
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
                    # Filter out tiny icon/logo images (< 100x100)
                    if (img.width and img.width < 100) or (img.height and img.height < 100):
                        continue

                    cand_info = candidate_image_map.get(img.id, {})
                    desc_sim = cand_info.get("desc_sim", 0.0)
                    is_co = cand_info.get("is_co_occurring", False)

                    # Check if image page matches any top retrieved text chunk pages
                    page_relevance = 1.0 if img.page_id in retrieved_page_ids else 0.0

                    rel_score = image_scorer.compute_score(
                        image=img,
                        desc_sim=desc_sim,
                        surrounding_sim=desc_sim * 0.7,
                        caption_sim=desc_sim * 0.9,
                        page_relevance=page_relevance,
                        is_co_occurring=is_co,
                        query_has_visual_intent=query_has_visual_intent,
                    )

                    if image_scorer.is_relevant(
                        score=rel_score,
                        desc_sim=desc_sim,
                        query_has_visual_intent=query_has_visual_intent,
                        image=img,
                    ):
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
