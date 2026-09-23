from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate
from backend.app.services.kb_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(data: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    return await service.create_kb(data)


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(owner_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    return await service.list_kbs(owner_id)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    return await service.get_kb(kb_id)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    await service.delete_kb(kb_id)
    return None
