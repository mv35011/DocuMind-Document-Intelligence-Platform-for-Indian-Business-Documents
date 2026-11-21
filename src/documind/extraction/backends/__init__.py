from typing import Type
from documind.extraction.backends.ocr_llm import OCRLLMExtractor
from documind.extraction.backends.regex import RegexExtractor
from documind.extraction.backends.stub import StubExtractor
from documind.extraction.backends.vlm_finetuned import VLMFinetunedExtractor
from documind.extraction.backends.vlm_prompted import VLMPromptedExtractor
from documind.extraction.base import Extractor

BACKEND_REGISTRY: dict[str, Type[Extractor]] = {
    "stub": StubExtractor,
    "regex": RegexExtractor,
    "ocr_llm": OCRLLMExtractor,
    "vlm_prompted": VLMPromptedExtractor,
    "vlm_finetuned": VLMFinetunedExtractor,
}


def get_extractor(backend_name: str = "stub", **kwargs: object) -> Extractor:
    cls = BACKEND_REGISTRY.get(backend_name)
    if not cls:
        raise ValueError(f"Unknown extractor backend: {backend_name}. Available: {list(BACKEND_REGISTRY.keys())}")
    return cls(**kwargs)  # type: ignore[call-arg]


__all__ = [
    "Extractor",
    "StubExtractor",
    "RegexExtractor",
    "OCRLLMExtractor",
    "VLMPromptedExtractor",
    "VLMFinetunedExtractor",
    "get_extractor",
]
