import math
from typing import Any, Dict, List, Tuple


def compute_expected_calibration_error(
    confidences: List[float],
    accuracies: List[int],
    n_bins: int = 10,
) -> Tuple[float, List[Dict[str, Any]]]:
    """Computes Expected Calibration Error (ECE) and binning data for reliability diagrams."""
    if not confidences or len(confidences) != len(accuracies):
        return 0.0, []

    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    bins_data = []
    ece = 0.0
    total_samples = len(confidences)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Find points in bin
        indices = [
            idx for idx, c in enumerate(confidences)
            if (bin_lower <= c < bin_upper) or (i == n_bins - 1 and bin_lower <= c <= bin_upper)
        ]

        bin_size = len(indices)
        if bin_size > 0:
            avg_confidence = sum(confidences[idx] for idx in indices) / bin_size
            avg_accuracy = sum(accuracies[idx] for idx in indices) / bin_size
            ece += (bin_size / total_samples) * abs(avg_accuracy - avg_confidence)

            bins_data.append({
                "bin_index": i,
                "range": f"[{bin_lower:.1f}, {bin_upper:.1f}]",
                "count": bin_size,
                "avg_confidence": round(avg_confidence, 4),
                "avg_accuracy": round(avg_accuracy, 4),
            })

    return round(ece, 4), bins_data


class CalibratedConfidenceScorer:
    """Logistic regression Platt scaling model for field error probability."""

    def __init__(self, w_grounding: float = 2.4, w_ocr: float = 1.2, w_rule: float = 1.8, bias: float = -1.5):
        self.w_grounding = w_grounding
        self.w_ocr = w_ocr
        self.w_rule = w_rule
        self.bias = bias

    def predict_probability(self, grounding_score: float, ocr_conf: float, rule_passed: bool) -> float:
        """Predicts calibrated probability that the field extraction is correct."""
        z = (
            self.bias
            + self.w_grounding * grounding_score
            + self.w_ocr * ocr_conf
            + self.w_rule * (1.0 if rule_passed else -1.0)
        )
        # Sigmoid
        prob = 1.0 / (1.0 + math.exp(-max(min(z, 20.0), -20.0)))
        return round(prob, 4)
