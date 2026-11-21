from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Protocol

try:
    from pydantic import BaseModel

    class RawExtraction(BaseModel):
        backend: str
        doc_type: str
        raw_payload: Dict[str, Any]
        json_valid: bool = True
        schema_valid: bool = True
        repair_retries: int = 0
        latency_ms: float = 0.0
        tokens_in: Optional[int] = None
        tokens_out: Optional[int] = None

except ImportError:
    class RawExtraction:  # type: ignore[no-redef]
        def __init__(
            self,
            backend: str,
            doc_type: str,
            raw_payload: Dict[str, Any],
            json_valid: bool = True,
            schema_valid: bool = True,
            repair_retries: int = 0,
            latency_ms: float = 0.0,
            tokens_in: Optional[int] = None,
            tokens_out: Optional[int] = None,
        ):
            self.backend = backend
            self.doc_type = doc_type
            self.raw_payload = raw_payload
            self.json_valid = json_valid
            self.schema_valid = schema_valid
            self.repair_retries = repair_retries
            self.latency_ms = latency_ms
            self.tokens_in = tokens_in
            self.tokens_out = tokens_out


DocType = Literal["gst_invoice", "bank_statement", "receipt", "unknown"]


@dataclass
class PageImage:
    page_no: int
    image_bytes: bytes
    width: int
    height: int
    format: str = "PNG"


@dataclass
class OCRToken:
    text: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float


@dataclass
class OCRPage:
    page_no: int
    full_text: str
    tokens: List[OCRToken] = field(default_factory=list)


class Extractor(Protocol):
    name: str

    def extract(
        self,
        pages: List[PageImage],
        ocr: Optional[List[OCRPage]],
        doc_type: DocType,
    ) -> RawExtraction:
        ...
