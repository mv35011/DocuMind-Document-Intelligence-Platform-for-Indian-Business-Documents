from decimal import Decimal
from typing import List
from documind.extraction.schemas.receipt import Receipt
from documind.validation.engine import RuleResult

TOLERANCE = Decimal("1.00")


def evaluate_receipt_rules(rcpt: Receipt) -> List[RuleResult]:
    results: List[RuleResult] = []

    # 1. Total >= Subtotal (soft)
    if rcpt.total is not None and rcpt.subtotal is not None:
        total_ge = rcpt.total >= rcpt.subtotal - TOLERANCE
        results.append(
            RuleResult(
                rule_id="total_ge_subtotal",
                severity="soft",
                passed=total_ge,
                message="Total is greater than or equal to subtotal" if total_ge else f"Total ({rcpt.total}) is less than subtotal ({rcpt.subtotal})",
                fields=["total", "subtotal"],
            )
        )

    # 2. Items sum matches subtotal (soft)
    if rcpt.subtotal is not None and rcpt.line_items:
        items_sum = sum((item.line_total or item.taxable_value or Decimal("0.0")) for item in rcpt.line_items)
        if items_sum > 0:
            matches = abs(items_sum - rcpt.subtotal) <= TOLERANCE
            results.append(
                RuleResult(
                    rule_id="items_sum_matches_subtotal",
                    severity="soft",
                    passed=matches,
                    message="Sum of items matches subtotal" if matches else f"Sum of items ({items_sum}) != subtotal ({rcpt.subtotal})",
                    fields=["subtotal", "line_items"],
                )
            )

    return results
