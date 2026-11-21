# Human Operator Tasks Guide

This document lists the specific tasks requiring manual execution, GPU access, or external API keys, along with exact commands and verification criteria.

---

## 1. Remote LLM Setup (Groq Cloud - Free Tier)

**Purpose**: Powers baseline B1 (`ocr_llm`) and the LangGraph SQL/RAG agent at zero cost with high throughput.

### Instructions:
1. Go to [console.groq.com](https://console.groq.com) and create a free account.
2. Navigate to **API Keys** and generate a new key (starts with `gsk_`).
3. Add the key to your `.env` file in the project root:
   ```env
   LLM_BASE_URL=https://api.groq.com/openai/v1
   LLM_API_KEY=gsk_your_actual_key_here
   LLM_MODEL=llama-3.3-70b-versatile
   ```
4. Verify by running the extraction benchmark on B1:
   ```bash
   make eval-extraction MODEL=ocr_llm
   ```

---

## 2. Model Fine-Tuning on Kaggle (Free T4 GPU - $0 Cost)

**Purpose**: Train **Model M1** (`Qwen/Qwen2-VL-2B-Instruct` with 4-bit QLoRA) on Indian business document layouts.

### Instructions:
1. Open [kaggle.com](https://www.kaggle.com) and create a new Notebook.
2. In the right panel under **Settings**:
   - Set **Accelerator** to **GPU T4 x2** or **GPU T4**.
   - Set **Internet** to **On**.
3. Upload or copy the code from `training/notebooks/train_kaggle.ipynb`.
4. Run all cells in sequence:
   - Cell 1 installs `transformers`, `peft`, `bitsandbytes`, `accelerate`.
   - Cell 3 loads `Qwen/Qwen2-VL-2B-Instruct` under 4-bit NF4 quantization (~6.8 GB VRAM).
   - Cell 4 freezes the vision tower and attaches LoRA adapters to language linear projections.
   - Cell 5 trains for 3 epochs with gradient accumulation 16 and learning rate `2e-4`.
5. Download the zipped adapter `documind_qwen2_vl_adapter.zip` at the end of the notebook.
6. Extract the adapter into your local `models/adapter/` directory.

---

## 3. High-Concurrency Serving on RunPod (L4 / A10G Spot)

**Purpose**: High-throughput vLLM serving and running the concurrency load benchmark (`bench_serving.py`).

### Instructions:
1. Log into your RunPod account.
2. Deploy a **Spot Pod**:
   - GPU: 1x **NVIDIA L4** ($0.29/hr) or **A10G** ($0.44/hr).
   - Template: **RunPod PyTorch** or **vLLM Official**.
3. In the Web Terminal, launch the vLLM OpenAI-compatible server:
   ```bash
   python -m vllm.entrypoints.openai.api_server \
       --model Qwen/Qwen2-VL-2B-Instruct \
       --port 8000 \
       --dtype half \
       --max-model-len 4096 \
       --enable-lora \
       --lora-modules documind-qwen2-vl=./models/adapter
   ```
4. Run the benchmark:
   ```bash
   python3 -m eval.bench_serving --endpoint http://localhost:8000/v1 --concurrencies 1,4,8,16
   ```
5. **Stop the pod immediately** after the run using `scripts/gpu_down.sh` or through the RunPod dashboard to avoid ongoing charges. Expected total cost: **< $0.50**.

---

## 4. Real Document Gold Labeling (`test_real`)

**Purpose**: Verify generalization on 100+ real, unredacted Indian invoices and bank statements.

### Instructions:
1. Gather sample PDFs into `data/test_real/`. Redact any personal PAN or full account numbers.
2. Pre-fill initial extraction labels:
   ```bash
   python3 -m eval.tools.prefill_gold --input-dir data/test_real/ --output-dir data/test_real/labels/
   ```
3. Hand-verify and edit each field against the image using the review interface.
4. Validate schema and business rules compliance:
   ```bash
   python3 -m eval.tools.validate_gold --labels-dir data/test_real/labels/
   ```
