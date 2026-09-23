from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    kb_id: Optional[str] = Field(None, description="Optional Knowledge Base filter")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")
    include_visuals: bool = Field(True, description="Retrieve relevant images/charts")
    include_tables: bool = Field(True, description="Retrieve relevant tables")


class SearchResultSource(BaseModel):
    document_id: str
    document_name: str
    page: int
    content_type: str = "text"  # text, table, image
    snippet: str
    score: float


class SearchResultVisual(BaseModel):
    asset_id: str
    type: str = "image"  # image, diagram, chart
    document_id: str
    document_name: str
    page: int
    url: str
    caption: Optional[str] = None
    semantic_description: Optional[str] = None
    relevance_score: float


class SearchResultTable(BaseModel):
    table_id: str
    document_id: str
    document_name: str
    page: int
    markdown: str
    headers: List[str] = []
    rows: List[List[Any]] = []
    caption: Optional[str] = None
    score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    sources: List[SearchResultSource] = []
    visuals: List[SearchResultVisual] = []
    tables: List[SearchResultTable] = []
