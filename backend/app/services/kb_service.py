from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import NotFoundError
from backend.app.models.entities import KnowledgeBase
from backend.app.repositories.kb_repository import KnowledgeBaseRepository
from backend.app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeBaseRepository(session)

    async def create_kb(self, data: KnowledgeBaseCreate) -> KnowledgeBaseResponse:
        kb = await self.repo.create(name=data.name, description=data.description, owner_id=data.owner_id)
        await self.session.commit()
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            owner_id=kb.owner_id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=0,
        )

    async def list_kbs(self, owner_id: Optional[str] = None) -> List[KnowledgeBaseResponse]:
        kbs_with_count = await self.repo.list_all(owner_id)
        return [
            KnowledgeBaseResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                owner_id=kb.owner_id,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
                document_count=count,
            )
            for kb, count in kbs_with_count
        ]

    async def get_kb(self, kb_id: str) -> KnowledgeBaseResponse:
        kb = await self.repo.get_by_id(kb_id)
        if not kb:
            raise NotFoundError("Knowledge Base", kb_id)
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            owner_id=kb.owner_id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=len(kb.documents) if kb.documents else 0,
        )

    async def delete_kb(self, kb_id: str) -> bool:
        success = await self.repo.delete(kb_id)
        if not success:
            raise NotFoundError("Knowledge Base", kb_id)
        await self.session.commit()
        return True
