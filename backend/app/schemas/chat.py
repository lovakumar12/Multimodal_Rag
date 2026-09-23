from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.retrieval import SearchResultSource, SearchResultTable, SearchResultVisual


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or prompt")
    kb_id: str = Field(..., description="Target Knowledge Base ID")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue thread")
    top_k: int = Field(5, ge=1, le=15, description="Number of evidence chunks to retrieve")
    stream: bool = Field(False, description="Whether to stream the response")


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list, alias="sources_json")
    visuals: List[Dict[str, Any]] = Field(default_factory=list, alias="visuals_json")
    tables: List[Dict[str, Any]] = Field(default_factory=list, alias="tables_json")
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kb_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    confidence: float = 0.95
    sources: List[SearchResultSource] = []
    visuals: List[SearchResultVisual] = []
    tables: List[SearchResultTable] = []
