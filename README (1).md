# Multimodal RAG: Beyond Text RAG
### A 30–40 minute classroom project — 100% free, 100% local (Ollama), no API keys

Students already know basic RAG (PDF → chunks → embeddings → FAISS → LLM). This project shows
how the *same* retrieval pipeline extends to **tables** and **images/charts**, using only local,
free tools — runnable entirely inside Google Colab's free GPU tier.

---

## 1. Folder structure

```
multimodal_rag/
├── README.md                          # this file
├── requirements.txt                   # pip dependencies (reference)
├── Multimodal_RAG_Classroom.ipynb     # the full runnable notebook — open this in Colab
└── data/
    ├── sample_report.pdf              # <- put your PDF here (or upload it inside the notebook)
    └── extracted_images/              # created automatically when the notebook runs
```

## 2. Installation instructions

1. Open `Multimodal_RAG_Classroom.ipynb` in **Google Colab**.
2. `Runtime → Change runtime type → T4 GPU` (free tier is enough).
3. Run the cells top to bottom. The notebook installs everything itself:
   - Python packages via `pip install`
   - Ollama via `curl -fsSL https://ollama.com/install.sh | sh`
   - The vision-language model via `ollama pull qwen2.5vl:3b`

No OpenAI / Gemini / Claude / Groq / AWS account or API key is required anywhere.

## 3. Local models used

| Purpose | Model | Approx. size / requirement |
|---|---|---|
| Text embeddings | `all-MiniLM-L6-v2` (Sentence-Transformers) | ~90 MB, runs on CPU |
| LLM + Vision-Language Model | `qwen2.5vl:3b` (via Ollama) | ~3.2 GB download, ~4–5 GB VRAM — fits free Colab T4 |
| Optional stronger VLM | `qwen2.5vl:7b` | ~6 GB download, ~8–9 GB VRAM — still fits a T4 (15 GB) |

Change the `MODEL_NAME` variable in the notebook to switch between them. If no GPU is available at
all, Ollama will still run the 3B model on CPU — just noticeably slower per answer.

## 4. Sample input / dataset

Use a small **company annual report / product report / business report** PDF that contains:
- normal paragraph text
- at least one table
- at least one chart, graph, or diagram image

If you don't have one handy, any publicly available company annual report PDF (search "[company
name] annual report filetype:pdf") works well, or you can substitute your own document — a
product spec sheet, a project status report, etc. Upload it inside the notebook (Step 3, `data/
sample_report.pdf`) or drag it directly into the Colab file browser at that path.

## 5. Step-by-step execution order

1. **Setup** — check GPU, install pip packages, install & start Ollama, pull the model.
2. **Upload PDF** — place your report at `data/sample_report.pdf`.
3. **Content extraction** — pull out text (PyMuPDF), tables (pdfplumber), and images (PyMuPDF)
   separately.
4. **Chunking** — split long text into overlapping chunks (tables/images stay whole).
5. **Image captioning** — the local VLM writes a short description of each extracted image/chart.
6. **Embeddings** — embed text chunks, table markdown, and image captions into one shared vector
   space with Sentence-Transformers.
7. **FAISS index** — build one vector store containing everything.
8. **Retriever** — top-k similarity search, type-agnostic.
9. **Multimodal generation** — text/table context goes in as plain text; retrieved images are sent
   to the VLM as actual images (not just captions) for the final answer.
10. **Demo questions** — run the five example questions and inspect which content type was
    retrieved for each.

## 6. Expected output per stage

| Stage | Expected output |
|---|---|
| Text extraction | List of `{page, text}` — one entry per page with visible text |
| Table extraction | List of `{page, markdown}` — each table rendered as a markdown grid |
| Image extraction | PNG/JPEG files saved under `data/extracted_images/`, plus their page numbers |
| Chunking | A few hundred short text chunks (~600 characters each) |
| Captioning | One 1–2 sentence description printed per extracted image |
| Embeddings | A NumPy array of shape `(num_items, 384)` |
| FAISS index | `index.ntotal` equals the total number of embedded items |
| Retrieval | Top-k results printed with type (`text`/`table`/`image`), page, and similarity score |
| Generation | A natural-language answer, plus the list of sources it was grounded in |

## 7. Troubleshooting

See Section 14 inside the notebook — covers Ollama install/start issues, slow model pulls, PDFs
with no extractable tables/images, GPU runtime configuration, and answers that seem to ignore an
image.

## 8. Architecture: traditional RAG vs. multimodal RAG

**Traditional RAG:** `Text → Chunks → Embeddings → Vector Search → LLM → Answer`

**Multimodal RAG (this project):**
```
Text + Tables + Images
        ↓
Content Extraction (type-specific tools)
        ↓
Representation (chunks / table-as-markdown / image captions)
        ↓
One shared embedding space → FAISS
        ↓
Retriever (unchanged from basic RAG)
        ↓
Multimodal context (text + the real retrieved image)
        ↓
Local Vision-Language Model → Answer
```
What changes: extraction (type-specific tools) and generation (a VLM that can accept an actual
image). What stays the same: chunking → embed → FAISS → retrieve — the core RAG skeleton students
already know.

## 9. 30–40 minute teaching flow

| Time | Segment |
|---|---|
| 0–5 min | Recap basic RAG → introduce the multimodal RAG diagram |
| 5–10 min | Setup (pre-run before class if possible to skip download wait time) |
| 10–15 min | Content extraction — show raw text/table/image outputs |
| 15–18 min | Chunking + image captioning — the key "bridge" step |
| 18–23 min | Embeddings + FAISS — point out it's identical to what they already know |
| 23–28 min | Retrieval + multimodal generation function walkthrough |
| 28–35 min | Run all 5 demo questions live, discuss retrieved sources |
| 35–40 min | Recap comparison table + optional improvements + Q&A |

## 10. Optional improvements for advanced students

- Swap the caption-then-embed trick for true joint embeddings (e.g. CLIP).
- Handle complex tables with `camelot-py`, or have the VLM read a rendered table image directly.
- Add a cross-encoder re-ranker on top of FAISS retrieval.
- Route questions to the right retrieval strategy (table-focused vs. image-focused vs. general).
- Extend to video: sample frames with OpenCV, caption each frame the same way images are
  captioned here, and reuse the same embed → FAISS → retrieve → VLM pipeline. Optionally
  transcribe audio locally with Whisper and treat the transcript as another text document.
- Try a larger local model (`qwen2.5vl:7b` or `qwen2.5vl:32b`) for better chart-reading accuracy.

## Why video was left out of the main notebook

Given the 30–40 minute window, video (frame extraction + optional local speech-to-text) was kept
out of the runnable code so the PDF + tables + images demo can be taught thoroughly. Section 10
above sketches exactly how to extend today's pipeline to video as a follow-up exercise — the
retrieval and generation code you build today needs no changes, only a new frame-extraction step.



*************************************** hive llm models api******

U29ApLUt0gpahZmTLXS1Dg==