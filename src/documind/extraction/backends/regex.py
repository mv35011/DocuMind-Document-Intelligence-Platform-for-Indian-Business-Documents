import re
import time
from typing import List, Optional
from documind.extraction.base import DocType, OCRPage, PageImage, RawExtraction
from documind.extraction.normalize import normalize_date, normalize_identifier, normalize_indian_amount

# Basic regex rules for Baseline B0
GSTIN_REGEX = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
INV_NUM_REGEX = re.compile(r"(?:Invoice\s*(?:No|Num|Number|#)[\s:]*)([A-Z0-9\-\/]+)", re.IGNORECASE)
DATE_REGEX = re.compile(r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b")
TOTAL_REGEX = re.compile(r"(?:Total|Grand\s*Total|Net\s*Amount)[\s:]*([₹\s0-9,\.]+)", re.IGNORECASE)


class RegexExtractor:
    """Baseline B0: Naive regex rules over OCR text."""
    name = "regex"

    def extract(
        self,
        pages: List[PageImage],
        ocr: Optional[List[OCRPage]],
        doc_type: DocType,
    ) -> RawExtraction:
        start = time.perf_counter()
        full_text = "\n".join(p.full_text for p in (ocr or []))

        payload: dict = {"doc_type": doc_type}

        if doc_type == "gst_invoice":
            # Extract GSTINs
            gstins = GSTIN_REGEX.findall(full_text)
            supplier_gstin = gstins[0] if len(gstins) > 0 else None
            buyer_gstin = gstins[1] if len(gstins) > 1 else None

            # Extract invoice number
            inv_match = INV_NUM_REGEX.search(full_text)
            invoice_num = inv_match.group(1).strip() if inv_match else None

            # Extract dates
            date_matches = DATE_REGEX.findall(full_text)
            inv_date = None
            if date_matches:
                d = normalize_date(date_matches[0])
                inv_date = d.isoformat() if d else None

            # Extract Grand Total
            tot_match = TOTAL_REGEX.search(full_text)
            grand_total = None
            if tot_match:
                amt = normalize_indian_amount(tot_match.group(1))
                grand_total = float(amt) if amt else None

            payload = {
                "doc_type": "gst_invoice",
                "invoice_number": invoice_num,
                "invoice_date": inv_date,
                "supplier": {"name": None, "gstin": supplier_gstin},
                "buyer": {"name": None, "gstin": buyer_gstin},
                "line_items": [],
                "grand_total": grand_total,
            }

        elif doc_type == "receipt":
            date_matches = DATE_REGEX.findall(full_text)
            rcpt_date = None
            if date_matches:
                d = normalize_date(date_matches[0])
                rcpt_date = d.isoformat() if d else None

            tot_match = TOTAL_REGEX.search(full_text)
            total = None
            if tot_match:
                amt = normalize_indian_amount(tot_match.group(1))
                total = float(amt) if amt else None

            payload = {
                "doc_type": "receipt",
                "vendor_name": None,
                "date": rcpt_date,
                "total": total,
            }

        latency = (time.perf_counter() - start) * 1000
        return RawExtraction(
            backend="regex",
            doc_type=doc_type,
            raw_payload=payload,
            json_valid=True,
            schema_valid=True,
            repair_retries=0,
            latency_ms=latency,
        )
