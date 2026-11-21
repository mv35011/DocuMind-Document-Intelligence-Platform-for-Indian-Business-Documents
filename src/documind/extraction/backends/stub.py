import time
from typing import Any, Dict, List, Optional
from documind.extraction.base import DocType, OCRPage, PageImage, RawExtraction


class StubExtractor:
    name = "stub"

    def __init__(self, canned_data: Optional[Dict[str, Any]] = None):
        self.canned_data = canned_data or {
            "gst_invoice": {
                "doc_type": "gst_invoice",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2025-02-15",
                "supplier": {
                    "name": "Tata Motors Ltd",
                    "gstin": "27AAPFU0939F1ZV",
                    "state_code": "27",
                    "pan": "AAPFU0939F",
                },
                "buyer": {
                    "name": "Reliance Retail Ltd",
                    "gstin": "27AABCR1234F1Z5",
                    "state_code": "27",
                },
                "place_of_supply": "27",
                "line_items": [
                    {
                        "description": "Spare Parts Model X",
                        "quantity": 10,
                        "unit_price": 1000.0,
                        "taxable_value": 10000.0,
                        "gst_rate": 18.0,
                        "line_total": 11800.0,
                    }
                ],
                "taxable_total": 10000.0,
                "cgst": 900.0,
                "sgst": 900.0,
                "igst": 0.0,
                "grand_total": 11800.0,
                "currency": "INR",
            },
            "bank_statement": {
                "doc_type": "bank_statement",
                "bank_name": "HDFC Bank",
                "account_holder": "Manmohan Vishwakarma",
                "account_number_last4": "4589",
                "opening_balance": 50000.0,
                "closing_balance": 52500.0,
                "transactions": [
                    {
                        "date": "2025-01-05",
                        "description": "NEFT Salary Credit",
                        "credit": 5000.0,
                        "debit": 0.0,
                        "balance": 55000.0,
                    },
                    {
                        "date": "2025-01-10",
                        "description": "UPI Groceries",
                        "credit": 0.0,
                        "debit": 2500.0,
                        "balance": 52500.0,
                    },
                ],
            },
            "receipt": {
                "doc_type": "receipt",
                "vendor_name": "Blue Tokai Coffee",
                "date": "2025-02-20",
                "subtotal": 450.0,
                "tax": 22.5,
                "total": 472.5,
            },
        }

    def extract(
        self,
        pages: List[PageImage],
        ocr: Optional[List[OCRPage]],
        doc_type: DocType,
    ) -> RawExtraction:
        start = time.perf_counter()
        payload = self.canned_data.get(doc_type, {"doc_type": doc_type})
        latency = (time.perf_counter() - start) * 1000

        return RawExtraction(
            backend="stub",
            doc_type=doc_type,
            raw_payload=payload,
            json_valid=True,
            schema_valid=True,
            repair_retries=0,
            latency_ms=latency,
        )
