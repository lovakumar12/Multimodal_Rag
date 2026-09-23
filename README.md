# Enterprise Multimodal RAG Platform

> **A Production-Grade, Scalable Multimodal Retrieval-Augmented Generation (RAG) Platform for Complex Documents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 🌟 Overview & Architecture Philosophy

Standard RAG architectures treat documents as flat streams of text. When documents contain architecture diagrams, financial charts, multi-column data tables, screenshots, and complex hierarchical layouts (such as PDFs, PPTX slide decks, DOCX reports, and technical schematics), traditional RAG fails:

- **Lost Visual Context**: Crucial diagrams and charts are ignored or discarded.
- **Table Corruption**: Multi-row, multi-column tables are crushed into fragmented tokens.
- **Missing Hierarchical Lineage**: Relationships between document sections, pages, captions, and visual blocks are severed.
- **Hallucinated Answers**: Generative models cannot cite or display original visual evidence.

This platform solves multimodal document intelligence by implementing a **Decoupled SaaS Architecture** with a relational hierarchy, multi-signal image scoring, graph-expanded hybrid retrieval, and strictly grounded multimodal synthesis.

```
                              ┌─────────────────────────────────────────┐
                              │           React + Vite Frontend         │
                              │  (Visual Cards, Table View, Citations)  │
                              └────────────────────┬────────────────────┘
                                                   │ HTTP / REST
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Application                                  │
│  ┌───────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────┐  │
│  │ Document Ingestion &  │  │   Hybrid Retriever & Graph   │  │ Grounded Generator  │  │
│  │ Multimodal Extractors │  │      Relationship Scorer     │  │  (Gemini / OpenAI)  │  │
│  └───────────┬───────────┘  └──────────────┬───────────────┘  └──────────┬──────────┘  │
└──────────────┼─────────────────────────────┼─────────────────────────────┼─────────────┘
               │                             │                             │
               ▼                             ▼                             ▼
┌──────────────────────────────┐ ┌───────────────────────┐ ┌─────────────────────────────┐
│ Relational Database (SQLite/ │ │ Vector Store (FAISS / │ │ Object Storage (Local / S3) │
│ PostgreSQL + pgvector)       │ │ pgvector Index)       │ │ (Page Renders, Images, Docs)│
└──────────────────────────────┘ └───────────────────────┘ └─────────────────────────────┘
```

---

## 🚀 Key Platform Capabilities

### 1. Robust Multimodal Extraction Across Formats
- **PDF**: PyMuPDF + pdfplumber hybrid extracting font-size heading hierarchies, 120 DPI page previews, structured tables (both JSON and clean Markdown), and embedded vector/raster images with bounding coordinates.
- **PowerPoint (PPTX)**: python-pptx extractor treating slides as first-class pages, extracting shapes, tables, speaker notes, and embedded high-resolution graphics.
- **Word (DOCX)**: python-docx extractor preserving heading levels (H1–H3), multi-column tables, inline figures, and logical pagination.
- **Images (PNG, JPG, TIFF, WEBP)**: Direct OCR via pytesseract and multimodal vision descriptions.

### 2. Vision Understanding & Automated Description
- Generates high-fidelity textual summaries and structural descriptions for all figures, charts, and diagrams using **Google Gemini 3.5 Flash Lite** or **OpenAI GPT-4o Vision**.
- Automatic heuristic fallback ensures the pipeline never halts even when offline or without API credits.

### 3. Hierarchical Relational Data Model
Preserves full document lineage from file to atomic chunk:
```
KnowledgeBase ──> Document ──> DocumentPage ──> DocumentSection ──> ContentBlock
                                                                          ├── TextChunk
                                                                          ├── ExtractedImage
                                                                          └── ExtractedTable
```

### 4. Graph-Expanded Hybrid Retrieval & Multi-Signal Image Scoring
Combines semantic dense vector search with document structural relationships:
- If a relevant text chunk is retrieved, the retriever traverses relationships to surface co-located tables, figures, and page previews from that section.
- **Multi-Signal Image Relevance Formula**:
  $$S_{image}(q, I) = w_1 S_{desc}(q, I) + w_2 S_{text}(q, T_{assoc}) + w_3 S_{caption}(q, I_{cap}) + w_4 S_{page}(q, P_{assoc}) + w_5 \mathbb{I}_{co-occur}$$
  Weights default to $w_1=0.35, w_2=0.25, w_3=0.15, w_4=0.15, w_5=0.10$.

### 5. Grounded Multimodal Synthesis & Interactive Citations
- LLM is instructed with strict grounding rules: answers are synthesized solely from retrieved context.
- Generates precise bracketed citations: `[Doc: filename, Page: X, Section: Y]`.
- Directly returns structured tables and original visual evidence cards with confidence score meters.

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+, Uvicorn, AnyIO) |
| **ORM & Database** | SQLAlchemy 2.0 (Async), `aiosqlite` (local) & PostgreSQL + `pgvector` (production) |
| **Vector Engine** | [FAISS](https://github.com/facebookresearch/faiss) (Flat inner-product cosine) & pgvector |
| **Embeddings** | [Sentence-Transformers](https://sbert.net/) (`all-MiniLM-L6-v2`), Gemini `text-embedding-004` |
| **LLM & Vision** | Google Gemini (`gemini-3.5-flash-lite`, `gemini-3.6-flash`), OpenAI (`gpt-4o`) |
| **Frontend Framework** | [React 19](https://react.dev/), [TypeScript 5.7](https://www.typescriptlang.org/), [Vite 6](https://vitejs.dev/) |
| **Styling & Icons** | [Tailwind CSS v4](https://tailwindcss.com/), [Lucide React](https://lucide.dev/) |
| **HTTP Client** | Axios |
| **Containerization** | Docker, Docker Compose, Multi-stage builds, Nginx reverse proxy |

---

## 📁 Repository Structure

```
Multimodal_Rag/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI route controllers (health, kb, docs, chat, search, assets)
│   │   ├── core/                # Configuration, async DB session, logging, security, errors
│   │   ├── embeddings/          # SentenceTransformers, Gemini, OpenAI embedding providers
│   │   ├── extraction/          # Hybrid PDF, PPTX, DOCX, and Image extractors + Vision describer
│   │   ├── generation/          # Grounded generator, context assembler, LLM provider
│   │   ├── ingestion/           # Pipeline coordinator, structure chunker, relationship builder
│   │   ├── models/              # Normalized SQLAlchemy entity models
│   │   ├── repositories/        # Async DB access layer with eager relationship loading
│   │   ├── reranking/           # Cross-modal reranker
│   │   ├── retrieval/           # Hybrid retriever, vector store, multi-signal image scorer
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic (KB, Document, Chat services)
│   │   ├── storage/             # Local and S3 storage services
│   │   └── workers/             # Background ingestion task worker
│   ├── tests/                   # Pytest test suite (unit, integration, end-to-end)
│   ├── Dockerfile               # Multi-stage Python 3.12 backend container
│   ├── requirements.txt         # Pinned backend dependencies
│   └── run.py                   # Development application runner
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Typed Axios API client
│   │   ├── components/          # VisualEvidenceCard, TableViewer, SourceDrawer, FileUploadModal, Navbar
│   │   ├── pages/               # DashboardPage, KnowledgeBasesPage, DocumentsPage, ChatPage
│   │   ├── types/index.ts       # Shared TypeScript schemas
│   │   ├── App.tsx              # Main application router and state
│   │   └── index.css            # Tailwind CSS v4 styling
│   ├── Dockerfile               # Production multi-stage Nginx build
│   ├── nginx.conf               # SPA routing & API reverse proxy configuration
│   ├── package.json             # NPM scripts and dependencies
│   └── vite.config.ts           # Vite dev server and proxy config
├── docs/                        # Comprehensive Architecture & Deployment Documentation
│   ├── architecture.md          # Relational diagrams & design choices
│   ├── rag-pipeline.md          # Multi-signal scoring formulas & ingestion deep-dive
│   ├── api.md                   # Complete REST OpenAPI documentation
│   └── deployment.md            # AWS ECS/Fargate, RDS Aurora, S3, Docker Compose guide
├── docker-compose.yml           # Full-stack Docker orchestration
├── .env.example                 # Template for environment configuration
└── README.md                    # Platform documentation (this file)
```

---

## ⚡ Quickstart: Local Development

### Prerequisites
- **Python**: 3.12 or higher
- **Node.js**: 20 or higher & npm
- **Tesseract OCR** (optional, for image OCR fallback)

### 1. Environment Configuration
Clone the repository and create your `.env` file from the example:
```bash
cp .env.example .env
```

Edit `.env` to configure your API keys (optional if running in offline fallback mode):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
DEFAULT_LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=sentence-transformers
AUTO_DESCRIBE_IMAGES=true
```

### 2. Backend Setup & Startup
Navigate to the root directory and install Python dependencies:
```bash
pip install -r backend/requirements.txt
```

Start the FastAPI backend:
```bash
python backend/run.py
```
* The backend API will be live at `http://localhost:8000`
* Interactive OpenAPI Swagger docs: `http://localhost:8000/docs`
* Health check: `http://localhost:8000/api/v1/health`

### 3. Frontend Setup & Startup
In a separate terminal, navigate to the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```
* The React frontend will be live at `http://localhost:5173`
* Vite automatically proxies `/api/` calls to `http://localhost:8000`

---

## 🐳 Quickstart: Docker Compose

To launch the full enterprise stack (FastAPI backend, React frontend, PostgreSQL with pgvector, and Redis cache):

```bash
# Build and start all services
docker compose up --build -d

# View service logs
docker compose logs -f

# Stop all services
docker compose down
```

Services exposed:
- **Frontend SPA**: `http://localhost:3000`
- **Backend API & Swagger**: `http://localhost:8000/docs`
- **PostgreSQL Vector DB**: `localhost:5432`

---

## 🧪 Running the Test Suite

The platform includes comprehensive unit, integration, and end-to-end tests covering all extractors, the chunker, the image relevance scorer, API endpoints, and the full multimodal pipeline.

Run the entire suite with pytest:
```bash
python -m pytest backend/tests/ -v
```

Run specific test modules:
```bash
# Multi-signal image scorer tests
python -m pytest backend/tests/test_image_scorer.py -v

# Document extractors (PDF, PPTX, DOCX)
python -m pytest backend/tests/test_extractors.py -v

# Full end-to-end RAG pipeline
python -m pytest backend/tests/test_end_to_end.py -v
```

---

## 📖 In-Depth Documentation

For advanced architecture guides, deployment patterns, and API contracts, refer to the `docs/` directory:

- 🏛️ **[System Architecture](docs/architecture.md)**: Layered design, domain models, entity relationships, and async lifecycle.
- 🔬 **[Multimodal RAG Pipeline](docs/rag-pipeline.md)**: Extraction techniques, structure-aware chunking, vector indexing, image scoring formulas, and prompt engineering.
- 📡 **[REST API Reference](docs/api.md)**: Endpoints, request/response JSON schemas, and error codes.
- 🚀 **[Production Deployment Guide](docs/deployment.md)**: AWS ECS/Fargate, S3, RDS Aurora PostgreSQL, Redis, and observability.

---

## 🛡️ License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
