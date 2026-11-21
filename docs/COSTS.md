# Cost & GPU Hardware Strategy (ROI Analysis)

This document details the cost architecture and hardware choices for training, serving, and agent execution in DocuMind.

---

## 1. Executive Summary: Maximum ROI Architecture

| Component | Selected Platform | Cost per Unit | Total Project Cost | Reason |
|---|---|---|---|---|
| **QLoRA Fine-Tuning** | **Kaggle T4 GPU** (16 GB) | **$0.00** / hr | **$0.00** | Fits comfortably under 4-bit NF4 (~6.8 GB VRAM); free 30 hrs/week |
| **API Baseline & Synthesizer** | **Groq Cloud** (Llama-3.3 70B) | **$0.00** (Free Tier) | **$0.00** | 30 requests/min, 14.4k req/day free, ultra-fast 250+ tokens/sec |
| **Serving Load Benchmark** | **RunPod L4 Spot** | **$0.29** / hr | **~$0.60** (2 hours) | vLLM throughput testing at concurrency 1, 4, 8, 16 |
| **Local Development** | CPU / Docker Compose | **$0.00** | **$0.00** | Fully runnable without GPU via `stub` backend |
| **Total Cloud GPU Spend** | | | **< $1.00** | Maximum reach, zero waste |

---

## 2. Why Kaggle T4 for QLoRA?

- `Qwen/Qwen2-VL-2B-Instruct` has 2.2 billion parameters.
- In 16-bit float (`fp16`), weights alone take 4.4 GB + activations/gradients = 14 GB VRAM.
- In 4-bit NormalFloat (`NF4`) quantization via `bitsandbytes`, base weights occupy just **1.2 GB**.
- LoRA adapters ($r=16, \alpha=32$) on attention and MLP linear projections add only **~18 MB** of trainable parameters (0.8% of base model).
- Peak training memory with batch size 1 and gradient checkpointing is **~6.8 GB**, leaving over 9 GB headroom on a single Kaggle 16 GB T4 GPU.
- Result: **Zero cloud cost** for model training.

---

## 3. Why Groq Cloud for Baseline B1 and Agent?

- Groq provides an OpenAI-compatible API (`https://api.groq.com/openai/v1`) powered by custom LPU hardware.
- Fast execution (~250-300 tokens/sec), eliminating latency bottlenecks in SQL generation and RAG synthesis.
- Free tier includes generous token quotas per minute and day.
- Allows the project to be 100% evaluated and demoed on live LLMs without requiring an OpenAI credit card.

---

## 4. Why RunPod Spot for vLLM Serving Benchmarks?

- vLLM achieves up to 4x higher serving throughput than standard HuggingFace pipelines through PagedAttention.
- A single NVIDIA L4 (Ada Lovelace, 24 GB VRAM) spot instance on RunPod costs **$0.29/hour**.
- Running a 2-hour benchmark suite at concurrency 1, 4, 8, and 16 costs **less than $0.60**.
- Scripts `scripts/gpu_up.sh` and `scripts/gpu_down.sh` prevent accidental idle charges.
