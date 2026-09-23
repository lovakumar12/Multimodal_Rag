# Multimodal RAG Pipeline: Ingestion, Retrieval & Grounded Generation

## 1. Traditional RAG vs. Multimodal RAG

| Capability | Traditional RAG | OmniRAG Platform |
|---|---|---|
| **Input Content** | Plain text only | Text, headings, structured tables, original diagrams, charts, figures, and page previews |
| **Table Understanding** | Flattened text or lost | Preserved as structured JSON headers/rows + Markdown grid + semantic embedding |
| **Visual Artifacts** | Discarded or hallucinated | Extracted in original resolution, captioned via Vision AI, indexed, and returned alongside answers |
| **Chunking Strategy** | Blind character splitting | Structure-aware chunking respecting headings, sections, tables, and image associations |
| **Retrieval Scope** | Text similarity only | Hybrid retrieval (text + tables + image descriptions + relationship graph expansion) |
| **Image Relevance** | None | Multi-signal scoring combining visual description, nearby text, captions, and page co-occurrence |
| **Citations** | Vague document title | Document name, exact page/slide number, content type, and interactive page viewer |

---

## 2. Ingestion & Extraction Pipeline

```
Uploaded Document (PDF / PPTX / DOCX / Image)
  │
  ├── [1. Format Extractor]
  │     ├── PDF: PyMuPDF (blocks, fonts, images) + pdfplumber (table cells/grids)
  │     ├── PPTX: python-pptx (slides, titles, shapes, notes, tables, pictures)
  │     ├── DOCX: python-docx (paragraphs, headings H1-H3, tables, inline images)
  │     └── Images: PIL dimensions, format + OCR text extraction
  │
  ├── [2. Vision Describer (Ingestion Time)]
  │     └── Diagram / Chart / Figure -> Multimodal Vision Model (Gemini / OpenAI)
  │         -> Generates semantic summary of components, flow, metrics & caption
  │
  ├── [3. Relationship Builder]
  │     └── Constructs Document -> Page -> Section -> ContentBlocks hierarchy
  │
  ├── [4. Structure-Aware Chunker]
  │     └── Respects headings, prepends section breadcrumbs, tags co-located visual IDs
  │
  └── [5. Multimodal Embedding & Vector Indexing]
        ├── Text Chunks -> SentenceTransformers / Gemini / OpenAI embeddings
        ├── Structured Tables -> Table markdown + summary embeddings
        └── Visual Assets -> Semantic description + caption + OCR embeddings
```

---

## 3. Structure-Aware Chunking Strategy

Rather than splitting raw text into arbitrary 500-character windows that fracture sentences and divorce figures from their context, the platform implements **Structure-Aware Chunking**:

1. **Heading Preservation**: Text chunks inherit active section breadcrumbs:
   ```text
   [System Architecture > Encoder-Decoder Pipeline]
   The transformer encoder processes the input sequence into continuous representations...
   ```
2. **Table Intactness**: Tables are extracted as whole structured units, preventing header severance across chunks.
3. **Multimodal Association**: When an image or table is detected on a page, its unique asset ID is directly embedded into the metadata of all surrounding text chunks on that page.

---

## 4. Multi-Signal Image Relevance Scoring

To prevent returning decorative logos or irrelevant background images, candidate visuals are evaluated using a multi-signal scoring model:

$$\text{ImageScore} = w_1 \cdot S_{\text{desc}} + w_2 \cdot S_{\text{text}} + w_3 \cdot S_{\text{caption}} + w_4 \cdot S_{\text{page}} + w_5 \cdot S_{\text{co\_occurrence}}$$

Where:
- $S_{\text{desc}}$: Cosine similarity between query vector and image semantic description embedding ($w_1 = 0.35$).
- $S_{\text{text}}$: Similarity between query and surrounding text context ($w_2 = 0.25$).
- $S_{\text{caption}}$: Lexical and semantic match with the figure caption ($w_3 = 0.20$).
- $S_{\text{page}}$: Binary or continuous relevance of the parent page ($w_4 = 0.10$).
- $S_{\text{co\_occurrence}}$: Boost ($1.0$) if the visual artifact was co-located with a top-1 retrieved text chunk ($w_5 = 0.10$).

Visuals scoring below `IMAGE_RELEVANCE_THRESHOLD` (default 0.40) are filtered out, ensuring only semantically pertinent figures appear in the response.

---

## 5. Grounded LLM Generation

The synthesis engine constructs a rigorously demarcated prompt:

```text
### TEXT EVIDENCE:
[1] Source Document: 'Attention_Paper.pdf', Page 3
Content: [Encoder Architecture] The encoder is composed of a stack of N = 6 identical layers...

### STRUCTURED TABLES:
[1] Table from 'Attention_Paper.pdf', Page 9 (Caption: Table 1: Model Variations):
| Model | d_model | heads | BLEU |
|---|---|---|---|
| Base | 512 | 8 | 27.3 |

### VISUAL ARTIFACTS (DIAGRAMS, CHARTS, FIGURES):
[1] DIAGRAM from 'Attention_Paper.pdf', Page 3 (Caption: Figure 1: The Transformer Architecture):
Description: Diagram showing Multi-Head Attention and Feed Forward blocks with residual connections.
```

The LLM is governed by strict system constraints:
- Must only answer from provided evidence.
- Must cite original document names and page numbers: `[Document.pdf, Page 3]`.
- Must refer to figures and tables naturally (e.g., *"As illustrated in the architecture diagram on Page 3..."*).
