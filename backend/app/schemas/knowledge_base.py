from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of knowledge base")
    description: Optional[str] = Field(None, description="Description of knowledge base")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    owner_id: Optional[str] = Field("default_tenant", description="Owner or tenant ID")


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
