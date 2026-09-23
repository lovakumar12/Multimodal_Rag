from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.retrieval.retriever import MultimodalRetriever
from backend.app.schemas.retrieval import SearchRequest, SearchResponse

router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    retriever = MultimodalRetriever(db)
    return await retriever.search(
        query=request.query,
        kb_id=request.kb_id,
        top_k=request.top_k,
        include_visuals=request.include_visuals,
        include_tables=request.include_tables,
    )
