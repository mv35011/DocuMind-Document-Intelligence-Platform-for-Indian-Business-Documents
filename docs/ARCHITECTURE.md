# DocuMind Architecture Specification

DocuMind is an enterprise document intelligence and financial retrieval system built for Indian business documents.

---

## 1. System Component Diagram

```
                +-------------------+
 Browser  --->  |  Streamlit UI     |  (Upload, Human Review Queue, Agent Chat, Dashboard)
                +---------+---------+
                          |
                +---------v---------+       +------------------+
                |   FastAPI (api)   | <---> |  PostgreSQL 16   |  (Row-Level Security by Workspace)
                +----+---------+----+       +------------------+
                     |         |
        enqueue job  |         | chat query
                     v         v
              +------+--+   +--+--------------+      +---------+
              |  Redis  |   | LangGraph Agent | ---> | Qdrant  |  (Hybrid BM25 + Dense RRF)
              +----+----+   +--+--------------+      +---------+
                   |           |  Read-only SQL Role
        +----------v-----+     v
        | Celery Workers |   PostgreSQL Views (v_*)
        |  default queue |
        |  extract queue |---> VLM Backend (stub | ocr_llm | vlm_finetuned via vLLM)
        +----------+-----+
                   |
          +--------v--------+        +-----------------+
          |  MinIO / AWS S3 |        | MLflow Tracking |
          | (docs, pages)   |        | (models, runs)  |
          +-----------------+        +-----------------+
```

---

## 2. Processing Pipeline Flow

Each stage is an idempotent Celery task:

```
ingest_validate
  -> render_pages (200 DPI PNG)
  -> preprocess (OpenCV deskew, denoise, CLAHE)
  -> ocr (Tesseract / PaddleOCR tokens & bounding boxes)
  -> classify (Vision Classifier)
  -> extract (Qwen2-VL-2B QLoRA / Groq LLM)
  -> parse_repair (1-shot JSON schema retry)
  -> normalize (Indian numbering, ISO dates, GSTIN casing)
  -> validate_rules (GSTIN Base-36 checksum, tax consistency, running balance)
  -> ground_fields (RapidFuzz OCR token alignment & bbox evidence)
  -> score_confidence (Calibrated logistic regression)
  -> route (auto_approved if score >= threshold and hard rules pass, else needs_review)
  -> persist (extractions table)
  -> index_vectors (Qdrant hybrid vector index after approval)
```

---

## 3. Defense-in-Depth Security

1. **JWT & RBAC**: Scoped strictly to `workspace_id` with roles `viewer`, `reviewer`, `admin`.
2. **PostgreSQL RLS**: `ALTER TABLE documents FORCE ROW LEVEL SECURITY` with `SET LOCAL app.workspace_id`.
3. **Qdrant Vector Isolation**: Server-side filter on `workspace_id` injected into all hybrid queries.
4. **AST SQL Guard**: `sqlglot` parser restricting queries strictly to single `SELECT` on `v_*` views.
