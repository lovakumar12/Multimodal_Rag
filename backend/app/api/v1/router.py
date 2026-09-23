from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    assets,
    chat,
    documents,
    health,
    knowledge_bases,
    search,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(search.router)
api_router.include_router(assets.router)
