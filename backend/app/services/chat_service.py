from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import NotFoundError
from backend.app.generation.generator import rag_generator
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.kb_repository import KnowledgeBaseRepository
from backend.app.reranking.reranker import reranker
from backend.app.retrieval.retriever import MultimodalRetriever
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
)


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.kb_repo = KnowledgeBaseRepository(session)
        self.retriever = MultimodalRetriever(session)

    async def execute_chat(self, req: ChatRequest) -> ChatResponse:
        # 1. Verify Knowledge Base
        kb = await self.kb_repo.get_by_id(req.kb_id)
        if not kb:
            raise NotFoundError("Knowledge Base", req.kb_id)

        # 2. Get or create Conversation
        conv_id = req.conversation_id
        if not conv_id:
            # Generate short title from query
            title = req.query[:40] + ("..." if len(req.query) > 40 else "")
            conv = await self.conv_repo.create(kb_id=req.kb_id, title=title)
            conv_id = conv.id
        else:
            conv = await self.conv_repo.get_by_id(conv_id)
            if not conv:
                conv = await self.conv_repo.create(kb_id=req.kb_id, title=req.query[:40])
                conv_id = conv.id

        # 3. Save User Message
        await self.conv_repo.add_message(
            conversation_id=conv_id,
            role="user",
            content=req.query,
        )

        # 4. Multimodal Retrieval with Relationship Expansion
        search_res = await self.retriever.search(
            query=req.query,
            kb_id=req.kb_id,
            top_k=req.top_k,
            include_visuals=True,
            include_tables=True,
        )

        # 5. Rerank Sources
        reranked_sources = reranker.rerank_sources(req.query, search_res.sources)

        # 6. Generate Grounded Answer
        answer, confidence = rag_generator.generate_answer(
            query=req.query,
            sources=reranked_sources,
            visuals=search_res.visuals,
            tables=search_res.tables,
        )

        # 7. Persist Assistant Message
        assistant_msg = await self.conv_repo.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=answer,
            sources_json=[s.model_dump() for s in reranked_sources],
            visuals_json=[v.model_dump() for v in search_res.visuals],
            tables_json=[t.model_dump() for t in search_res.tables],
        )
        await self.session.commit()

        return ChatResponse(
            conversation_id=conv_id,
            message_id=assistant_msg.id,
            answer=answer,
            confidence=confidence,
            sources=reranked_sources,
            visuals=search_res.visuals,
            tables=search_res.tables,
        )

    async def list_conversations(self, kb_id: str) -> List[ConversationResponse]:
        convs = await self.conv_repo.list_by_kb(kb_id)
        return [
            ConversationResponse(
                id=c.id,
                kb_id=c.kb_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                messages=[
                    MessageResponse(
                        id=m.id,
                        conversation_id=m.conversation_id,
                        role=m.role,
                        content=m.content,
                        sources_json=m.sources_json or [],
                        visuals_json=m.visuals_json or [],
                        tables_json=m.tables_json or [],
                        created_at=m.created_at,
                    )
                    for m in c.messages
                ]
                if hasattr(c, "messages") and c.messages
                else [],
            )
            for c in convs
        ]

    async def get_conversation(self, conversation_id: str) -> ConversationResponse:
        c = await self.conv_repo.get_by_id(conversation_id)
        if not c:
            raise NotFoundError("Conversation", conversation_id)
        return ConversationResponse(
            id=c.id,
            kb_id=c.kb_id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    sources_json=m.sources_json or [],
                    visuals_json=m.visuals_json or [],
                    tables_json=m.tables_json or [],
                    created_at=m.created_at,
                )
                for m in c.messages
            ],
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        success = await self.conv_repo.delete(conversation_id)
        if not success:
            raise NotFoundError("Conversation", conversation_id)
        await self.session.commit()
        return True
