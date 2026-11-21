from typing import Dict

SYSTEM_EXTRACTION_PROMPT = """You are DocuMind, an expert information extraction system specialized in Indian business documents.
Your task is to analyze document images or OCR text and extract structured fields according to the requested JSON schema.

RULES:
1. Output MUST be a single, valid JSON object matching the requested schema.
2. For any field not explicitly found in the document, assign null. Never invent or hallucinate values.
3. Clean Indian currency and grouping numbers into standard decimal numbers (e.g., 1,23,456.50 -> 123456.50).
4. Parse dates into ISO format YYYY-MM-DD.
5. Extract GSTIN in uppercase without spaces.
6. Return ONLY the raw JSON object. Do not wrap in conversational preamble or commentary.
"""

DOC_SCHEMAS_DESCRIPTIONS: Dict[str, str] = {
    "gst_invoice": """{
  "doc_type": "gst_invoice",
  "invoice_number": string or null,
  "invoice_date": "YYYY-MM-DD" or null,
  "due_date": "YYYY-MM-DD" or null,
  "supplier": {"name": str, "gstin": str, "pan": str, "address": str, "state_code": str},
  "buyer": {"name": str, "gstin": str, "pan": str, "address": str, "state_code": str},
  "place_of_supply": str or null,
  "line_items": [{"description": str, "hsn_sac": str, "quantity": num, "unit": str, "unit_price": num, "discount": num, "taxable_value": num, "gst_rate": num, "line_total": num}],
  "taxable_total": num or null,
  "cgst": num or null,
  "sgst": num or null,
  "igst": num or null,
  "cess": num or null,
  "round_off": num or null,
  "grand_total": num or null,
  "currency": "INR"
}""",
    "bank_statement": """{
  "doc_type": "bank_statement",
  "bank_name": string or null,
  "account_holder": string or null,
  "account_number_last4": "last 4 digits only" or null,
  "ifsc": string or null,
  "period_start": "YYYY-MM-DD" or null,
  "period_end": "YYYY-MM-DD" or null,
  "opening_balance": num or null,
  "closing_balance": num or null,
  "transactions": [{"date": "YYYY-MM-DD", "description": str, "ref_no": str, "debit": num, "credit": num, "balance": num}]
}""",
    "receipt": """{
  "doc_type": "receipt",
  "vendor_name": string or null,
  "address": string or null,
  "date": "YYYY-MM-DD" or null,
  "line_items": [{"description": str, "quantity": num, "unit_price": num, "line_total": num}],
  "subtotal": num or null,
  "tax": num or null,
  "total": num or null
}""",
}


def build_user_prompt(doc_type: str, ocr_text: str = "") -> str:
    schema_hint = DOC_SCHEMAS_DESCRIPTIONS.get(doc_type, "{}")
    ocr_section = f"\n\nOCR Document Text:\n```\n{ocr_text}\n```" if ocr_text else ""
    return f"""Extract structured fields for document type '{doc_type}'.

Target JSON Schema:
```json
{schema_hint}
```
{ocr_section}

Output the extracted JSON matching the schema:"""
