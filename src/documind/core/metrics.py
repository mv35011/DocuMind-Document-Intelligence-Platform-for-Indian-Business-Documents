from prometheus_client import Counter, Gauge, Histogram

# Pipeline Latency & Volume
DOCUMENTS_PROCESSED_TOTAL = Counter(
    "documind_documents_processed_total",
    "Total documents processed by status and document type",
    ["status", "doc_type", "workspace_id"],
)

STAGE_DURATION_SECONDS = Histogram(
    "documind_stage_duration_seconds",
    "Duration of individual pipeline stages",
    ["stage"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

REVIEW_QUEUE_SIZE = Gauge(
    "documind_review_queue_size",
    "Current number of documents waiting in human review queue",
    ["workspace_id"],
)

# LLM & Agent Observability
LLM_TOKENS_TOTAL = Counter(
    "documind_llm_tokens_total",
    "Total LLM tokens consumed",
    ["direction", "model", "operation"],
)

CHAT_LATENCY_SECONDS = Histogram(
    "documind_chat_latency_seconds",
    "End-to-end response time for agent queries",
    ["route"],
    buckets=[0.2, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0],
)
