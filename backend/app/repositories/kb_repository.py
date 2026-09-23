from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.entities import KnowledgeBase, Document


class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: Optional[str] = None, owner_id: str = "default_tenant") -> KnowledgeBase:
        kb = KnowledgeBase(name=name, description=description, owner_id=owner_id)
        self.session.add(kb)
        await self.session.flush()
        await self.session.refresh(kb)
        return kb

    async def get_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        query = (
            select(KnowledgeBase)
            .where(KnowledgeBase.id == kb_id)
            .options(selectinload(KnowledgeBase.documents))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, owner_id: Optional[str] = None) -> List[tuple[KnowledgeBase, int]]:
        query = (
            select(KnowledgeBase, func.count(Document.id).label("doc_count"))
            .outerjoin(Document, KnowledgeBase.id == Document.kb_id)
            .group_by(KnowledgeBase.id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        if owner_id:
            query = query.where(KnowledgeBase.owner_id == owner_id)
        result = await self.session.execute(query)
        return result.all()

    async def update(self, kb_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[KnowledgeBase]:
        kb = await self.get_by_id(kb_id)
        if not kb:
            return None
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        await self.session.flush()
        await self.session.refresh(kb)
        return kb

    async def delete(self, kb_id: str) -> bool:
        kb = await self.get_by_id(kb_id)
        if not kb:
            return False
        await self.session.delete(kb)
        await self.session.flush()
        return True
