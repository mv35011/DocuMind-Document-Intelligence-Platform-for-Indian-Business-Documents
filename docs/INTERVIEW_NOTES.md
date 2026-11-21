# DocuMind: Technical Interview Preparation & Deep Dives

This document summarizes the top 10 architectural decisions, technical trade-offs, and questions an engineering interviewer is likely to ask during AI/ML system design and fresher/intern interviews.

---

### 1. Why Qwen2-VL-2B instead of Florence-2, Donut, or larger models?
- **Trade-off**:
  - Donut lacks native high-resolution table processing and multi-page context.
  - Florence-2 is strong at bounding box detection, but struggles with multi-currency arithmetic and dense Indian GST invoice structures.
  - 7B/72B models cannot be trained or served on free/low-cost GPUs.
  - `Qwen2-VL-2B` features dynamic visual token resolution (`min_pixels` to `max_pixels`), handles native document layouts, and comfortably fits within a **16 GB VRAM budget (Kaggle T4)** under 4-bit NF4 quantization (~6.8 GB peak memory).

### 2. Why QLoRA (4-bit NF4) over Full Fine-Tuning?
- **Trade-off**:
  - Full fine-tuning of 2.2B parameters requires multi-GPU clusters (A100/H100) and substantial cloud budget.
  - 4-bit NF4 with Double Quantization (`bitsandbytes`) compresses the base model from 4.4 GB to 1.2 GB.
  - LoRA adapters ($r=16, \alpha=32$) placed on all linear language projection layers (`q, k, v, o, gate, up, down`) update only ~18M parameters (0.8% of total).
  - Keeping the vision encoder frozen stabilizes spatial features and prevents catastrophic forgetting of visual tokens.

### 3. Why split datasets by Template rather than Random Train/Test Split?
- **Trade-off**:
  - Random splitting leaks visual layout patterns between train and test sets, artificially inflating F1 scores (models memorize coordinate positions rather than learning semantic associations).
  - By partitioning templates:
    - `train`: Templates T1–T4 (Seeds A)
    - `val`: Templates T1–T4 (Seeds B)
    - `test_seen`: Templates T1–T4 (Seeds C)
    - `test_unseen`: Templates T5–T6 (Never seen during training)
    - `test_real`: Hand-verified real business documents.
  - This measures true generalization to new vendor invoice templates.

### 4. How does the Base-36 GSTIN Checksum work?
- **Trade-off**:
  - Standard regex only catches length and character type errors.
  - Indian GSTINs use a 15-character structure where character 15 is a mathematical check digit computed over characters 1–14 using Base-36 (`0-9A-Z`).
  - Algorithm: Alternate positional multipliers (1 for even, 2 for odd indices), add quotient and remainder of division by 36, and compute $(36 - \text{sum} \pmod{36}) \pmod{36}$.
  - This deterministic check catches OCR transposition errors before sending data downstream.

### 5. Why both Heuristic and Calibrated Confidence Scoring?
- **Trade-off**:
  - Raw model logprobs are often poorly calibrated (models can be 99% confident while hallucinating).
  - Phase 3 uses a deterministic heuristic: $0.6 \times \text{grounding} + 0.4 \times \text{rule\_pass}$.
  - Phase 5 trains a logistic regression with Platt/Isotonic scaling on validation features (token fuzzy match, OCR confidence, rule results) and evaluates Expected Calibration Error (ECE) via reliability diagrams.
  - Auto-approval thresholds are selected on validation curves to guarantee $\ge 98\%$ precision at $\ge 60\%$ coverage.

### 6. Why use `sqlglot` AST validation instead of trusting LLM SQL generation?
- **Trade-off**:
  - Prompt instructions alone cannot guarantee protection against prompt injection embedded inside uploaded invoices (e.g. an invoice vendor named `'; DROP TABLE v_invoices; --`).
  - `sqlglot` parses queries into an Abstract Syntax Tree (AST) for PostgreSQL:
    - Enforces single-statement queries (blocks stacked commands).
    - Restricts commands strictly to `SELECT`.
    - Whitelists table references strictly to read-only views (`v_invoices`, `v_bank_txns`).
    - Prohibits system functions (`pg_sleep`, `pg_read_file`).
    - Injects `LIMIT 200` when omitted to prevent denial of service.

### 7. How is Multi-Tenant Isolation enforced across DB, Vector Store, and Agent?
- **Defense-in-depth architecture**:
  1. **Application Layer**: `workspace_id` is extracted strictly from verified JWT tokens (never trusted from request body or LLM prompts).
  2. **Database Layer**: PostgreSQL Row-Level Security (RLS) is forced on all tenant tables using `SET LOCAL app.workspace_id = '...'`.
  3. **Vector Layer**: All Qdrant hybrid searches include mandatory server-side `Filter(key="workspace_id", match=...)`.
  4. **Agent Layer**: The read-only SQL role can only query pre-filtered views.

### 8. Why Celery + Redis instead of pure async Python?
- **Trade-off**:
  - Document rendering (`pdf2image` / poppler) and OCR (`Tesseract` / `PaddleOCR`) are CPU and memory-intensive C-extensions that block Python's asyncio GIL.
  - Celery provides out-of-process worker concurrency, dedicated worker queues (`default` for fast I/O, `extract` with concurrency 1 for heavy ML), and automatic task retries on failure.

### 9. Why Groq Cloud for Baseline B1 and Text-to-SQL?
- **Trade-off**:
  - Running 70B parameter models locally is impossible on commodity developer hardware.
  - Groq Cloud offers a generous free tier with OpenAI SDK compatibility, delivering inference speeds over 250 tokens/sec.
  - It provides a high-accuracy, zero-cost baseline and zero-latency chat synthesizer without credit card barriers.

### 10. What are the system limitations?
- Single-page receipts and statements are robust; multi-page bank statements currently require page-by-page transaction stitching.
- Multilingual OCR (e.g. Hindi or Tamil invoices) is not in scope for v1.
- Handwritten bills are filtered out at the ingest stage.
