from typing import List
from backend.app.schemas.retrieval import SearchResultSource, SearchResultTable


class CrossModalReranker:
    """Reranker that re-evaluates candidate evidence for optimal context presentation."""

    def rerank_sources(self, query: str, sources: List[SearchResultSource]) -> List[SearchResultSource]:
        if not sources:
            return []

        # Simple high-speed lexical-semantic composite boost
        query_terms = set(query.lower().split())
        scored_sources = []
        for s in sources:
            text_lower = s.snippet.lower()
            term_matches = sum(1 for term in query_terms if term in text_lower)
            lexical_boost = min(0.2, (term_matches / max(1, len(query_terms))) * 0.2)
            composite_score = s.score + lexical_boost
            scored_sources.append((composite_score, s))

        scored_sources.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored_sources]


reranker = CrossModalReranker()
