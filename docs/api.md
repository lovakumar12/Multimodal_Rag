# REST API Reference: Multimodal RAG Platform

Version: `v1`  
Base URL: `/api/v1`

---

## 1. Health & Readiness

### `GET /health`
Liveness check for container orchestration and load balancers.
- **Response** `200 OK`:
  ```json
  {
    "status": "healthy",
    "app": "Multimodal RAG Platform",
    "version": "1.0.0",
    "environment": "development"
  }
  ```

### `GET /ready`
Readiness check verifying database connectivity, vector index status, and storage volume availability.
- **Response** `200 OK`:
  ```json
  {
    "status": "ready",
    "database": "connected",
    "vector_store": {
      "indexed_vectors": 52,
      "dimension": 384
    },
    "storage": "local"
  }
  ```

### `GET /api/v1/stats`
Aggregated dashboard statistics.
- **Response** `200 OK`:
  ```json
  {
    "total_documents": 12,
    "processing_documents": 0,
    "completed_documents": 12,
    "failed_documents": 0,
    "total_images": 48,
    "total_tables": 34,
    "total_chunks": 180,
    "total_vectors": 262
  }
  ```

---

## 2. Knowledge Bases

### `POST /api/v1/knowledge-bases`
Create a new knowledge base workspace.
- **Request Body**:
  ```json
  {
    "name": "AI Research Papers",
    "description": "Transformers, RAG, and multimodal foundation models",
    "owner_id": "org_default"
  }
  ```
- **Response** `201 Created`:
  ```json
  {
    "id": "kb_uuid",
    "name": "AI Research Papers",
    "description": "Transformers, RAG, and multimodal foundation models",
    "owner_id": "org_default",
    "document_count": 0,
    "created_at": "2026-09-22T20:00:00Z",
    "updated_at": "2026-09-22T20:00:00Z"
  }
  ```

### `GET /api/v1/knowledge-bases`
List all knowledge bases.
- **Response** `200 OK`: Array of `KnowledgeBaseResponse`.

### `DELETE /api/v1/knowledge-bases/{id}`
Deletes a knowledge base and cascades deletion across all documents, vector indices, and chats.
- **Response** `204 No Content`.

---

## 3. Documents & Ingestion

### `POST /api/v1/documents/upload`
Upload a document (PDF, PPTX, DOCX, PNG, JPG). Dispatches asynchronous extraction and indexing in the background.
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `kb_id`: UUID string (Required)
  - `file`: Binary file upload (Required)
- **Response** `202 Accepted`:
  ```json
  {
    "id": "doc_uuid",
    "kb_id": "kb_uuid",
    "filename": "Transformer_Architecture.pdf",
    "file_type": "pdf",
    "file_size": 2450820,
    "status": "PENDING",
    "page_count": 0,
    "created_at": "2026-09-22T20:00:00Z",
    "updated_at": "2026-09-22T20:00:00Z"
  }
  ```

### `GET /api/v1/documents/{id}/status`
Poll ingestion and indexing progress.
- **Response** `200 OK`:
  ```json
  {
    "id": "doc_uuid",
    "filename": "Transformer_Architecture.pdf",
    "status": "COMPLETED",
    "page_count": 15,
    "error_message": null,
    "created_at": "2026-09-22T20:00:00Z",
    "updated_at": "2026-09-22T20:00:30Z"
  }
  ```

### `GET /api/v1/documents/{id}`
Retrieve complete document inspection details including rendered page images, extracted original figures, and tables.
- **Response** `200 OK`: `DocumentDetailResponse` containing page breakdown.

---

## 4. Multimodal Chat & Retrieval

### `POST /api/v1/chat`
Ask a grounded document question with conversational memory.
- **Request Body**:
  ```json
  {
    "kb_id": "kb_uuid",
    "query": "What is the architecture of the proposed model?",
    "conversation_id": "conv_uuid_optional",
    "top_k": 5
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "conversation_id": "conv_uuid",
    "message_id": "msg_uuid",
    "answer": "As illustrated in Figure 1 on Page 3, the model consists of an encoder and decoder stack...",
    "confidence": 0.95,
    "sources": [
      {
        "document_id": "doc_uuid",
        "document_name": "Transformer_Architecture.pdf",
        "page": 3,
        "content_type": "text",
        "snippet": "[Encoder Architecture] The encoder is composed of a stack of N = 6 identical layers...",
        "score": 0.92
      }
    ],
    "visuals": [
      {
        "asset_id": "asset_uuid",
        "type": "diagram",
        "document_id": "doc_uuid",
        "document_name": "Transformer_Architecture.pdf",
        "page": 3,
        "url": "/api/v1/assets/assets/doc_uuid_p3_i1.png",
        "caption": "Figure 1: The Transformer - model architecture",
        "semantic_description": "Architecture diagram illustrating Scaled Dot-Product Attention...",
        "relevance_score": 0.93
      }
    ],
    "tables": [
      {
        "table_id": "table_uuid",
        "document_id": "doc_uuid",
        "document_name": "Transformer_Architecture.pdf",
        "page": 9,
        "markdown": "| Model | BLEU |\n|---|---|\n| Base | 27.3 |",
        "headers": ["Model", "BLEU"],
        "rows": [["Base", "27.3"]],
        "caption": "Table 1: Variations on the Transformer architecture",
        "score": 0.89
      }
    ]
  }
  ```

---

## 5. Assets Serving

### `GET /api/v1/assets/{file_path}`
Serves extracted original visual artifacts and rendered document page previews with caching headers (`max-age=86400`).
