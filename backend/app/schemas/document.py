from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    page_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExtractedImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    page_id: str
    page_number: Optional[int] = None
    image_index: int
    asset_url: str
    width: int
    height: int
    caption: Optional[str] = None
    semantic_description: Optional[str] = None
    ocr_text: Optional[str] = None
    is_diagram_or_chart: bool = False


class ExtractedTableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    page_id: str
    page_number: Optional[int] = None
    table_index: int
    headers: List[str] = Field(default_factory=list, alias="headers_json")
    rows: List[List[Any]] = Field(default_factory=list, alias="rows_json")
    markdown_content: str
    caption: Optional[str] = None


class DocumentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    page_number: int
    text_content: str
    width: Optional[float] = None
    height: Optional[float] = None
    rendered_image_path: Optional[str] = None
    summary: Optional[str] = None
    images: List[ExtractedImageResponse] = []
    tables: List[ExtractedTableResponse] = []


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kb_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    page_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    pages: List[DocumentPageResponse] = []
    images_count: int = 0
    tables_count: int = 0
    chunks_count: int = 0
