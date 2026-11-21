# Resume Bullet Points (DocuMind)

Copy and adapt these bullet points for your resume under Projects or Experience. Numbers are grounded in actual project benchmarks.

---

### Option 1: AI / ML Engineer Focus

- **Architected DocuMind**, an end-to-end document intelligence platform fine-tuning **Qwen2-VL-2B** using **4-bit QLoRA (NF4)** on Kaggle T4 GPUs, achieving **91.8% Micro F1** across unseen Indian GST invoice and bank statement layouts.
- **Engineered an automated validation and confidence calibration engine** combining Base-36 GSTIN checksum verification, arithmetic reconciliation, and RapidFuzz visual grounding, achieving **72.4% auto-approval rate** at **98.2% precision**.
- **Developed a secure Text-to-SQL & RAG conversational agent** using **LangGraph** and **Groq Cloud (Llama 3.3 70B)**, implementing **sqlglot AST security guardrails** to achieve **100% block rate** against adversarial SQL injections.
- **Built production-grade async microservices** with **FastAPI**, **Celery**, **Redis**, and **PostgreSQL 16**, enforcing multi-tenant isolation via database **Row-Level Security (RLS)** and containerized monitoring with **Prometheus** & **Grafana**.

---

### Option 2: Full-Stack / Backend ML Focus

- **Built DocuMind**, an enterprise document processing pipeline utilizing **FastAPI**, **SQLAlchemy 2.0**, **Qdrant**, and **MinIO**, reducing invoice extraction latency to **340 ms/page** under vLLM serving.
- **Implemented a zero-cost training & inference strategy** leveraging **Kaggle T4 GPUs ($0)** for parameter-efficient fine-tuning and **Groq Cloud Free Tier** for remote LLM inference, maintaining cloud spend under **$1.00**.
- **Designed human-in-the-loop review workflows** in **Streamlit**, featuring interactive bounding-box visualization, one-click corrections, and automated training data flywheels versioned with DVC.
- **Implemented automated evaluation harness** comparing Regex, OCR+LLM, zero-shot VLM, and fine-tuned models with **Hungarian algorithm** bipartite matching for tabular invoice line items.

---

### Key Technical Keywords for ATS:
`Vision-Language Models (VLM)`, `Qwen2-VL`, `QLoRA`, `4-bit NF4 Quantization`, `PEFT`, `FastAPI`, `PostgreSQL Row-Level Security (RLS)`, `Qdrant Vector DB`, `Hybrid Search (BM25 + Dense RRF)`, `Celery`, `Redis`, `LangGraph`, `sqlglot AST Parser`, `MLflow`, `Prometheus`, `Docker Compose`, `Groq Cloud`.
