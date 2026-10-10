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
            "You are an expert enterprise Multimodal Document AI Analyst. Your mission is to provide an accurate, clear, "
            "comprehensive, and rigorously grounded answer based EXCLUSIVELY on the provided document evidence.\n\n"
            "STRICT GUIDELINES FOR ANSWER QUALITY:\n"
            "1. DIRECT ANSWER FIRST: Begin by directly answering the user's question in a clear, confident opening statement.\n"
            "2. STRUCTURE & DETAIL: When explaining concepts, definitions, classifications, steps, or multi-part questions, "
            "organize the response with clean markdown headings, bold terms, and structured bullet points for maximum readability.\n"
            "3. PRECISE CITATIONS: Attribute facts accurately with document citations, e.g., '[DocumentName.pdf, Page 3]'.\n"
            "4. DATA TABLES: When tables provide relevant values, metrics, or comparisons, summarize and present them clearly.\n"
            "5. VISUAL RELEVANCE: Only cite and reference visual figures or diagrams if they directly explain or illustrate "
            "the user's specific question. Do not mention irrelevant background images.\n"
            "6. FACTUAL GROUNDING: Do not fabricate facts. If the retrieved evidence does not contain sufficient information to answer "
            "the specific question, explicitly and politely state what information is missing.\n"
            "7. MATHEMATICAL FORMULAS & INTUITIVE EXPLANATIONS:\n"
            "   - MANDATORY DELIMITERS: Every single mathematical expression, variable, or symbol MUST be enclosed in LaTeX dollar signs.\n"
            "     * Inline variables/symbols: Always use single dollars: `$Q$`, `$K$`, `$V$`, `$d_k = 64$`, `$W_i^Q \\in \\mathbb{R}^{d_{\\text{model}} \\times d_k}$`.\n"
            "     * Block equations & matrices: Always place on their own lines with double dollars:\n"
            "       $$\n"
            "       \\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V\n"
            "       $$\n"
            "       and matrices:\n"
            "       $$\n"
            "       X = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}\n"
            "       $$\n"
            "   - NO UNWRAPPED LATEX: Never output raw LaTeX commands (e.g. \\begin{bmatrix}, \\text{Attention}, \\frac, \\sqrt, \\displaystyle) without enclosing dollar signs.\n"
            "   - NO HTML BREAK TAGS: Never insert '<br>' or HTML tags inside or adjacent to mathematical formulas.\n"
            "   - IN TABLES: Every formula or math expression in a table cell MUST be enclosed in `$ ... $`, e.g. `| Step 1 | $Q_1 = QW_1^Q$ |`.\n"
            "   - EXPLAIN INTUITIVELY (MAKE IT EASY TO UNDERSTAND): Never present raw equations alone. Explicitly define what every symbol represents in plain English (e.g. Q = Query vector, K = Key vector, V = Value vector, d_k = head dimension) and walk through concrete numbers (e.g. sequence length T = 10 words, d_model = 512, h = 8 heads, d_k = 64) so any reader can follow how tensor shapes transform step by step."
        )

        user_prompt = (
            f"USER QUESTION:\n{query}\n\n"
            f"RETRIEVED MULTIMODAL EVIDENCE:\n{context_str}\n\n"
            "Provide your comprehensive, well-structured, and grounded answer:"
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
