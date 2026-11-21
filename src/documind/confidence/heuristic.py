from typing import Any, Dict, List
from documind.validation.engine import RuleResult


def compute_heuristic_confidence(
    field_grounding: Dict[str, Dict[str, Any]],
    rule_results: List[RuleResult],
    required_fields: List[str],
) -> Dict[str, Any]:
    """Computes field-level and document-level confidence scores.

    Formula:
      field_conf = 0.6 * grounding_score + 0.4 * rule_ok
      doc_conf = min over required fields
    """
    # Map rules touching specific fields
    failing_fields = set()
    for rule in rule_results:
        if not rule.passed:
            for f in rule.fields:
                failing_fields.add(f)

    field_confidences: Dict[str, float] = {}

    for field_path, ground_info in field_grounding.items():
        g_score = ground_info.get("score", 0.0)
        rule_ok = 0.0 if field_path in failing_fields else 1.0
        conf = 0.6 * g_score + 0.4 * rule_ok
        field_confidences[field_path] = round(conf, 3)

    # Document confidence is the minimum across required fields
    req_confs = [field_confidences.get(rf, 0.5) for rf in required_fields if rf in field_confidences]
    doc_conf = min(req_confs) if req_confs else (min(field_confidences.values()) if field_confidences else 0.5)

    return {
        "document_confidence": round(doc_conf, 3),
        "field_confidences": field_confidences,
    }
