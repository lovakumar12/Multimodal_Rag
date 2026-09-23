from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.errors import AppError, app_error_handler, http_error_handler
from backend.app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting up Multimodal RAG Platform Backend...")
    await init_db()
    try:
        from backend.app.core.database import AsyncSessionLocal
        from backend.app.retrieval.vector_store import vector_store
        async with AsyncSessionLocal() as session:
            await vector_store.sync_from_db(session)
    except Exception as e:
        logger.warning(f"Vector store sync on startup encountered an issue: {e}")
    yield
    logger.info("Shutting down Multimodal RAG Platform Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade Multimodal RAG Platform supporting PDF, PPTX, DOCX, and images. "
        "Extracts text, headings, tables, diagrams, and figures, preserves hierarchical relationships, "
        "and performs hybrid multimodal retrieval with grounded LLM generation and original visual citations."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)

# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Also include health endpoints at root level for cloud orchestration / load balancers
from backend.app.api.v1.endpoints.health import router as health_router
app.include_router(health_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
