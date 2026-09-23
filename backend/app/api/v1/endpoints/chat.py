from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
)
from backend.app.services.chat_service import ChatService

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.execute_chat(request)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.list_conversations(kb_id)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.get_conversation(conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    await service.delete_conversation(conversation_id)
    return None
