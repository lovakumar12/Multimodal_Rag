from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedImageData:
    image_bytes: bytes
    format: str = "PNG"
    width: int = 0
    height: int = 0
    page_number: int = 1
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    semantic_description: Optional[str] = None
    surrounding_text: Optional[str] = None
    is_diagram_or_chart: bool = False
    bbox: Optional[List[float]] = None


@dataclass
class ExtractedTableData:
    headers: List[str]
    rows: List[List[Any]]
    markdown: str
    page_number: int = 1
    table_index: int = 0
    caption: Optional[str] = None
    surrounding_text: Optional[str] = None
    bbox: Optional[List[float]] = None


@dataclass
class ExtractedSectionData:
    title: str
    level: int = 1
    page_number: int = 1
    order_index: int = 0


@dataclass
class ExtractedPageData:
    page_number: int
    text: str
    width: Optional[float] = None
    height: Optional[float] = None
    rendered_image_bytes: Optional[bytes] = None
    sections: List[ExtractedSectionData] = field(default_factory=list)
    images: List[ExtractedImageData] = field(default_factory=list)
    tables: List[ExtractedTableData] = field(default_factory=list)


@dataclass
class ExtractionResult:
    filename: str
    file_type: str
    page_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: List[ExtractedPageData] = field(default_factory=list)


class BaseExtractor(ABC):
    """Abstract interface for document format extractors."""

    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Extracts structured text, headings, tables, and images from document bytes."""
        pass
