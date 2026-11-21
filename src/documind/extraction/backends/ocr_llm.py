import json
import time
from typing import Any, Dict, List, Optional
from documind.core.config import get_settings
from documind.extraction.base import DocType, OCRPage, PageImage, RawExtraction
from documind.extraction.parse_repair import create_repair_prompt, extract_json_string
from documind.extraction.prompts import SYSTEM_EXTRACTION_PROMPT, build_user_prompt
from documind.extraction.schemas import BankStatement, GSTInvoice, Receipt

SCHEMA_MAP = {
    "gst_invoice": GSTInvoice,
    "bank_statement": BankStatement,
    "receipt": Receipt,
}


class OCRLLMExtractor:
    """Baseline B1: OCR full text passed to a prompted LLM (e.g. Groq Cloud Llama-3.3 70B)."""
    name = "ocr_llm"

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        try:
            from openai import OpenAI
            self.client: Optional[OpenAI] = OpenAI(base_url=self.base_url, api_key=self.api_key)
        except ImportError:
            self.client = None

    def extract(
        self,
        pages: List[PageImage],
        ocr: Optional[List[OCRPage]],
        doc_type: DocType,
    ) -> RawExtraction:
        if self.client is None:
            return RawExtraction(
                backend="ocr_llm",
                doc_type=doc_type,
                raw_payload={"error": "openai library not installed"},
                json_valid=False,
                schema_valid=False,
            )

        start = time.perf_counter()
        full_ocr_text = "\n\n".join(f"--- Page {p.page_no} ---\n{p.full_text}" for p in (ocr or []))
        user_prompt = build_user_prompt(doc_type, full_ocr_text)

        messages = [
            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        repair_retries = 0
        tokens_in = 0
        tokens_out = 0

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            raw_content = resp.choices[0].message.content or "{}"
            if resp.usage:
                tokens_in += resp.usage.prompt_tokens
                tokens_out += resp.usage.completion_tokens

            # Validate against Pydantic schema
            schema_cls = SCHEMA_MAP.get(doc_type)
            clean_json_str = extract_json_string(raw_content)
            parsed_dict = json.loads(clean_json_str)
            schema_valid = True

            if schema_cls:
                try:
                    schema_cls.model_validate(parsed_dict)
                except Exception as ve:
                    # Attempt 1 repair retry
                    repair_retries += 1
                    repair_prompt = create_repair_prompt(raw_content, str(ve), doc_type)
                    retry_resp = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                            {"role": "user", "content": repair_prompt},
                        ],  # type: ignore
                        temperature=0.0,
                        response_format={"type": "json_object"},
                    )
                    retry_content = retry_resp.choices[0].message.content or "{}"
                    if retry_resp.usage:
                        tokens_in += retry_resp.usage.prompt_tokens
                        tokens_out += retry_resp.usage.completion_tokens
                    parsed_dict = json.loads(extract_json_string(retry_content))
                    schema_cls.model_validate(parsed_dict)

            latency = (time.perf_counter() - start) * 1000
            return RawExtraction(
                backend="ocr_llm",
                doc_type=doc_type,
                raw_payload=parsed_dict,
                json_valid=True,
                schema_valid=schema_valid,
                repair_retries=repair_retries,
                latency_ms=latency,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return RawExtraction(
                backend="ocr_llm",
                doc_type=doc_type,
                raw_payload={"error": str(e), "doc_type": doc_type},
                json_valid=False,
                schema_valid=False,
                repair_retries=repair_retries,
                latency_ms=latency,
            )
