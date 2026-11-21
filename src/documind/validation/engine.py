from typing import Any, List, Literal, Optional

try:
    from pydantic import BaseModel

    class RuleResult(BaseModel):
        rule_id: str
        severity: Literal["hard", "soft"]
        passed: bool
        message: str
        fields: List[str]

    class ValidationSummary(BaseModel):
        is_valid: bool
        hard_failures_count: int
        soft_failures_count: int
        rule_results: List[RuleResult]

        @property
        def auto_approvable(self) -> bool:
            return self.hard_failures_count == 0

except ImportError:
    class RuleResult:  # type: ignore[no-redef]
        def __init__(self, rule_id: str, severity: str, passed: bool, message: str, fields: List[str]):
            self.rule_id = rule_id
            self.severity = severity
            self.passed = passed
            self.message = message
            self.fields = fields

    class ValidationSummary:  # type: ignore[no-redef]
        def __init__(self, is_valid: bool, hard_failures_count: int, soft_failures_count: int, rule_results: List[RuleResult]):
            self.is_valid = is_valid
            self.hard_failures_count = hard_failures_count
            self.soft_failures_count = soft_failures_count
            self.rule_results = rule_results

        @property
        def auto_approvable(self) -> bool:
            return self.hard_failures_count == 0


class ValidationEngine:
    def __init__(self) -> None:
        pass

    def evaluate(self, model: Any) -> ValidationSummary:
        doc_type = getattr(model, "doc_type", None)
        results: List[RuleResult] = []

        if doc_type == "gst_invoice":
            from documind.validation.rules.gst_invoice import evaluate_gst_invoice_rules
            results = evaluate_gst_invoice_rules(model)
        elif doc_type == "bank_statement":
            from documind.validation.rules.bank_statement import evaluate_bank_statement_rules
            results = evaluate_bank_statement_rules(model)
        elif doc_type == "receipt":
            from documind.validation.rules.receipt import evaluate_receipt_rules
            results = evaluate_receipt_rules(model)
        else:
            results = [
                RuleResult(
                    rule_id="unknown_doc_type",
                    severity="hard",
                    passed=False,
                    message=f"Unsupported document type: {doc_type}",
                    fields=["doc_type"],
                )
            ]

        hard_fails = sum(1 for r in results if not r.passed and r.severity == "hard")
        soft_fails = sum(1 for r in results if not r.passed and r.severity == "soft")

        return ValidationSummary(
            is_valid=(hard_fails == 0 and soft_fails == 0),
            hard_failures_count=hard_fails,
            soft_failures_count=soft_fails,
            rule_results=results,
        )
