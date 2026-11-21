import base64
import json
import time
from typing import List, Optional
from documind.core.config import get_settings
from documind.extraction.base import DocType, OCRPage, PageImage, RawExtraction
from documind.extraction.parse_repair import extract_json_string
from documind.extraction.prompts import SYSTEM_EXTRACTION_PROMPT, build_user_prompt
from documind.extraction.schemas import BankStatement, GSTInvoice, Receipt

SCHEMA_MAP = {
    "gst_invoice": GSTInvoice,
    "bank_statement": BankStatement,
    "receipt": Receipt,
}


class VLMFinetunedExtractor:
    """Model M1: Fine-tuned Qwen2-VL served via vLLM OpenAI compatible endpoint with guided JSON decoding."""
    name = "vlm_finetuned"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.VLM_BASE_URL
        self.model = model or "documind-qwen2-vl-2b-qlora"
        try:
            from openai import OpenAI
            self.client: Optional[OpenAI] = OpenAI(base_url=self.base_url, api_key="EMPTY")
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
                backend="vlm_finetuned",
                doc_type=doc_type,
                raw_payload={"error": "openai library not installed"},
                json_valid=False,
                schema_valid=False,
            )

        start = time.perf_counter()
        user_text = build_user_prompt(doc_type)

        content_items: list = [{"type": "text", "text": user_text}]
        for page in pages:
            b64_img = base64.b64encode(page.image_bytes).decode("utf-8")
            content_items.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_img}"},
            })

        messages = [
            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
            {"role": "user", "content": content_items},
        ]

        schema_cls = SCHEMA_MAP.get(doc_type)
        extra_body = {}
        if schema_cls and hasattr(schema_cls, "model_json_schema"):
            extra_body["guided_json"] = schema_cls.model_json_schema()

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=0.0,
                extra_body=extra_body,  # type: ignore
            )
            raw_content = resp.choices[0].message.content or "{}"
            clean_json_str = extract_json_string(raw_content)
            parsed_dict = json.loads(clean_json_str)

            if schema_cls:
                schema_cls.model_validate(parsed_dict)

            latency = (time.perf_counter() - start) * 1000
            return RawExtraction(
                backend="vlm_finetuned",
                doc_type=doc_type,
                raw_payload=parsed_dict,
                json_valid=True,
                schema_valid=True,
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return RawExtraction(
                backend="vlm_finetuned",
                doc_type=doc_type,
                raw_payload={"error": str(e), "doc_type": doc_type},
                json_valid=False,
                schema_valid=False,
                latency_ms=latency,
            )
