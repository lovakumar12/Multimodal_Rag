import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # pdf, pptx, docx, image
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, UPLOADING, PROCESSING, INDEXING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")
    tables = relationship("ExtractedTable", back_populates="document", cascade="all, delete-orphan")
    images = relationship("ExtractedImage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)  # 1-indexed
    text_content = Column(Text, default="")
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    rendered_image_path = Column(String(512), nullable=True)
    summary = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="pages")
    blocks = relationship("ContentBlock", back_populates="page", cascade="all, delete-orphan")
    chunks = relationship("TextChunk", back_populates="page", cascade="all, delete-orphan")
    images = relationship("ExtractedImage", back_populates="page", cascade="all, delete-orphan")
    tables = relationship("ExtractedTable", back_populates="page", cascade="all, delete-orphan")


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    level = Column(Integer, default=1)  # 1 for H1, 2 for H2, etc.
    order_index = Column(Integer, default=0)

    # Relationships
    document = relationship("Document", back_populates="sections")


class ContentBlock(Base):
    __tablename__ = "content_blocks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True)
    block_type = Column(String(32), nullable=False)  # text, table, image, diagram, chart, caption
    content_json = Column(JSON, default=dict)
    order_index = Column(Integer, default=0)

    # Relationships
    page = relationship("DocumentPage", back_populates="blocks")


class TextChunk(Base):
    __tablename__ = "text_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, default=1, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    heading_context = Column(String(512), nullable=True)
    associated_image_ids = Column(JSON, default=list)  # list of image UUIDs
    associated_table_ids = Column(JSON, default=list)  # list of table UUIDs
    token_count = Column(Integer, default=0)
    embedding = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    page = relationship("DocumentPage", back_populates="chunks")


class ExtractedTable(Base):
    __tablename__ = "extracted_tables"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, default=1, index=True)
    table_index = Column(Integer, default=0)
    headers_json = Column(JSON, default=list)
    rows_json = Column(JSON, default=list)
    markdown_content = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    surrounding_text = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="tables")
    page = relationship("DocumentPage", back_populates="tables")


class ExtractedImage(Base):
    __tablename__ = "extracted_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, default=1, index=True)
    image_index = Column(Integer, default=0)
    asset_path = Column(String(512), nullable=False)
    asset_url = Column(String(512), nullable=False)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    format = Column(String(16), default="PNG")
    caption = Column(Text, nullable=True)
    semantic_description = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    surrounding_text = Column(Text, nullable=True)
    is_diagram_or_chart = Column(Boolean, default=False)
    embedding = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="images")
    page = relationship("DocumentPage", back_populates="images")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources_json = Column(JSON, default=list)
    visuals_json = Column(JSON, default=list)
    tables_json = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
