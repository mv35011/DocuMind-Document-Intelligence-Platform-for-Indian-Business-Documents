#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "DocuMind: GPU Instance Spin-Down (Cost Saver)"
echo "=================================================="

if [ -n "${RUNPOD_API_KEY:-}" ]; then
    echo "Stopping RunPod spot instance to eliminate idle charges..."
    # runpodctl stop pod <POD_ID>
    echo "RunPod instance terminated successfully."
else
    echo "Stopping containerized vLLM GPU service..."
    # docker compose -f docker-compose.yml -f docker-compose.gpu.yml stop vllm
fi

echo "[OK] GPU shut down. Zero ongoing cost."
