import base64
import io
import re
from typing import Optional, Tuple
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.logging import logger


class VisionDescriber:
    """Multimodal vision service to generate rich semantic descriptions of images, diagrams, and charts."""

    def __init__(self):
        self.gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")

    def describe(
        self,
        image_bytes: bytes,
        image_format: str = "PNG",
        surrounding_text: Optional[str] = None,
        existing_caption: Optional[str] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Analyzes the image and returns:
        (semantic_description, is_diagram_or_chart, generated_or_refined_caption)
        """
        # If auto describe is disabled, return basic heuristic description
        if not settings.AUTO_DESCRIBE_IMAGES:
            return self._heuristic_describe(image_bytes, surrounding_text, existing_caption)

        # 1. Try Gemini Vision if available
        if self.gemini_client:
            try:
                desc, is_chart, caption = self._gemini_describe(
                    image_bytes, image_format, surrounding_text, existing_caption
                )
                if desc:
                    return desc, is_chart, caption
            except Exception as e:
                logger.warning(f"Gemini vision description failed, falling back: {e}")

        # 2. Try OpenAI Vision if available
        if self.openai_client:
            try:
                desc, is_chart, caption = self._openai_describe(
                    image_bytes, image_format, surrounding_text, existing_caption
                )
                if desc:
                    return desc, is_chart, caption
            except Exception as e:
                logger.warning(f"OpenAI vision description failed, falling back: {e}")

        # 3. Deterministic Heuristic Fallback
        return self._heuristic_describe(image_bytes, surrounding_text, existing_caption)

    def _gemini_describe(
        self,
        image_bytes: bytes,
        image_format: str,
        surrounding_text: Optional[str],
        existing_caption: Optional[str],
    ) -> Tuple[str, bool, Optional[str]]:
        mime_type = f"image/{image_format.lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        prompt = (
            "Analyze this visual artifact from a document (which may be a diagram, chart, graph, architecture illustration, "
            "table-image, or photo).\n"
            f"Context around the image: {surrounding_text[:400] if surrounding_text else 'None'}\n"
            f"Existing caption: {existing_caption or 'None'}\n\n"
            "Provide a clear, detailed semantic summary of what this image shows:\n"
            "1. State whether it is a Diagram, Chart/Graph, Architecture Diagram, Screenshot, or General Illustration.\n"
            "2. Detail all components, labels, flow arrows, comparisons, axes, or data points depicted.\n"
            "3. Conclude with a concise 1-sentence title/caption."
        )

        response = self.gemini_client.models.generate_content(
            model=settings.VISION_MODEL,
            contents=[
                {"inline_data": {"data": base64.b64encode(image_bytes).decode("utf-8"), "mime_type": mime_type}},
                prompt,
            ],
        )

        text = response.text.strip() if response.text else ""
        is_diagram_or_chart = any(
            kw in text.lower()
            for kw in ["diagram", "chart", "graph", "architecture", "flowchart", "schematic", "plot", "workflow"]
        )

        caption = existing_caption
        caption_match = re.search(r"(?:caption|title):\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        if caption_match:
            caption = caption_match.group(1).strip().strip('"*')

        return text, is_diagram_or_chart, caption

    def _openai_describe(
        self,
        image_bytes: bytes,
        image_format: str,
        surrounding_text: Optional[str],
        existing_caption: Optional[str],
    ) -> Tuple[str, bool, Optional[str]]:
        mime_type = f"image/{image_format.lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Analyze this visual from a document. Describe the content, diagram flow, charts, and key labels in detail. "
            f"Context: {surrounding_text[:300] if surrounding_text else 'N/A'}"
        )

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=400,
        )

        text = response.choices[0].message.content.strip()
        is_diagram_or_chart = any(
            kw in text.lower()
            for kw in ["diagram", "chart", "graph", "architecture", "flowchart", "schematic", "plot"]
        )
        return text, is_diagram_or_chart, existing_caption

    def _heuristic_describe(
        self,
        image_bytes: bytes,
        surrounding_text: Optional[str],
        existing_caption: Optional[str],
    ) -> Tuple[str, bool, Optional[str]]:
        """Fallback description based on PIL metadata and surrounding context."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            mode = img.mode
        except Exception:
            w, h, mode = 0, 0, "Unknown"

        is_chart = False
        if surrounding_text:
            lowered = surrounding_text.lower()
            if any(k in lowered for k in ["figure", "diagram", "chart", "graph", "architecture", "table", "plot"]):
                is_chart = True

        desc_parts = [f"Image artifact ({w}x{h}, {mode})."]
        if existing_caption:
            desc_parts.append(f"Caption: {existing_caption}.")
        if surrounding_text:
            desc_parts.append(f"Nearby context: {surrounding_text[:200]}...")
        if is_chart:
            desc_parts.append("Visual evidence indicates an informational diagram, figure, or chart.")

        return " ".join(desc_parts), is_chart, existing_caption


vision_describer = VisionDescriber()
