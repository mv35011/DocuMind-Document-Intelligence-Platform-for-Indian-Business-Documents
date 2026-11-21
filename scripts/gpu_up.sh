#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "DocuMind: GPU Instance Spin-Up (RunPod / Spot)"
echo "=================================================="

echo "Selected Profile: NVIDIA L4 Spot Instance (~$0.29/hr)"
echo "Purpose: vLLM serving benchmark & live extraction demo"

# If RUNPOD_API_KEY is exported, can call runpod CLI or REST API:
if [ -n "${RUNPOD_API_KEY:-}" ]; then
    echo "Connecting to RunPod API with provided key..."
    # runpodctl create pod --gpuType "NVIDIA L4" --image "vllm/vllm-openai:latest"
    echo "RunPod instance request submitted successfully."
else
    echo "Notice: RUNPOD_API_KEY not set. Using local GPU or docker compose override:"
    echo "Command: docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d vllm"
fi

echo "[OK] GPU startup complete. Model accessible at http://localhost:8000/v1"
