from typing import List, Optional, Tuple
from backend.app.core.logging import logger
from backend.app.generation.llm_provider import get_llm_provider
from backend.app.schemas.retrieval import (
    SearchResultSource,
    SearchResultTable,
    SearchResultVisual,
)


class RAGGroundedGenerator:
    """Multimodal RAG generator with strict grounding and original visual asset citation."""

    def __init__(self):
        self.provider = get_llm_provider()

    def generate_answer(
        self,
        query: str,
        sources: List[SearchResultSource],
        visuals: List[SearchResultVisual],
        tables: List[SearchResultTable],
    ) -> Tuple[str, float]:
        if not sources and not visuals and not tables:
            return (
                "The uploaded documents in this knowledge base do not contain enough information to answer this question. "
                "Please verify your query or upload the relevant document.",
                0.0,
            )

        # 1. Build context blocks
        context_parts: List[str] = []

        # Text chunks
        if sources:
            context_parts.append("### TEXT EVIDENCE:")
            for idx, s in enumerate(sources, 1):
                context_parts.append(
                    f"[{idx}] Source Document: '{s.document_name}', Page {s.page}\nContent: {s.snippet}\n"
                )

        # Tables
        if tables:
            context_parts.append("### STRUCTURED TABLES:")
            for idx, t in enumerate(tables, 1):
                context_parts.append(
                    f"[{idx}] Table from '{t.document_name}', Page {t.page} (Caption: {t.caption or 'N/A'}):\n{t.markdown}\n"
                )

        # Visuals
        if visuals:
            context_parts.append("### VISUAL ARTIFACTS (DIAGRAMS, CHARTS, FIGURES):")
            for idx, v in enumerate(visuals, 1):
                context_parts.append(
                    f"[{idx}] {v.type.upper()} from '{v.document_name}', Page {v.page} (Caption: {v.caption or 'N/A'}):\n"
                    f"Description: {v.semantic_description or 'Visual illustration'}\n"
                )

        context_str = "\n".join(context_parts)

        # 2. System prompt
        system_instruction = (
            "You are an expert enterprise Multimodal AI Analyst. Your mission is to provide an accurate, clear, "
            "and rigorously grounded answer based EXCLUSIVELY on the provided document evidence.\n\n"
            "STRICT RULES:\n"
            "1. Ground your answer completely on the provided text, tables, and visual evidence. Do not extrapolate facts "
            "or invent details not present in the documents.\n"
            "2. Whenever citing information, always mention the document name and page number, e.g. [Document.pdf, Page 12].\n"
            "3. If visual diagrams or charts are relevant, refer to them naturally (e.g., 'As shown in the architecture diagram on Page 2...', 'According to the chart on Page 4...').\n"
            "4. If tables are relevant, discuss or summarize the relevant values from the table.\n"
            "5. If the provided context does not contain sufficient details to answer the user question, state clearly that "
            "the uploaded documents do not contain enough information."
        )

        user_prompt = (
            f"USER QUESTION:\n{query}\n\n"
            f"RETRIEVED MULTIMODAL EVIDENCE:\n{context_str}\n\n"
            "Provide your comprehensive grounded answer:"
        )

        try:
            answer = self.provider.generate(prompt=user_prompt, system_instruction=system_instruction)
            confidence = 0.95 if sources or visuals else 0.50
            return answer, confidence
        except Exception as e:
            logger.error(f"Error during RAG answer generation: {e}. Building grounded summary from retrieved evidence.")
            summary_points = []
            for s in sources[:4]:
                snippet_clean = s.snippet.strip().replace("\n", " ")
                summary_points.append(f"- **From [{s.document_name}, Page {s.page}]**: {snippet_clean[:250]}...")

            if tables:
                for t in tables[:2]:
                    summary_points.append(f"- **Table from [{t.document_name}, Page {t.page}]**: {t.caption or 'Data Table'}")

            if visuals:
                for v in visuals[:2]:
                    desc = v.semantic_description or v.caption or "Visual artifact"
                    summary_points.append(f"- **{v.type.capitalize()} on [{v.document_name}, Page {v.page}]**: {desc[:200]}")

            bullet_text = "\n\n".join(summary_points) if summary_points else "Relevant document evidence was retrieved and is displayed below."
            fallback_answer = (
                f"### Grounded Evidence Summary\n\n"
                f"{bullet_text}\n\n"
                f"*(Answer synthesized directly from retrieved document evidence. Cloud LLM rate-limited: {str(e)[:90]}).*"
            )
            return fallback_answer, 0.75


rag_generator = RAGGroundedGenerator()
