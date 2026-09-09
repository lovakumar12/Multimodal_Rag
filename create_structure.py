from pathlib import Path


# This script lives in the repository root, so new folders are created here.
ROOT = Path(__file__).resolve().parent

DIRECTORIES = [
    "app",
    "app/api",
    "app/api/routes",
    "app/rag",
    "app/processors",
    "app/models",
    "app/storage",
    "app/schemas",
    "data/uploads",
    "data/images",
    "data/tables",
    "tests",
]

FILES = [
    "app/__init__.py",
    "app/app.py",
    "app/config.py",
    "app/api/__init__.py",
    "app/api/dependencies.py",
    "app/api/routes/__init__.py",
    "app/api/routes/documents.py",
    "app/api/routes/chat.py",
    "app/api/routes/health.py",
    "app/rag/__init__.py",
    "app/rag/ingest.py",
    "app/rag/retrieve.py",
    "app/rag/rerank.py",
    "app/rag/context.py",
    "app/rag/generate.py",
    "app/processors/__init__.py",
    "app/processors/pdf.py",
    "app/processors/text.py",
    "app/processors/image.py",
    "app/processors/table.py",
    "app/models/__init__.py",
    "app/models/embeddings.py",
    "app/models/vision.py",
    "app/models/llm.py",
    "app/storage/__init__.py",
    "app/storage/vector.py",
    "app/storage/metadata.py",
    "app/storage/files.py",
    "app/schemas/__init__.py",
    "app/schemas/document.py",
    "app/schemas/query.py",
    "app/schemas/response.py",
    "tests/test_documents.py",
    "tests/test_retrieval.py",
    "tests/test_chat.py",
    "Dockerfile",
    "docker-compose.yml",
]


def create_structure() -> None:
    print(f"\nCreating the Multimodal RAG structure in {ROOT}...\n")

    for directory in DIRECTORIES:
        path = ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"[DIR]  {path.relative_to(ROOT)}")

    for file in FILES:
        path = ROOT / file
        if path.exists():
            print(f"[SKIP] {path.relative_to(ROOT)} already exists")
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        print(f"[FILE] {path.relative_to(ROOT)}")

    print("\nProject structure created without overwriting existing files.")


if __name__ == "__main__":
    create_structure()