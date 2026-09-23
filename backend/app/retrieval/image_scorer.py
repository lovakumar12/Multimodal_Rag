from typing import Dict, List, Optional
import numpy as np
from backend.app.core.config import settings
from backend.app.models.entities import ExtractedImage


class MultiSignalImageScorer:
    """
    Computes a multi-signal semantic relevance score for document visual assets
    (diagrams, charts, figures) relative to the user query and retrieved text evidence.
    """

    def __init__(
        self,
        w_desc: float = settings.WEIGHT_DESC_SIM,
        w_text: float = settings.WEIGHT_TEXT_SIM,
        w_caption: float = settings.WEIGHT_CAPTION_SIM,
        w_page: float = settings.WEIGHT_PAGE_SIM,
        w_co_occurrence: float = settings.WEIGHT_CO_OCCURRENCE,
        threshold: float = settings.IMAGE_RELEVANCE_THRESHOLD,
    ):
        self.w_desc = w_desc
        self.w_text = w_text
        self.w_caption = w_caption
        self.w_page = w_page
        self.w_co_occurrence = w_co_occurrence
        self.threshold = threshold

    def compute_score(
        self,
        image: ExtractedImage,
        desc_sim: float,
        surrounding_sim: float = 0.0,
        caption_sim: float = 0.0,
        page_relevance: float = 0.0,
        is_co_occurring: bool = False,
    ) -> float:
        """
        Combines weighted signals into a composite relevance score.
        """
        co_occurrence_score = 1.0 if is_co_occurring else 0.0

        # If caption similarity wasn't calculated separately, approximate with description similarity
        if caption_sim == 0.0 and image.caption:
            caption_sim = desc_sim * 0.9

        composite = (
            self.w_desc * max(0.0, desc_sim)
            + self.w_text * max(0.0, surrounding_sim)
            + self.w_caption * max(0.0, caption_sim)
            + self.w_page * max(0.0, page_relevance)
            + self.w_co_occurrence * co_occurrence_score
        )

        # Normalize score into [0.0, 1.0]
        final_score = float(np.clip(composite, 0.0, 1.0))
        return round(final_score, 4)

    def is_relevant(self, score: float) -> bool:
        return score >= self.threshold


image_scorer = MultiSignalImageScorer()
