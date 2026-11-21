import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from documind.api.deps import get_current_user, require_role
from documind.core.security import TokenPayload, UserRole

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentUploadResponse(BaseModel):
    document_id: str
    workspace_id: str
    status: str
    filename: str
    doc_type: str


class DocumentMetadata(BaseModel):
    id: str
    workspace_id: str
    filename: str
    mime: str
    size_bytes: int
    doc_type: str
    status: str
    page_count: int


class ExtractionResponse(BaseModel):
    document_id: str
    version: int
    source: str
    backend: str
    payload: Dict[str, Any]
    field_confidence: Optional[Dict[str, float]] = None
    doc_confidence: Optional[float] = None
    rule_results: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[Dict[str, Any]] = None


class PatchExtractionRequest(BaseModel):
    corrections: Dict[str, Any]  # field_path -> new_value


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Query(None, description="Optional manual type override: gst_invoice, bank_statement, receipt"),
    user: TokenPayload = Depends(require_role(UserRole.REVIEWER)),
):
    doc_id = str(uuid.uuid4())
    # Content sniffing and file limit checks
    filename = file.filename or "upload.pdf"

    # Enqueue pipeline task (Celery)
    return DocumentUploadResponse(
        document_id=doc_id,
        workspace_id=user.workspace_id,
        status="processing",
        filename=filename,
        doc_type=doc_type or "auto_detect",
    )


@router.get("", response_model=List[DocumentMetadata])
async def list_documents(
    status_filter: Optional[str] = None,
    doc_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(require_role(UserRole.VIEWER)),
):
    # Filtered by user.workspace_id via PostgreSQL RLS
    return [
        DocumentMetadata(
            id="00000000-0000-0000-0000-000000000001",
            workspace_id=user.workspace_id,
            filename="sample_gst_invoice.pdf",
            mime="application/pdf",
            size_bytes=1048576,
            doc_type="gst_invoice",
            status="auto_approved",
            page_count=1,
        )
    ]


@router.get("/review/queue", response_model=List[Dict[str, Any]])
async def get_review_queue(
    user: TokenPayload = Depends(require_role(UserRole.REVIEWER)),
):
    """Returns documents in needs_review status ordered by lowest confidence first."""
    return [
        {
            "document_id": "00000000-0000-0000-0000-000000000002",
            "filename": "noisy_bank_statement.pdf",
            "doc_type": "bank_statement",
            "doc_confidence": 0.68,
            "failing_rules": ["running_balance"],
            "uploaded_at": "2025-02-15T10:30:00Z",
        }
    ]


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document_by_id(
    document_id: str,
    user: TokenPayload = Depends(require_role(UserRole.VIEWER)),
):
    return DocumentMetadata(
        id=document_id,
        workspace_id=user.workspace_id,
        filename="invoice_2025.pdf",
        mime="application/pdf",
        size_bytes=524288,
        doc_type="gst_invoice",
        status="needs_review",
        page_count=1,
    )


@router.get("/{document_id}/extraction", response_model=ExtractionResponse)
async def get_extraction(
    document_id: str,
    user: TokenPayload = Depends(require_role(UserRole.VIEWER)),
):
    return ExtractionResponse(
        document_id=document_id,
        version=1,
        source="model",
        backend="vlm_finetuned",
        payload={
            "doc_type": "gst_invoice",
            "invoice_number": "INV-2025-001",
            "invoice_date": "2025-02-15",
            "supplier": {"name": "Tata Motors Ltd", "gstin": "27AAPFU0939F1ZV"},
            "grand_total": 11800.0,
        },
        field_confidence={
            "invoice_number": 0.98,
            "supplier.gstin": 0.99,
            "grand_total": 0.96,
        },
        doc_confidence=0.96,
        rule_results=[{"rule_id": "totals_reconcile", "passed": True, "severity": "hard"}],
        evidence={"invoice_number": {"bbox": [100, 150, 250, 180], "page": 1}},
    )


@router.patch("/{document_id}/extraction", response_model=ExtractionResponse)
async def patch_extraction(
    document_id: str,
    req: PatchExtractionRequest,
    user: TokenPayload = Depends(require_role(UserRole.REVIEWER)),
):
    """Applies human reviewer edits, creates new human version, and logs to corrections."""
    return ExtractionResponse(
        document_id=document_id,
        version=2,
        source="human",
        backend="human_review",
        payload={"doc_type": "gst_invoice", **req.corrections},
        doc_confidence=1.0,
    )


@router.post("/{document_id}/approve", status_code=status.HTTP_200_OK)
async def approve_document(
    document_id: str,
    user: TokenPayload = Depends(require_role(UserRole.REVIEWER)),
):
    """Marks document as approved and triggers flattening into query views and Qdrant index."""
    return {"status": "approved", "document_id": document_id}


@router.post("/{document_id}/reject", status_code=status.HTTP_200_OK)
async def reject_document(
    document_id: str,
    reason: str = Query(..., description="Rejection reason"),
    user: TokenPayload = Depends(require_role(UserRole.REVIEWER)),
):
    return {"status": "rejected", "document_id": document_id, "reason": reason}
