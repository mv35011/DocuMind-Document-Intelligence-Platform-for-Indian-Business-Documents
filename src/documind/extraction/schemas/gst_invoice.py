from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from documind.extraction.schemas.common import BaseExtractionModel, InvoiceLine, Party


class GSTInvoice(BaseExtractionModel):
    doc_type: Literal["gst_invoice"] = "gst_invoice"
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    supplier: Optional[Party] = None
    buyer: Optional[Party] = None
    place_of_supply: Optional[str] = None
    line_items: List[InvoiceLine] = []
    taxable_total: Optional[Decimal] = None
    cgst: Optional[Decimal] = None
    sgst: Optional[Decimal] = None
    igst: Optional[Decimal] = None
    cess: Optional[Decimal] = None
    round_off: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None
    currency: Optional[str] = "INR"
