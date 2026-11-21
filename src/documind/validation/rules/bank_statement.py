from decimal import Decimal
from typing import List
from documind.extraction.schemas.bank_statement import BankStatement
from documind.validation.engine import RuleResult

TOLERANCE = Decimal("0.01")


def evaluate_bank_statement_rules(stmt: BankStatement) -> List[RuleResult]:
    results: List[RuleResult] = []

    txns = stmt.transactions

    # 1. Running Balance Check (hard)
    running_balance_failed = False
    fail_msg = "Running balance verified across all transactions"
    failing_row = -1

    if txns and len(txns) >= 2:
        for i in range(1, len(txns)):
            prev_bal = txns[i - 1].balance
            curr_bal = txns[i].balance
            credit = txns[i].credit or Decimal("0.0")
            debit = txns[i].debit or Decimal("0.0")

            if prev_bal is not None and curr_bal is not None:
                expected = prev_bal + credit - debit
                if abs(expected - curr_bal) > TOLERANCE:
                    running_balance_failed = True
                    failing_row = i
                    fail_msg = f"Running balance broken at txn #{i}: prev {prev_bal} + cr {credit} - dr {debit} != curr {curr_bal}"
                    break

    results.append(
        RuleResult(
            rule_id="running_balance",
            severity="hard",
            passed=not running_balance_failed,
            message=fail_msg,
            fields=["transactions.balance", "transactions.debit", "transactions.credit"],
        )
    )

    # 2. Period Reconcile (hard)
    if stmt.opening_balance is not None and stmt.closing_balance is not None and txns:
        total_credit = sum((t.credit or Decimal("0.0")) for t in txns)
        total_debit = sum((t.debit or Decimal("0.0")) for t in txns)
        computed_closing = stmt.opening_balance + total_credit - total_debit
        period_ok = abs(computed_closing - stmt.closing_balance) <= TOLERANCE
        results.append(
            RuleResult(
                rule_id="period_reconcile",
                severity="hard",
                passed=period_ok,
                message="Opening + Credits - Debits equals Closing balance" if period_ok else f"Period closing mismatch: computed {computed_closing} vs reported {stmt.closing_balance}",
                fields=["opening_balance", "closing_balance", "transactions"],
            )
        )

    # 3. Single Sided Txn (soft)
    both_sided = []
    for idx, t in enumerate(txns):
        if (t.debit is not None and t.debit > 0) and (t.credit is not None and t.credit > 0):
            both_sided.append(f"txn #{idx}")

    results.append(
        RuleResult(
            rule_id="single_sided_txn",
            severity="soft",
            passed=len(both_sided) == 0,
            message=f"Transactions with both debit and credit found: {', '.join(both_sided)}" if both_sided else "All transactions are cleanly single-sided",
            fields=["transactions.debit", "transactions.credit"],
        )
    )

    # 4. Dates Monotonic (soft)
    monotonic_ok = True
    dates = [t.date for t in txns if t.date is not None]
    if len(dates) >= 2:
        for i in range(1, len(dates)):
            if dates[i] < dates[i - 1]:
                monotonic_ok = False
                break

    results.append(
        RuleResult(
            rule_id="dates_monotonic",
            severity="soft",
            passed=monotonic_ok,
            message="Transaction dates follow chronological order" if monotonic_ok else "Transaction dates are not strictly monotonic",
            fields=["transactions.date"],
        )
    )

    return results
