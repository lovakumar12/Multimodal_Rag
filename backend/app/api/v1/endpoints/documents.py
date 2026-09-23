from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.document import (
    DocumentDetailResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    kb_id: str = Form(..., description="Target Knowledge Base ID"),
    file: UploadFile = File(..., description="Document file to upload (PDF, PPTX, DOCX, PNG, JPG)"),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    return await service.upload_document(kb_id=kb_id, file=file, background_tasks=background_tasks)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    return await service.list_documents(kb_id=kb_id)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    return await service.get_document_detail(document_id=document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    return await service.get_document_status(document_id=document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    await service.delete_document(document_id=document_id)
    return None
