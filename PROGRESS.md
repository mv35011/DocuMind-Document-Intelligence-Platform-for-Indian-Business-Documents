# DocuMind Implementation Progress

## Phase Checklist

- [x] **Phase 0: Scaffold & Configuration**
  - [x] Repository layout & directory structure
  - [x] `pyproject.toml` with pinned dependencies
  - [x] Makefile with all required build and test targets
  - [x] Environment configuration (`.env.example`, `configs/app.yaml`, `configs/gst_rates.yaml`)
  - [x] Architecture Decision Records (`DECISIONS.md`)

- [x] **Phase 1: Core Logic & Validation Engine**
  - [x] Pydantic v2 extraction schemas (`GSTInvoice`, `BankStatement`, `Receipt`)
  - [x] Normalization helpers (Indian currency numbers, dates, GSTIN/PAN casing)
  - [x] Pure-Python GSTIN checksum & formatting verification (Base-36 check digit)
  - [x] Business validation rules engine (GST reconciliation, running balance, math sanity)
  - [x] Extraction repair loop (`parse_repair.py`)
  - [x] Comprehensive unit tests for GSTIN, normalizers, and business rules

- [ ] **Phase 2: Data Generation & Evaluation Baselines**
  - [ ] Synthetic invoice and bank statement generator with WeasyPrint & Jinja2
  - [ ] Albumentations image degradations (mild, harsh, clean)
  - [ ] Metric computation (Field micro/macro F1, Hungarian line-item matching, exact match)
  - [ ] Evaluation harness runner (`eval/run_extraction_eval.py`)
  - [ ] Baseline implementations (B0 regex, B1 Groq/OCR-LLM)

- [ ] **Phase 3: Asynchronous Pipeline & REST API**
  - [ ] Celery pipeline tasks (ingest -> render -> preprocess -> OCR -> extract -> ground -> route)
  - [ ] FastAPI backend with multi-tenant auth and document lifecycle endpoints
  - [ ] PostgreSQL SQLAlchemy 2.0 schema and migrations

- [ ] **Phase 4: QLoRA Fine-Tuning for Qwen2-VL**
  - [ ] Training dataset builder (`training/build_dataset.py`)
  - [ ] QLoRA 4-bit fine-tuning script (`training/train_qlora.py`) with CPU smoke-test
  - [ ] Ready-to-run Kaggle T4 notebook (`training/notebooks/train_kaggle.ipynb`)
  - [ ] RunPod vLLM serving notebook & guide (`training/notebooks/train_runpod.ipynb`)

- [ ] **Phase 5: Grounding, Calibrated Confidence & Human Review**
  - [ ] RapidFuzz token-level grounding evidence extraction
  - [ ] Calibrated confidence scorer & reliability diagram
  - [ ] Streamlit review interface (`ui/app.py`)

- [ ] **Phase 6: Multi-Tenant Agent (Text-to-SQL & RAG)**
  - [ ] `sqlglot` AST security guard (`sql_guard.py`)
  - [ ] LangGraph agent state machine for hybrid SQL/RAG answers
  - [ ] Adversarial evaluation dataset (50 benchmark queries)

- [ ] **Phase 7 & 8: Production Readiness, Resume Bullets & Demo**
  - [ ] Prometheus metrics and Grafana dashboard JSON
  - [ ] Step-by-step human guide (`docs/HUMAN_TASKS.md`)
  - [ ] Resume bullet points (`docs/RESUME_BULLETS.md`) and interview notes (`docs/INTERVIEW_NOTES.md`)
