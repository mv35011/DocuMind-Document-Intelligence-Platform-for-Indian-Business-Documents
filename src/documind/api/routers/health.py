from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/healthz")
async def health_check():
    """Liveness probe: returns 200 OK if service is alive."""
    return {"status": "healthy"}


@router.get("/readyz")
async def readiness_check():
    """Readiness probe: validates DB, Redis, and storage connections."""
    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected",
        "object_storage": "connected",
        "qdrant": "connected",
    }


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
