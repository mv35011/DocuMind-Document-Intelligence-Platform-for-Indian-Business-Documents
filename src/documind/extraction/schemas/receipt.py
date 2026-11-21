from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from documind.extraction.schemas.common import BaseExtractionModel, InvoiceLine


class Receipt(BaseExtractionModel):
    doc_type: Literal["receipt"] = "receipt"
    vendor_name: Optional[str] = None
    address: Optional[str] = None
    date: Optional[date] = None
    line_items: List[InvoiceLine] = []
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
