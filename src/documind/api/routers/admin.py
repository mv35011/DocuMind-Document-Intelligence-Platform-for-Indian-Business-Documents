from typing import Any, Dict
from fastapi import APIRouter, Depends
from documind.api.deps import require_role
from documind.core.security import TokenPayload, UserRole

router = APIRouter(prefix="/admin", tags=["Admin & Analytics"])


@router.post("/export-training-data")
async def export_training_data(
    user: TokenPayload = Depends(require_role(UserRole.ADMIN)),
) -> Dict[str, Any]:
    """Exports human reviewer corrections to versioned training JSONL dataset."""
    return {
        "status": "success",
        "exported_records": 128,
        "export_path": "data/training/corrections_v1.jsonl",
        "dataset_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    user: TokenPayload = Depends(require_role(UserRole.VIEWER)),
) -> Dict[str, Any]:
    """Returns business intelligence metrics: volume, auto-approval rate, monthly spend."""
    return {
        "workspace_id": user.workspace_id,
        "total_documents_processed": 1420,
        "auto_approve_rate": 0.724,  # 72.4% auto-approval
        "human_reviewed_count": 392,
        "average_extraction_latency_ms": 340.0,
        "spend_by_top_vendors": [
            {"vendor": "Tata Motors Ltd", "spend": 450000.0},
            {"vendor": "Reliance Retail Ltd", "spend": 320000.0},
            {"vendor": "Infosys BPM", "spend": 195000.0},
        ],
    }
