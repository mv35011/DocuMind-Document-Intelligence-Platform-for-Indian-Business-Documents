import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="reviewer", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded", index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    ocr_json_key: Mapped[Optional[str]] = mapped_column(String(512))
    ocr_engine: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(50), default="model")  # 'model' or 'human'
    model_version: Mapped[Optional[str]] = mapped_column(String(100))
    backend: Mapped[str] = mapped_column(String(50))
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    field_confidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    doc_confidence: Mapped[Optional[float]] = mapped_column(Float)
    rule_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    extraction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("extractions.id"), nullable=False)
    field_path: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="running")
    error: Mapped[Optional[str]] = mapped_column(Text)


class ChatTrace(Base):
    __tablename__ = "chat_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str] = mapped_column(String(50), nullable=False)
    sql: Mapped[Optional[str]] = mapped_column(Text)
    rows_returned: Mapped[Optional[int]] = mapped_column(Integer)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Flattened Query Tables
class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    invoice_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(255))
    supplier_gstin: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    buyer_name: Mapped[Optional[str]] = mapped_column(String(255))
    buyer_gstin: Mapped[Optional[str]] = mapped_column(String(15))
    taxable_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    cgst: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    sgst: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    igst: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    grand_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), index=True)


class InvoiceItemRecord(Base):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    line_no: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[Optional[str]] = mapped_column(Text)
    hsn_sac: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    taxable_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    gst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    line_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))


class BankStatementRecord(Base):
    __tablename__ = "bank_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(255))
    account_holder: Mapped[Optional[str]] = mapped_column(String(255))
    account_last4: Mapped[Optional[str]] = mapped_column(String(4))
    period_start: Mapped[Optional[date]] = mapped_column(Date)
    period_end: Mapped[Optional[date]] = mapped_column(Date)
    opening_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    closing_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))


class BankTxnRecord(Base):
    __tablename__ = "bank_txns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    txn_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    debit: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    credit: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
