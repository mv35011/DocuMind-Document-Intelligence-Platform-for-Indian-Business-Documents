# DocuMind: Build Specification for the Coding Agent

> Read this whole file before writing any code. Then start at Phase 0 and work through the phases in order.
> Owner: Manmohan (final-year ECE student, NIT Patna). Purpose: a flagship portfolio project for AI/ML internship and fresher roles. It must be real, measured, deployed, and explainable in an interview.

---

## 0. Operating rules for the agent

1. **Work phase by phase.** Do not start a phase until the previous phase's "Done when" checks pass. Commit in small steps using conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
2. **Boring technology first.** Prefer the simplest option that meets the requirement. Do not add a dependency without a one-line reason in `DECISIONS.md`.
3. **Never fabricate numbers.** Every metric in the README, reports, or resume bullets must be produced by a script in `eval/` and saved under `reports/`. If a result is bad, report it honestly. No hardcoded metrics anywhere.
4. **Human gates.** Some steps need a GPU, credentials, hand-labeling, or money. Mark them `[HUMAN]`. When you reach one, write precise step-by-step instructions to `docs/HUMAN_TASKS.md`, make everything else work with a stub or fallback, and continue.
5. **Everything must run on CPU in dev mode.** The coding environment has no GPU. Use the `stub` and `prompted_api` backends for development and CI. GPU work (fine-tuning, vLLM serving) is scripted and smoke-tested on tiny inputs, then run by the human.
6. **Log decisions.** Any time you choose between options, append an entry to `DECISIONS.md` (context, options, choice, trade-off). Update `PROGRESS.md` at the end of every phase.
7. **Verify library APIs against current docs.** Versions move fast (transformers, peft, trl, qdrant-client, langgraph, vllm). Pin exact versions in `uv.lock` after confirming that your calls work. Do not rely on memory of an API.
8. **Quality bar.** Type hints everywhere, Pydantic at every boundary, no global mutable state, dependency injection for OCR/LLM/extractor clients, structured logging (no `print`), tests next to each module, `ruff` and `mypy` clean.
9. **Privacy.** Never commit real documents, real PII, API keys, or datasets. Commit only synthetic data generators, configs, and small fixtures built from synthetic data.
10. **Writing style in docs and README.** Plain, direct sentences. No marketing language, no em dashes.

---

## 1. Product definition

**DocuMind** is a document intelligence platform for Indian business documents. A user uploads PDFs or scans. The system reads them, extracts structured fields with a fine-tuned vision-language model, validates the result with business rules, routes uncertain documents to human review, learns from corrections, and lets users query the extracted data in plain English.

### 1.1 Supported document types (v1)
| Type | Key | Source of data |
|---|---|---|
| GST tax invoice | `gst_invoice` | Synthetic (generated) + small real hand-labeled test set |
| Bank statement | `bank_statement` | Synthetic (generated) + small real hand-labeled test set |
| Retail receipt | `receipt` | Public datasets (SROIE, CORD), mapped to our schema |

### 1.2 Core user flows
1. **Upload** one or many documents (optionally specifying the type; otherwise auto-detect).
2. **Process** asynchronously: preprocess, OCR, extract, normalize, validate, ground, score, route.
3. **Review**: low-confidence or rule-failing documents appear in a review queue. A reviewer sees the page image next to editable fields and approves or corrects.
4. **Learn**: corrections are stored and exported as versioned training data.
5. **Ask**: users query approved data in natural language (text-to-SQL plus RAG over document text) with answers that cite the SQL and the source documents.
6. **Operate**: dashboards show throughput, latency, confidence distribution, auto-approval rate, and drift.

### 1.3 Non-goals for v1
No handwriting recognition, no non-Indian tax regimes, no multilingual (Hindi) OCR, no email ingestion, no billing, no mobile app. Do not build these.

### 1.4 Success targets (aspirational; report actuals even if lower)
- JSON schema validity of final extraction: at least 99% (after constrained decoding and one repair retry).
- Fine-tuned model beats the prompted-LLM baseline on field-level micro F1 on the unseen-template test and the real test set.
- Auto-approve precision at least 98% at a coverage of at least 60% on the synthetic validation set.
- Text-to-SQL execution accuracy at least 80% on the 50-question eval set.
- Zero cross-workspace data leakage across all API, agent, and vector-search paths (tested).

---

## 2. Architecture decisions (summary)

| Concern | Decision | Why | Fallback or note |
|---|---|---|---|
| Language and tooling | Python 3.11, `uv`, `ruff`, `mypy`, `pytest` | Fast, reproducible, standard | none |
| API | FastAPI + Pydantic v2 | Typed, async, matches owner's stack | none |
| ORM and migrations | SQLAlchemy 2.0 + Alembic | Standard, explicit migrations | none |
| Primary DB | PostgreSQL 16 | Relational data, Row-Level Security, SQL for the agent | RDS is a config change only |
| Vector store | Qdrant (dense + sparse BM25, RRF fusion) | Hybrid search, owner knows it | verify the current `query_points` fusion API |
| Object storage | S3 API; MinIO locally, S3 on AWS (`boto3`, endpoint override) | Same code in dev and prod | none |
| Async work | Celery + Redis, separate `extract` queue | Simple, proven. Kafka is overkill here | Arq is acceptable if Celery blocks progress |
| OCR | `OCREngine` protocol: `tesseract` (CI, baseline) and `paddleocr` (default for quality) | Compare engines in eval | `rapidocr-onnxruntime` if PaddleOCR install is painful |
| Extraction model | `Qwen/Qwen2-VL-2B-Instruct`, QLoRA fine-tuned, config-driven | Small enough to train on a free T4/L4 and serve cheaply | `Qwen/Qwen2.5-VL-3B-Instruct` if memory allows. Last resort: Donut |
| LLM access | `openai` SDK with configurable `base_url` | Works with OpenAI, Gemini's OpenAI-compatible endpoint, Groq, Together, vLLM, Ollama. No LiteLLM needed | none |
| Serving the VLM | vLLM OpenAI-compatible server (GPU, optional). `local_hf` backend for small runs | Same client code for hosted and self-hosted | `prompted_api` when no GPU is available |
| Agent | LangGraph state machine | Explicit, testable control flow | none |
| Review UI | Streamlit (v1) | Fast to build, ML-friendly | React is a stretch goal only |
| Experiment tracking and registry | MLflow (tracking + registry with alias `champion`) | Standard | none |
| Data versioning | DVC with S3/MinIO remote | Reproducible datasets and splits | none |
| Monitoring | Prometheus + Grafana + Evidently (scheduled drift report) | Standard stack | OpenTelemetry is a stretch goal |
| CI/CD | GitHub Actions, GHCR images, deploy to a single EC2 host with docker compose | Cheap and simple | Terraform is a stretch goal |
| Auth | JWT (access token), roles `admin`, `reviewer`, `viewer`, scoped to a workspace | Enough for RBAC story | no OAuth in v1 |

Write each of these into `DECISIONS.md` as ADR-lite entries during Phase 0.

---

## 3. System design

### 3.1 Component diagram

```
                +-------------------+
 Browser  --->  |  Streamlit UI     |  (upload, review queue, chat, dashboard)
                +---------+---------+
                          |
                +---------v---------+       +------------------+
                |   FastAPI (api)   | <---> |  PostgreSQL      |  (RLS by workspace)
                +----+---------+----+       +------------------+
                     |         |
        enqueue job  |         | chat
                     v         v
              +------+--+   +--+--------------+      +---------+
              |  Redis  |   | LangGraph agent | ---> | Qdrant  |
              +----+----+   +--+--------------+      +---------+
                   |           |  read-only SQL role
        +----------v-----+     v
        | Celery workers |   PostgreSQL (views v_*)
        |  default queue |
        |  extract queue |---> VLM backend (stub | prompted_api | local_hf | vllm)
        +----------+-----+
                   |
          +--------v--------+        +-----------------+
          |  MinIO / S3     |        | MLflow + DVC    |
          | (docs, pages)   |        | (models, data)  |
          +-----------------+        +-----------------+
   Prometheus scrapes api + workers; Grafana dashboards; Evidently daily drift job.
```

### 3.2 Processing pipeline (Celery chain, each stage idempotent with retries and time limits)

```
ingest_validate -> render_pages -> preprocess -> ocr -> classify(optional) -> extract
  -> parse_repair -> normalize -> validate_rules -> ground_fields -> score_confidence
  -> route(auto_approve | needs_review) -> persist -> index_vectors (after approval)
```

Every stage writes a row to `pipeline_runs` with `stage`, `started_at`, `duration_ms`, `status`, `error`. These feed the latency dashboards.

**Stage details**

1. **ingest_validate**: check MIME by content sniffing (not extension), max 20 MB, max 20 pages, reject encrypted PDFs. Store the original in object storage under `{workspace_id}/{document_id}/original`. Never trust filenames.
2. **render_pages**: PDF to images with `pdf2image` (poppler) at 200 DPI, with a timeout. Images pass through as-is. Store pages as PNG.
3. **preprocess** (OpenCV): grayscale for OCR only (keep the color image for the VLM), deskew (Hough or minAreaRect), denoise, contrast normalization (CLAHE). Each step is optional per config and its effect is measured in the ablation (Phase 2).
4. **ocr**: run the configured `OCREngine`. Output a list of `{text, bbox, confidence}` plus the page's full text. Persist to the DB and object storage. OCR text serves three purposes: baseline B1 input, grounding check, and RAG indexing.
5. **classify**: if the user gave `doc_type`, skip. Otherwise ask the VLM (or API model) for one label from the fixed set with an `unknown` option. Low classifier confidence routes to review.
6. **extract**: call the `Extractor` for the doc type (see 3.3). For bank statements, run per page: page 1 returns header and transactions, later pages return transactions only, then merge.
7. **parse_repair**: parse into the Pydantic schema. On failure, one repair retry that sends the invalid output and the validation error back to the model. If it still fails, mark `needs_review` with `failure_reason='invalid_json'`.
8. **normalize**: Indian number grouping (`1,23,456.50`), currency symbols, `Decimal` money, dates to ISO 8601 (accept `dd/mm/yyyy`, `dd-mm-yy`, `12 Mar 2025`), GSTIN and PAN uppercase and trimmed, whitespace collapsed.
9. **validate_rules**: see section 5.
10. **ground_fields**: for each non-null leaf value, find the best fuzzy match in the OCR tokens (`rapidfuzz`) and store `{score, bbox, page}` as evidence. A value with no OCR support is a likely hallucination and is flagged.
11. **score_confidence**: see section 6.
12. **route**: `auto_approved` only if all hard rules pass and document confidence is at least the calibrated threshold. Otherwise `needs_review`.
13. **index_vectors**: when a document becomes `approved` or `auto_approved`, chunk the OCR text, embed, and upsert into Qdrant with `workspace_id`, `document_id`, `page`, `doc_type` in the payload. Also flatten the extraction into the query tables (section 4.2).

### 3.3 Extractor abstraction

```python
class Extractor(Protocol):
    name: str
    def extract(self, pages: list[PageImage], ocr: list[OCRPage] | None,
                doc_type: DocType) -> RawExtraction: ...
```

Implementations, selected by `EXTRACTOR_BACKEND`:

| Backend | Purpose |
|---|---|
| `stub` | Returns canned or ground-truth JSON from a fixture. Used in unit tests, integration tests, and CI. No network |
| `regex` | **Baseline B0**: rules and regex over OCR text. Weak by design |
| `ocr_llm` | **Baseline B1**: OCR text, then a prompted LLM (via the `openai` SDK) with JSON-schema output |
| `vlm_prompted` | Prompted VLM without fine-tuning (zero-shot reference point) |
| `vlm_finetuned` | **Model M1**: the QLoRA-tuned Qwen2-VL, served via vLLM or `local_hf` |

All backends return the same `RawExtraction` so the evaluation harness compares them directly.

**Output contract**: the model must output a single JSON object matching the doc-type schema, with `null` for any field not present on the page. Never guess. This null-discipline is part of the training data and the prompt. Use constrained decoding (vLLM guided JSON via the Pydantic-derived JSON schema) when the backend supports it; keep the repair retry as the safety net.

---

## 4. Data model

### 4.1 Pydantic extraction schemas (`src/documind/extraction/schemas/`)

Rules: money is `Decimal`, dates are `date`, every field is `Optional` except `doc_type`, and each model sets `extra="forbid"`.

```python
class Party(BaseModel):
    name: str | None
    gstin: str | None
    pan: str | None
    address: str | None
    state_code: str | None        # 2-digit GST state code

class InvoiceLine(BaseModel):
    description: str | None
    hsn_sac: str | None
    quantity: Decimal | None
    unit: str | None
    unit_price: Decimal | None
    discount: Decimal | None
    taxable_value: Decimal | None
    gst_rate: Decimal | None       # total rate in percent
    line_total: Decimal | None

class GSTInvoice(BaseModel):
    doc_type: Literal["gst_invoice"]
    invoice_number: str | None
    invoice_date: date | None
    due_date: date | None
    supplier: Party
    buyer: Party
    place_of_supply: str | None
    line_items: list[InvoiceLine]
    taxable_total: Decimal | None
    cgst: Decimal | None
    sgst: Decimal | None
    igst: Decimal | None
    cess: Decimal | None
    round_off: Decimal | None
    grand_total: Decimal | None
    currency: str | None           # default "INR" if the symbol is present

class BankTxn(BaseModel):
    date: date | None
    description: str | None
    ref_no: str | None
    debit: Decimal | None
    credit: Decimal | None
    balance: Decimal | None

class BankStatement(BaseModel):
    doc_type: Literal["bank_statement"]
    bank_name: str | None
    account_holder: str | None
    account_number_last4: str | None   # never store the full number
    ifsc: str | None
    period_start: date | None
    period_end: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    transactions: list[BankTxn]

class Receipt(BaseModel):
    doc_type: Literal["receipt"]
    vendor_name: str | None
    address: str | None
    date: date | None
    line_items: list[InvoiceLine]      # reuse, most fields null
    subtotal: Decimal | None
    tax: Decimal | None
    total: Decimal | None
```

Mapping from SROIE (company, date, address, total) and CORD (menu, sub_total, total) into `Receipt` lives in `datagen/public_datasets/`. Document the mapping and the license of each dataset in `docs/DATA.md`. Verify licenses before using or redistributing anything. Do not commit raw public datasets.

### 4.2 PostgreSQL tables (Alembic migrations)

Core tables (all carry `workspace_id uuid not null`, `created_at`, `updated_at`):

```
workspaces(id, name)
users(id, email unique, password_hash, role, workspace_id)
documents(id, workspace_id, filename, mime, size_bytes, doc_type, status, storage_key,
          page_count, uploaded_by, failure_reason)
document_pages(id, document_id, page_no, image_key, ocr_json_key, ocr_engine)
extractions(id, document_id, version int, source text check in ('model','human'),
            model_version, backend, payload jsonb, field_confidence jsonb,
            evidence jsonb, doc_confidence real, rule_results jsonb, is_current bool)
corrections(id, document_id, extraction_id, field_path, old_value, new_value, user_id)
pipeline_runs(id, document_id, stage, started_at, duration_ms, status, error)
chat_traces(id, workspace_id, user_id, question, route, sql, rows_returned,
            answer, tool_calls jsonb, latency_ms, tokens_in, tokens_out)
```

Document `status` values: `uploaded`, `processing`, `needs_review`, `auto_approved`, `approved`, `rejected`, `failed`.

Flattened query tables (populated only from approved or auto-approved current extractions, rebuilt idempotently per document):

```
invoices(document_id, workspace_id, invoice_number, invoice_date, supplier_name, supplier_gstin,
         buyer_name, buyer_gstin, taxable_total, cgst, sgst, igst, grand_total)
invoice_items(document_id, workspace_id, line_no, description, hsn_sac, quantity, unit_price,
              taxable_value, gst_rate, line_total)
bank_statements(document_id, workspace_id, bank_name, account_holder, account_last4,
                period_start, period_end, opening_balance, closing_balance)
bank_txns(document_id, workspace_id, txn_date, description, debit, credit, balance)
```

Agent-facing read-only views: `v_invoices`, `v_invoice_items`, `v_bank_txns`, `v_bank_statements` (these expose only the flattened tables, never `users`, `extractions`, or raw payloads).

### 4.3 Multi-tenancy and RBAC (defense in depth)

1. **Application layer**: every repository method takes `workspace_id` from the authenticated principal, never from the request body or the LLM.
2. **Database layer**: Row-Level Security on every table with `workspace_id`. Set `SET LOCAL app.workspace_id = '<uuid>'` at the start of each request or task transaction.
   ```sql
   ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
   ALTER TABLE documents FORCE ROW LEVEL SECURITY;
   CREATE POLICY ws_isolation ON documents
     USING (workspace_id = current_setting('app.workspace_id', true)::uuid);
   ```
   Use two DB roles that are not table owners: `documind_app` (read/write) and `documind_readonly` (SELECT on `v_*` views only, used by the agent). The owner and superuser roles are used only by Alembic.
3. **Vector layer**: every Qdrant query includes a server-side `workspace_id` filter. The filter is never produced by the LLM.
4. **Roles**: `viewer` can read approved data and chat; `reviewer` can also review, correct, and approve; `admin` can also manage users and export training data.
5. **Tests are mandatory**: a user in workspace A must get 404 or empty results for workspace B across every endpoint, the agent, and vector search.

---

## 5. Validation engine (`src/documind/validation/`)

Each rule returns `{rule_id, severity: hard|soft, passed, message, fields}`. Hard failures block auto-approval. Soft failures lower confidence.

**GST invoice rules**
- `gstin_format` (hard): regex `^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$`.
- `gstin_checksum` (hard): base-36 check digit. Algorithm: charset `0-9A-Z`; for each of the first 14 characters take its index `v`; multiply by 1 for even positions and 2 for odd positions (0-based); `p = v*factor`; add `p // 36 + p % 36` to a running sum; expected check char is `charset[(36 - sum % 36) % 36]`. Unit test against several publicly known valid GSTINs and generated ones.
- `gstin_state_matches` (soft): first two digits are a valid state code and agree with `state_code` and `place_of_supply` when present.
- `tax_type_consistent` (hard): if supplier state equals place of supply then CGST and SGST are present and equal and IGST is null or zero. Otherwise only IGST.
- `gst_rate_allowed` (soft): rate belongs to the set in `configs/gst_rates.yaml`. Default set `{0, 0.25, 3, 5, 12, 18, 28, 40}` so that historical and current invoices both pass. This is configuration because slabs change; do not hardcode.
- `line_math` (soft): `quantity * unit_price - discount` is within tolerance of `taxable_value`.
- `totals_reconcile` (hard): sum of line taxable values equals `taxable_total` within 1.00 INR; `taxable_total + cgst + sgst + igst + cess + round_off` equals `grand_total` within 1.00 INR.
- `dates_sane` (soft): invoice date not in the future and not before 2017-07-01 (GST start); due date is not before invoice date.
- `required_fields` (hard): invoice number, date, supplier name, grand total.

**Bank statement rules**
- `running_balance` (hard): for each consecutive pair, `balance_i == balance_{i-1} + credit_i - debit_i` within 0.01. Report the first failing row.
- `period_reconcile` (hard): `opening + sum(credit) - sum(debit) == closing` within 0.01.
- `dates_in_period` and `dates_monotonic` (soft).
- `single_sided_txn` (soft): a transaction has either debit or credit, not both.

**Receipt rules**: `total_ge_subtotal` (soft), `items_sum_matches_subtotal` (soft), `date_sane` (soft).

The validation engine must be pure Python with no I/O, and heavily unit-tested.

---

## 6. Grounding and confidence

**Grounding score** per field: best `rapidfuzz` partial-ratio between the normalized value and OCR tokens or token n-grams on the page, scaled to 0 to 1. Numbers are compared after normalization. Store the matched bbox as evidence; the review UI draws it on the page.

**Confidence v1 (heuristic, Phase 3)**: `field_conf = 0.6*grounding + 0.4*rule_ok`, where `rule_ok` is 1 if every rule touching the field passes. `doc_conf = min` over required fields.

**Confidence v2 (calibrated, Phase 5)**: train a logistic regression (scikit-learn) on the validation set to predict "field is correct" from features: grounding score, OCR confidence of matched tokens, rule flags, field type, and (when the backend returns logprobs) mean token logprob of the value. Calibrate with isotonic or Platt scaling. Report reliability diagram and Expected Calibration Error. Choose the auto-approve threshold on the validation set to hit the target precision, then evaluate it once on the test sets. Save the calibrator as an MLflow artifact next to the model.

---

## 7. Data strategy

### 7.1 Synthetic generator (`datagen/`)
- Reproducible by seed. Every document is emitted with a ground-truth JSON label and a `manifest.jsonl` row: `{id, doc_type, template_id, split, seed, augment_params, image_path, label_path}`.
- Content: `Faker('en_IN')` for names and addresses; valid GSTINs generated with the real checksum; PAN-like strings; HSN/SAC code list; realistic item catalogs (electronics, textiles, FMCG, services); Indian number formatting; CGST+SGST vs IGST chosen by the state logic; occasional discounts, round-off, and cess. Bank statements generate coherent running balances and realistic narration strings (UPI, NEFT, IMPS, ATM, cheque, interest).
- Rendering: Jinja2 HTML templates to PDF with WeasyPrint, then PDF to PNG. At least **6 invoice templates** and **4 bank statement templates** with different layouts, fonts, table styles, logo placement, and header positions.
- Augmentation (`albumentations`/OpenCV), applied at 3 levels (`clean`, `mild`, `harsh`): rotation and skew, perspective warp, Gaussian and salt-and-pepper noise, blur, JPEG compression, uneven lighting and shadow, stamp or signature overlays, partial crop margins.
- Scale to start: 1,500 documents, then grow to 4,000+ if training results justify it.

### 7.2 Splits (prevent leakage)
Split **by template**, not randomly:
- `train`: templates T1 to T4 (per type), seeds set A.
- `val`: the same templates, seeds set B.
- `test_seen`: the same templates, seeds set C.
- `test_unseen`: templates T5 and T6, never used in training or validation. This measures generalization to new layouts.
- `test_real`: **[HUMAN]** at least 100 real documents (public sample invoices and statements the owner is allowed to use, with all PII redacted or replaced). Hand-verified labels. Never used for training or threshold tuning except where stated in section 6.

Report all four test slices separately. The honest gap between synthetic and real is a feature of the write-up, not something to hide.

### 7.3 Gold labeling for `test_real` (`eval/tools/`)
Provide `prefill_gold.py` (runs the best API model to pre-fill JSON) and `validate_gold.py` (schema check plus rule check plus a diff view). The human verifies **every field** by hand. Document that prefilled labels can bias the evaluation toward the prefill model and that the verification step mitigates this.

### 7.4 Training data builder (`training/build_dataset.py`)
Chat-format JSONL: each example has the page image path(s), a system prompt, a user instruction containing the doc type and the schema hint, and the assistant target as **compact JSON with canonical key order and `null` for absent fields**. Include some examples with absent fields on purpose (null-discipline). Build from synthetic train data, the SROIE/CORD train splits, and exported human corrections (flywheel). Version with DVC.

---

## 8. Model training (`training/`)

- Base: `Qwen/Qwen2-VL-2B-Instruct` (config-driven; do not hardcode).
- Method: QLoRA (4-bit NF4 via bitsandbytes) with `peft` and `trl` (or a plain custom training loop if `trl`'s VLM support is awkward; log the choice).
- Starting hyperparameters (tune on validation): LoRA `r=16`, `alpha=32`, `dropout=0.05`, target all linear layers of the language model (keep the vision tower frozen); learning rate `1e-4` to `2e-4`, cosine schedule, warmup 3%; 2 to 3 epochs; batch size 1 with gradient accumulation 16; gradient checkpointing on; `sdpa` attention (no flash-attn on a T4); `bf16` if the GPU supports it, otherwise `fp16`.
- Image tokens: control with `min_pixels` / `max_pixels` in the processor config. Start near `max_pixels = 1024*28*28`. Text-heavy documents need resolution, so measure the accuracy-versus-memory trade-off and log it.
- Train on completions only (mask the prompt tokens in the loss).
- Evaluate on the validation set each epoch with the real extraction metrics (not just loss). Keep the best checkpoint.
- Track everything in MLflow: params, loss, val metrics, git SHA, DVC data version, adapter artifact, and the calibrator when it exists.
- Export: save the LoRA adapter; provide `merge_and_export.py` to merge it for vLLM (or serve with vLLM LoRA support; pick the working option and record it).
- **[HUMAN]** The real training run happens on a free or cheap GPU (Kaggle T4, Colab, or a rented L4/A10). Provide a ready-to-run `training/notebooks/train_kaggle.ipynb` plus a plain `train_qlora.py` CLI. The agent must smoke-test the script end to end on 8 examples with a tiny config (CPU or a dry-run flag) so that the human run does not fail on trivial bugs.

---

## 9. Evaluation harness (`eval/`)

The harness is built **before** any model work and is used for every comparison.

### 9.1 Extraction metrics
- **Normalization before comparison**: strings casefolded, punctuation and whitespace collapsed; money via `Decimal` within 0.01; dates compared as ISO; GSTIN and PAN exact.
- **Field-level scoring**: for each leaf field, pred non-null and equal to gold is TP; pred non-null and different from gold is FP and FN; pred null with gold non-null is FN; pred non-null with gold null is FP; both null is ignored. Report micro and macro F1, plus per-field F1.
- **Line items and transactions**: match predicted rows to gold rows with the Hungarian algorithm on a similarity of (description, amount). Report item-level precision, recall, F1, and per-attribute accuracy on matched rows.
- **Document exact match**: percent of documents with every field correct.
- **Reliability**: JSON-valid rate, schema-valid rate, repair-retry rate, hallucination rate (values with no OCR support).
- **Rule pass rate** on predictions, and the auto-approve metrics (coverage and precision at the chosen threshold).
- **Slices**: by `doc_type`, `template_id`, split (`test_seen`, `test_unseen`, `test_real`), and augmentation level.
- **Efficiency**: latency per page (p50, p95), tokens per page, cost per 1,000 pages (API) or GPU seconds per page (self-hosted).

### 9.2 Models compared (the main results table)
| ID | System |
|---|---|
| B0 | OCR + regex and rules |
| B1 | OCR + prompted LLM |
| V0 | Prompted VLM, no fine-tuning |
| M1 | QLoRA fine-tuned Qwen2-VL |
| M1-q | M1 quantized or served at lower precision (accuracy drop versus speed gain) |

### 9.3 Ablations (each as one script and one table)
OCR engine (tesseract vs paddleocr), preprocessing on/off, image resolution (`max_pixels`), constrained decoding on/off, training set size (500 / 1,500 / 4,000), with and without correction data from the flywheel.

### 9.4 Text-to-SQL and agent evaluation (`eval/datasets/agent_eval.jsonl`)
50 questions over a seeded synthetic database: about 30 SQL aggregations and filters, 10 RAG lookups, 5 mixed, 5 adversarial (cross-workspace requests, prompt injection inside a document, destructive SQL requests). Each question has a gold SQL and a gold answer, or an expected refusal. Metrics: execution accuracy (result-set equality, order-insensitive), numeric answer correctness, refusal correctness, average tool calls, latency, and tokens.

### 9.5 Output
`make eval-extraction MODEL=<id>` writes `reports/<run_id>/{metrics.json, report.md, plots/}` and logs to MLflow. `eval/make_readme_table.py` renders the README results section from the latest reports. Nothing else may write numbers into the README.

---

## 10. Agent (`src/documind/agent/`)

LangGraph state machine with a hard step limit:

```
route -> (sql_branch | rag_branch | both | refuse)
sql_branch: sql_generate -> sql_guard -> sql_execute -> (retry <= 2 on error) -> synthesize
rag_branch: hybrid_search -> synthesize
```

**Rules**
- **Router** classifies the question into `sql`, `rag`, `both`, or `out_of_scope`.
- **sql_generate** gets the view DDL with column descriptions and a few static few-shot examples. It outputs a single `SELECT`.
- **sql_guard** (`sqlglot`): parse as PostgreSQL; allow exactly one statement; `SELECT` only; relations limited to the `v_*` views; reject functions such as `pg_sleep` and `pg_read_file`; inject `LIMIT 200` when absent. Anything else is rejected before execution.
- **sql_execute**: runs as `documind_readonly` with `SET LOCAL app.workspace_id`, `statement_timeout = 5s`, and read-only transaction. The workspace comes from the authenticated user, never from the model.
- **Arithmetic is done in SQL, not by the LLM.** The synthesizer receives the result rows and writes a short answer.
- **Transparency**: the final response includes the executed SQL, the row count, and cited document IDs.
- **RAG**: hybrid dense (`BAAI/bge-small-en-v1.5` via `fastembed`) plus sparse BM25 with RRF fusion in Qdrant, always filtered by `workspace_id`. Chunk about 300 tokens with overlap. A reranker is a stretch goal.
- **Prompt-injection hygiene**: text from documents is passed to the model as quoted data in a clearly delimited block, never as instructions. The agent has no write tools. Include injection cases in the adversarial eval set and unit tests.
- Persist every conversation turn to `chat_traces` for the eval and debugging.
- Stream answers to the UI over SSE.

---

## 11. API (`src/documind/api/`)

| Method and path | Role | Purpose |
|---|---|---|
| `POST /auth/login` | public | Returns a JWT |
| `POST /documents` | reviewer+ | Multipart upload, optional `doc_type`, returns `document_id` and enqueues the job |
| `GET /documents` | viewer+ | List with filters (status, type, date), cursor pagination |
| `GET /documents/{id}` | viewer+ | Metadata, status, page URLs (short-lived presigned) |
| `GET /documents/{id}/extraction` | viewer+ | Current extraction with confidences, rule results, evidence boxes |
| `PATCH /documents/{id}/extraction` | reviewer+ | Apply corrections; writes `corrections` and a new human version |
| `POST /documents/{id}/approve` | reviewer+ | Approve; triggers flatten and indexing |
| `POST /documents/{id}/reject` | reviewer+ | Reject with reason |
| `GET /review/queue` | reviewer+ | Documents in `needs_review`, ordered by lowest confidence first |
| `POST /chat` | viewer+ | Agent question, SSE stream |
| `GET /analytics/summary` | viewer+ | Counts, auto-approve rate, spend totals by month and vendor |
| `POST /admin/export-training-data` | admin | Builds a versioned JSONL from corrections |
| `GET /healthz`, `GET /readyz`, `GET /metrics` | internal | Liveness, readiness (DB, Redis, Qdrant, S3), Prometheus |

Conventions: OpenAPI docs enabled, request IDs propagated through logs and Celery tasks, consistent error envelope, rate limiting on `/auth/login` and `/chat`, CORS restricted by config.

---

## 12. Data flywheel

1. Reviewer corrections are stored per field in `corrections`.
2. `POST /admin/export-training-data` (and `make export-corrections`) converts approved human versions into training JSONL with the same format as 7.4 and records the dataset hash.
3. DVC versions the new dataset; the training script produces a **candidate** model.
4. `make compare-candidate` runs the frozen test sets for candidate versus current champion. Promotion to MLflow alias `champion` is allowed only if the candidate does not regress on any slice by more than the configured tolerance and improves the primary metric.
5. Report auto-approval rate and F1 across at least two flywheel rounds (a simulated second round using held-back synthetic corrections is acceptable, and must be labeled as simulated).

---

## 13. MLOps, observability, security

### 13.1 Docker and compose
Services: `api`, `worker-default`, `worker-extract` (concurrency 1), `beat`, `ui`, `postgres`, `redis`, `minio`, `qdrant`, `mlflow`, `prometheus`, `grafana`. Profile `gpu` adds `vllm`. One multi-stage Dockerfile for the Python services, small images, non-root user, healthchecks on all services. `make up` starts the full dev stack on CPU with the stub or API backend.

### 13.2 CI/CD (GitHub Actions)
- `ci.yml` on every PR: `ruff`, `mypy`, unit tests, integration tests against compose services (stub extractor, 5 synthetic documents end to end), coverage report.
- `eval-smoke.yml` on PRs that touch `extraction/`, `validation/`, or `eval/`: run the extraction eval on a 30-document synthetic fixture and fail on regression greater than 2 points versus the stored baseline file.
- `build.yml` on main: build and push images to GHCR with the git SHA tag.
- `deploy.yml` on tag or manual dispatch: SSH to the EC2 host, pull images, `docker compose up -d`, poll `/readyz`, and roll back to the previous tag on failure. Secrets only from GitHub Secrets.

### 13.3 Monitoring
- Prometheus metrics: pages processed, documents by status, stage latency histograms, extraction errors, confidence histogram, auto-approve rate, review queue size, LLM tokens and cost, chat latency.
- Provide Grafana dashboard JSON files in `mlops/grafana/` (pipeline health, model quality proxies, business view).
- Evidently daily job (Celery beat): drift on confidence distribution, null-rate per field, and OCR confidence versus the training reference. Store the HTML report and expose an alert metric.
- Structured JSON logs with `request_id`, `document_id`, `workspace_id`. Mask account numbers and GSTIN-like strings in logs.

### 13.4 Security checklist
File-type sniffing and size/page limits; subprocess timeouts for poppler and OCR; presigned URLs with short expiry; passwords hashed with argon2 or bcrypt; JWT with short expiry; secrets only from env; dependency scanning (`pip-audit`) in CI; account numbers stored as last 4 digits only; encryption at rest on S3 (SSE); no raw document content in logs.

### 13.5 Serving benchmark (`eval/bench_serving.py`)
Load-test the extraction path with `locust` or an async script: concurrency 1, 4, 8, 16; record throughput (pages per minute), latency p50 and p95, error rate, and (for GPU runs) GPU memory and utilization. Compare backends: API model, `local_hf`, vLLM. **[HUMAN]** runs the GPU variants and commits the resulting `reports/` files.

### 13.6 Deployment on AWS (cost-aware)
One EC2 host (for example a `t3.large` or `t3.xlarge`) runs compose with Caddy or Nginx for TLS. Documents go to an S3 bucket. The GPU is **not** kept running 24/7: an optional `g4dn.xlarge` spot instance runs vLLM only for benchmarks and live demos, with `scripts/gpu_up.sh` and `scripts/gpu_down.sh`. The always-on demo uses the `prompted_api` backend or precomputed examples, clearly labeled in the UI. RDS is a documented option (change `DATABASE_URL`). Estimate monthly cost in `docs/COSTS.md`.

---

## 14. Repository layout

```
documind/
├── README.md                # results table is generated; see eval/make_readme_table.py
├── DECISIONS.md             # ADR-lite log
├── PROGRESS.md              # phase checklist
├── pyproject.toml           # uv, ruff, mypy, pytest config
├── Makefile
├── docker-compose.yml
├── docker-compose.gpu.yml
├── .env.example
├── configs/                 # app config, gst_rates.yaml, model and training configs
├── docs/                    # DATA.md, COSTS.md, HUMAN_TASKS.md, ARCHITECTURE.md
├── src/documind/
│   ├── api/                 # main.py, deps.py, routers/, schemas/
│   ├── core/                # config.py, logging.py, security.py, metrics.py
│   ├── db/                  # models.py, session.py, repositories/, alembic/
│   ├── ingest/              # validate.py, render.py, preprocess.py
│   ├── ocr/                 # base.py, tesseract.py, paddle.py
│   ├── extraction/          # base.py, schemas/, backends/, prompts.py, parse_repair.py, normalize.py
│   ├── validation/          # rules/, gstin.py, reconcile.py, engine.py
│   ├── grounding/           # match.py
│   ├── confidence/          # heuristic.py, calibrate.py
│   ├── indexing/            # embed.py, qdrant_store.py
│   ├── agent/               # graph.py, tools/, sql_guard.py, prompts.py
│   ├── workers/             # celery_app.py, tasks.py
│   └── flywheel/            # export.py
├── ui/                      # Streamlit app: upload, review, chat, dashboard
├── datagen/                 # templates/, generators/, augment.py, public_datasets/, cli.py
├── training/                # build_dataset.py, train_qlora.py, merge_and_export.py, notebooks/
├── eval/                    # metrics.py, run_extraction_eval.py, run_agent_eval.py, bench_serving.py, tools/
├── mlops/                   # grafana/, prometheus/, evidently_job.py
├── scripts/                 # gpu_up.sh, gpu_down.sh, seed_demo_data.py
├── tests/                   # unit/, integration/, e2e/
└── .github/workflows/
```

### 14.1 Required `make` targets
`make up`, `make down`, `make migrate`, `make seed`, `make datagen`, `make test`, `make lint`, `make eval-extraction MODEL=...`, `make eval-agent`, `make train-smoke`, `make export-corrections`, `make compare-candidate`, `make bench`, `make demo`.

### 14.2 Key environment variables (`.env.example`)
`DATABASE_URL`, `REDIS_URL`, `S3_ENDPOINT_URL`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `QDRANT_URL`, `MLFLOW_TRACKING_URI`, `JWT_SECRET`, `EXTRACTOR_BACKEND` (`stub|regex|ocr_llm|vlm_prompted|vlm_finetuned`), `OCR_ENGINE`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `VLM_BASE_URL`, `VLM_MODEL`, `AUTO_APPROVE_THRESHOLD`, `MAX_UPLOAD_MB`, `MAX_PAGES`.

---

## 15. Testing strategy

**Unit (fast, no network)**: GSTIN checksum and format; Indian number and date normalization; every validation rule with passing and failing cases; `parse_repair`; metric functions (hand-computed expected values); `sql_guard` against adversarial inputs (`DROP`, stacked statements, comments hiding statements, `pg_sleep`, selecting from `users`, cross-schema access); grounding matcher; confidence calibrator on toy data.

**Integration (compose services, stub extractor)**: upload to approved flow on 5 synthetic documents; correction creates a new version and a `corrections` row; approval populates flattened tables and Qdrant; idempotent re-run of a failed stage.

**Security and isolation**: two workspaces with seeded data. Assert no cross-workspace access via REST, via `/chat` (including a prompt asking for another workspace's data), via direct SQL under the read-only role, and via vector search.

**E2E**: one script that starts the stack, uploads a document, waits for processing, asks a question through `/chat`, and checks the answer.

**Property tests** (`hypothesis`) for normalizers and for the synthetic bank statement generator (balances always reconcile).

---

## 16. Phases and "Done when" criteria

### Phase 0: Scaffold
Repo layout, `pyproject.toml`, ruff and mypy config, CI skeleton, compose with Postgres, Redis, MinIO, Qdrant, MLflow, health endpoints, Alembic baseline, `DECISIONS.md` filled with section 2.
**Done when**: `make up` brings up all services healthy; `make test` and `make lint` pass in CI.

### Phase 1: Core logic (pure Python)
Pydantic schemas, normalizers, GSTIN utilities, full validation engine, `parse_repair`, and the extraction metric functions.
**Done when**: unit tests pass with at least 90% coverage on these modules, and metrics are verified against hand-computed examples.

### Phase 2: Data and baselines
Synthetic generator for all three types, splits by template, public dataset mappers, evaluation harness, baselines B0 and B1, preprocessing and OCR-engine ablations, first report. **[HUMAN]** assembles and labels `test_real` (at least 100 docs); the agent supplies the tools and a checklist.
**Done when**: `make datagen` and `make eval-extraction MODEL=B1` produce a complete `reports/` run with slice breakdowns; generated bank statements always reconcile.

### Phase 3: End-to-end pipeline
Ingest, rendering, preprocessing, OCR abstraction, Celery chain, DB persistence, API upload and status endpoints, object storage, heuristic confidence and routing, `prompted_api` backend.
**Done when**: uploading a synthetic invoice through the API yields a persisted extraction with confidences, rule results, and a correct routing decision; the integration test passes in CI.

### Phase 4: Fine-tuning
Dataset builder, training script, MLflow logging, merge/export, `vlm_finetuned` backend, smoke tests. **[HUMAN]** runs the training and serving on GPU following `docs/HUMAN_TASKS.md`.
**Done when**: `make train-smoke` passes on CPU or dry-run; after the human run, `make eval-extraction MODEL=M1` produces a report comparing M1 to B1 and V0 on all slices.

### Phase 5: Review, grounding, flywheel
Grounding and evidence boxes, calibrated confidence and threshold selection, Streamlit review UI with correction flow, corrections export, candidate-versus-champion comparison.
**Done when**: a reviewer can correct and approve a document in the UI; the export produces a valid training JSONL; calibration plots and ECE appear in a report.

### Phase 6: Query agent
Flattening on approval, Qdrant indexing, RLS and roles, `sql_guard`, LangGraph agent, chat endpoint, chat UI, agent eval set and runner, isolation tests.
**Done when**: `make eval-agent` produces metrics; all isolation and `sql_guard` tests pass; injection cases are handled.

### Phase 7: Production readiness
Metrics, Grafana dashboards, Evidently job, CI/CD workflows, deploy script with rollback, serving benchmark, AWS deployment docs and cost notes. **[HUMAN]** provides AWS access and runs GPU benchmarks.
**Done when**: a tagged release deploys to the EC2 host through Actions; dashboards show live metrics; benchmark reports exist for at least two backends.

### Phase 8: Polish
README with architecture diagram, generated results tables, a "Known limitations" section, a 2-minute demo video script, a 90-second architecture walkthrough, seeded demo data, and `docs/INTERVIEW_NOTES.md` listing the top 10 design decisions with trade-offs and the questions an interviewer is likely to ask.
**Done when**: a new reader can run `make demo` and reach a working UI with seeded data in under 10 minutes.

### Stretch (only after Phase 8)
Layout detection stage (pretrained document layout detector) with a table-region crop experiment; LayoutLMv3 baseline (B2) on SROIE/CORD; ONNX export or INT8 quantization of the OCR stack; reranker for RAG; React review UI; Terraform for the AWS setup; publish the adapter and a model card on Hugging Face (trained only on synthetic and license-compatible public data); OpenTelemetry tracing.

---

## 17. Known risks and how to handle them

| Risk | Mitigation |
|---|---|
| Fine-tuned model overfits synthetic templates | Template-level splits, `test_unseen`, real test set, and strong augmentation. Report the gap |
| Free GPU runs out of memory or time | Small `max_pixels`, 4-bit, gradient checkpointing, batch size 1; fallback to Qwen2.5-VL-3B only if memory allows, otherwise reduce data size, never silently cut evaluation |
| PaddleOCR installation problems | OCR protocol with Tesseract and RapidOCR fallbacks; the eval compares engines anyway |
| Hallucinated values | Null-discipline in training, constrained decoding, grounding check, hard validation rules |
| Real-data scarcity and PII | Small hand-labeled real set with redaction; documented in `docs/DATA.md`; nothing real is committed |
| LLM API cost or rate limits | Cache responses by content hash in dev, limit eval concurrency, keep the `stub` backend for CI |
| Scope creep | Phases are ordered by value. Phases 1 to 4 plus the harness already form a strong project. Do not start stretch items early |

---

## 18. Final deliverables checklist

- [ ] Running stack via `make up`, seeded demo via `make demo`
- [ ] Generated `reports/` for B0, B1, V0, M1 on all slices, plus ablations
- [ ] Calibration report with ECE and the chosen threshold
- [ ] Agent eval report and isolation tests passing
- [ ] Serving benchmark reports for at least two backends
- [ ] CI green, tagged release deployed, Grafana dashboards screenshotted into `docs/`
- [ ] README with generated results, architecture diagram, honest limitations
- [ ] `DECISIONS.md`, `docs/INTERVIEW_NOTES.md`, `docs/COSTS.md`, `docs/DATA.md` complete
- [ ] Resume bullets drafted in `docs/RESUME_BULLETS.md`, using only numbers copied from `reports/`
