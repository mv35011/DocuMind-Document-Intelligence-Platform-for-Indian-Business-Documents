# Architecture Decision Records (ADRs)

### ADR-001: Language and Tooling
- **Context**: Need a fast, reproducible, typed development environment for ML and API pipelines.
- **Options**: Python with uv/poetry/pip; Go; TypeScript.
- **Decision**: Python 3.10+ managed with uv/pip, ruff, mypy, pytest.
- **Trade-off**: Native Python support for all HuggingFace and PyTorch ML workflows; type safety enforced through Pydantic and mypy.

### ADR-002: Web Framework & Data Validation
- **Context**: High-performance typed REST API with automatic OpenAPI documentation.
- **Options**: FastAPI, Django, Flask, Express.
- **Decision**: FastAPI with Pydantic v2.
- **Trade-off**: High throughput, async request handling, strict schema validation and serialization at all boundaries.

### ADR-003: Relational Database & Migrations
- **Context**: Relational business entities requiring multi-tenant workspace isolation.
- **Options**: PostgreSQL 16, MySQL, SQLite, MongoDB.
- **Decision**: PostgreSQL 16 with SQLAlchemy 2.0 (asyncpg) and Alembic migrations.
- **Trade-off**: Native Row-Level Security (RLS) support for zero data leakage, ACID compliance for audit trails.

### ADR-004: Vector Database & Hybrid Retrieval
- **Context**: Document chunk retrieval supporting dense semantics and sparse keyword/symbol matching.
- **Options**: Qdrant, Pinecone, Chroma, pgvector.
- **Decision**: Qdrant with hybrid search (dense BGE + sparse BM25) and Reciprocal Rank Fusion (RRF).
- **Trade-off**: Fast filtering by workspace_id, self-hostable in Docker with low resource footprint.

### ADR-005: Object Storage
- **Context**: Storing original uploaded PDFs, rendered page PNGs, and OCR tokens.
- **Options**: S3 API (AWS S3 prod, MinIO local dev).
- **Decision**: Standard boto3 S3 client with configurable endpoint URL.
- **Trade-off**: Identical API code in local containerized development and AWS cloud deployments.

### ADR-006: Asynchronous Task Processing
- **Context**: Ingest, rendering, OCR, and extraction stages require reliable job queueing.
- **Options**: Celery + Redis, Temporal, Arq, AWS SQS.
- **Decision**: Celery with Redis broker and result backend. Dedicated `default` and `extract` queues.
- **Trade-off**: Battle-tested, supports chained tasks and fine-grained per-queue concurrency limits.

### ADR-007: OCR Engine Abstraction
- **Context**: Extracting text and bounding boxes from noisy scans and digital PDFs.
- **Options**: Tesseract, PaddleOCR, EasyOCR.
- **Decision**: Abstract `OCREngine` protocol. Tesseract for fast CPU dev/CI; PaddleOCR for high-accuracy production.
- **Trade-off**: Modular engine swapping allows quantitative ablation testing across engines.

### ADR-008: Extraction Vision-Language Model
- **Context**: Fine-tuning an open-source vision-language model for layout-aware document extraction.
- **Options**: Qwen2-VL-2B-Instruct, Qwen2.5-VL-3B, Donut, Florence-2.
- **Decision**: `Qwen/Qwen2-VL-2B-Instruct` fine-tuned with 4-bit QLoRA (NF4).
- **Trade-off**: Fits comfortably on free 16GB VRAM GPUs (Kaggle T4) while delivering high Indian layout comprehension.

### ADR-009: Remote LLM & Inference API
- **Context**: Fast zero-shot baseline (B1) and Text-to-SQL agent synthesizer with high token throughput at zero cost.
- **Options**: Groq Cloud (Llama 3.3 70B), OpenAI, Anthropic, Gemini API.
- **Decision**: OpenAI SDK with configurable `base_url`, defaulting to Groq Cloud free tier (`llama-3.3-70b-versatile`).
- **Trade-off**: Extremely fast inference speeds, high free-tier rate limits, no vendor lock-in.

### ADR-010: Agentic Text-to-SQL Guardrails
- **Context**: Enabling natural language queries over extracted business records without risk of SQL injection or data leaks.
- **Options**: Direct LLM-to-DB execution vs AST-based SQL guard (`sqlglot`) + Read-only views.
- **Decision**: `sqlglot` parser restricting queries strictly to single SELECT statements on `v_*` views with mandatory `LIMIT 200` injection and RLS tenant filtering.
- **Trade-off**: Complete prevention of destructive queries (`DROP`, `ALTER`, `UPDATE`, `pg_sleep`) with deterministic AST validation.
