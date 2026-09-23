import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import faiss
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger


class VectorIndexEntry:
    def __init__(
        self,
        entity_id: str,
        entity_type: str,  # text_chunk, table, image, page
        document_id: str,
        kb_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.document_id = document_id
        self.kb_id = kb_id
        self.metadata = metadata or {}


class LocalVectorStore:
    """FAISS-backed vector store for high-performance similarity search with persistence and DB sync."""

    def __init__(self, dimension: int = settings.VECTOR_DIMENSION):
        self.dimension = dimension
        # IndexFlatIP with normalized vectors computes exact cosine similarity
        self.index = faiss.IndexFlatIP(dimension)
        self.entries: List[VectorIndexEntry] = []
        self.index_dir = settings.BASE_DATA_DIR / "indexes"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "faiss.index"
        self.entries_file = self.index_dir / "entries.pkl"
        self.load()

    def save(self) -> None:
        """Persists the FAISS index and metadata entries to disk."""
        try:
            if self.index.ntotal > 0:
                faiss.write_index(self.index, str(self.index_file))
                with open(self.entries_file, "wb") as f:
                    pickle.dump(self.entries, f)
                logger.info(f"Persisted FAISS index with {self.index.ntotal} vectors to {self.index_file}")
        except Exception as e:
            logger.warning(f"Failed to persist FAISS index: {e}")

    def load(self) -> bool:
        """Loads the FAISS index and metadata entries from disk if available."""
        try:
            if self.index_file.exists() and self.entries_file.exists():
                loaded_index = faiss.read_index(str(self.index_file))
                with open(self.entries_file, "rb") as f:
                    loaded_entries = pickle.load(f)
                self.index = loaded_index
                self.entries = loaded_entries
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors from {self.index_file}")
                return True
        except Exception as e:
            logger.warning(f"Could not load FAISS index from disk ({e}), starting fresh.")
        return False

    async def sync_from_db(self, session: AsyncSession) -> None:
        """Synchronizes the in-memory/disk FAISS index from all existing embeddings in the database."""
        from backend.app.models.entities import Document, ExtractedImage, ExtractedTable, TextChunk

        # Query chunks with embeddings
        chunk_stmt = (
            select(TextChunk, Document.kb_id, Document.filename)
            .join(Document, TextChunk.document_id == Document.id)
            .where(TextChunk.embedding.isnot(None))
        )
        chunk_res = await session.execute(chunk_stmt)
        chunk_rows = chunk_res.all()

        # Query tables with embeddings
        table_stmt = (
            select(ExtractedTable, Document.kb_id, Document.filename)
            .join(Document, ExtractedTable.document_id == Document.id)
            .where(ExtractedTable.embedding.isnot(None))
        )
        table_res = await session.execute(table_stmt)
        table_rows = table_res.all()

        # Query images with embeddings
        img_stmt = (
            select(ExtractedImage, Document.kb_id, Document.filename)
            .join(Document, ExtractedImage.document_id == Document.id)
            .where(ExtractedImage.embedding.isnot(None))
        )
        img_res = await session.execute(img_stmt)
        img_rows = img_res.all()

        total_records = len(chunk_rows) + len(table_rows) + len(img_rows)
        if total_records == 0:
            logger.info("No embeddings found in database to sync.")
            return

        # Rebuild fresh index
        new_index = faiss.IndexFlatIP(self.dimension)
        new_entries: List[VectorIndexEntry] = []
        all_vectors: List[List[float]] = []

        # 1. Chunks
        for c, kb_id, filename in chunk_rows:
            all_vectors.append(c.embedding)
            new_entries.append(
                VectorIndexEntry(
                    entity_id=c.id,
                    entity_type="text_chunk",
                    document_id=c.document_id,
                    kb_id=kb_id,
                    metadata={
                        "page_number": c.page_number or 1,
                        "document_name": filename,
                        "snippet": (c.text or "")[:300],
                        "page_id": c.page_id,
                        "associated_image_ids": c.associated_image_ids or [],
                        "associated_table_ids": c.associated_table_ids or [],
                    },
                )
            )

        # 2. Tables
        for t, kb_id, filename in table_rows:
            all_vectors.append(t.embedding)
            new_entries.append(
                VectorIndexEntry(
                    entity_id=t.id,
                    entity_type="table",
                    document_id=t.document_id,
                    kb_id=kb_id,
                    metadata={
                        "page_number": t.page_number or 1,
                        "document_name": filename,
                        "markdown": t.markdown_content or "",
                        "headers": t.headers_json or [],
                        "rows": t.rows_json or [],
                        "caption": t.caption or "",
                    },
                )
            )

        # 3. Images
        for img, kb_id, filename in img_rows:
            all_vectors.append(img.embedding)
            new_entries.append(
                VectorIndexEntry(
                    entity_id=img.id,
                    entity_type="image",
                    document_id=img.document_id,
                    kb_id=kb_id,
                    metadata={
                        "page_number": img.page_number or 1,
                        "document_name": filename,
                        "asset_url": img.asset_url,
                        "caption": img.caption or "",
                        "description": img.semantic_description or "",
                        "is_diagram": img.is_diagram_or_chart,
                    },
                )
            )

        vec_np = np.array(all_vectors, dtype=np.float32)
        faiss.normalize_L2(vec_np)
        new_index.add(vec_np)

        self.index = new_index
        self.entries = new_entries
        self.save()
        logger.info(f"Successfully synced {self.index.ntotal} vectors from database into FAISS index.")

    def add_vectors(
        self,
        vectors: List[List[float]],
        entity_ids: List[str],
        entity_types: List[str],
        document_ids: List[str],
        kb_ids: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not vectors:
            return

        vec_np = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vec_np)

        self.index.add(vec_np)

        meta = metadata_list or [{} for _ in entity_ids]
        for i in range(len(entity_ids)):
            entry = VectorIndexEntry(
                entity_id=entity_ids[i],
                entity_type=entity_types[i],
                document_id=document_ids[i],
                kb_id=kb_ids[i],
                metadata=meta[i],
            )
            self.entries.append(entry)

        self.save()
        logger.info(f"Added {len(vectors)} vectors to index. Total index count: {self.index.ntotal}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        kb_id: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[Tuple[VectorIndexEntry, float]]:
        if self.index.ntotal == 0:
            return []

        q_np = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_np)

        search_k = min(self.index.ntotal, max(top_k * 4, 30))
        scores, indices = self.index.search(q_np, search_k)

        results: List[Tuple[VectorIndexEntry, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.entries):
                continue
            entry = self.entries[idx]

            # Filter by KB
            if kb_id and entry.kb_id != kb_id:
                continue

            # Filter by entity type
            if entity_type and entry.entity_type != entity_type:
                continue

            results.append((entry, float(score)))
            if len(results) >= top_k:
                break

        return results

    def clear(self) -> None:
        self.index.reset()
        self.entries = []
        if self.index_file.exists():
            self.index_file.unlink()
        if self.entries_file.exists():
            self.entries_file.unlink()


vector_store = LocalVectorStore()
