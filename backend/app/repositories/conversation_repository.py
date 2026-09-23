from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.entities import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, kb_id: str, title: str = "New Conversation") -> Conversation:
        conv = Conversation(kb_id=kb_id, title=title)
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_kb(self, kb_id: str) -> List[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.kb_id == kb_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources_json: Optional[List[Dict[str, Any]]] = None,
        visuals_json: Optional[List[Dict[str, Any]]] = None,
        tables_json: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources_json=sources_json or [],
            visuals_json=visuals_json or [],
            tables_json=tables_json or [],
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def update_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        conv = await self.get_by_id(conversation_id)
        if not conv:
            return None
        conv.title = title
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def delete(self, conversation_id: str) -> bool:
        conv = await self.get_by_id(conversation_id)
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.flush()
        return True
