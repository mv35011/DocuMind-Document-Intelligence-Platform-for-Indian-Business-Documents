from typing import Any, Dict, List, Optional
from documind.extraction.base import OCRPage

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


def fuzzy_similarity(s1: str, s2: str) -> float:
    """Calculates partial ratio string similarity (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    if HAS_RAPIDFUZZ:
        return fuzz.partial_ratio(s1.lower(), s2.lower()) / 100.0
    # Fallback substring matching
    s1_low, s2_low = s1.lower(), s2.lower()
    if s1_low in s2_low or s2_low in s1_low:
        return 1.0
    return 0.0


def ground_field_value(
    val: Any,
    ocr_pages: List[OCRPage],
    threshold: float = 0.75,
) -> Dict[str, Any]:
    """Finds best matching token sequence in OCR tokens as visual evidence."""
    if val is None:
        return {"grounded": False, "score": 0.0, "bbox": None, "page": None}

    val_str = str(val).strip()
    if not val_str:
        return {"grounded": False, "score": 0.0, "bbox": None, "page": None}

    best_score = 0.0
    best_bbox: Optional[List[int]] = None
    best_page: Optional[int] = None

    for page in ocr_pages:
        # Check against individual tokens
        for token in page.tokens:
            score = fuzzy_similarity(val_str, token.text)
            if score > best_score:
                best_score = score
                best_bbox = token.bbox
                best_page = page.page_no
                if best_score >= 0.99:
                    break

        # Fallback check against full page text
        if best_score < threshold and val_str.lower() in page.full_text.lower():
            best_score = max(best_score, 0.85)
            best_page = page.page_no

    return {
        "grounded": best_score >= threshold,
        "score": round(best_score, 3),
        "bbox": best_bbox,
        "page": best_page,
    }
