from datetime import date
from decimal import Decimal
from documind.extraction.schemas import (
    BankStatement,
    BankTxn,
    GSTInvoice,
    InvoiceLine,
    Party,
    Receipt,
)
from documind.validation.engine import ValidationEngine


def test_gst_invoice_passing_validation():
    engine = ValidationEngine()
    inv = GSTInvoice(
        invoice_number="INV-2025-01",
        invoice_date=date(2025, 1, 10),
        supplier=Party(name="Supplier Corp", gstin="27AAPFU0939F1ZV", state_code="27"),
        buyer=Party(name="Buyer Ltd", gstin="27AABCT1332L1ZE", state_code="27"),
        place_of_supply="27",
        line_items=[
            InvoiceLine(
                description="Widget A",
                quantity=Decimal("10"),
                unit_price=Decimal("100.00"),
                taxable_value=Decimal("1000.00"),
                gst_rate=Decimal("18.0"),
                line_total=Decimal("1180.00"),
            )
        ],
        taxable_total=Decimal("1000.00"),
        cgst=Decimal("90.00"),
        sgst=Decimal("90.00"),
        igst=Decimal("0.00"),
        grand_total=Decimal("1180.00"),
    )

    summary = engine.evaluate(inv)
    assert summary.auto_approvable is True
    assert summary.hard_failures_count == 0


def test_gst_invoice_failing_totals_reconcile():
    engine = ValidationEngine()
    inv = GSTInvoice(
        invoice_number="INV-2025-02",
        invoice_date=date(2025, 1, 10),
        supplier=Party(name="Supplier Corp", gstin="27AAPFU0939F1ZV"),
        line_items=[
            InvoiceLine(
                description="Widget A",
                quantity=Decimal("10"),
                unit_price=Decimal("100.00"),
                taxable_value=Decimal("1000.00"),
            )
        ],
        taxable_total=Decimal("1000.00"),
        cgst=Decimal("90.00"),
        sgst=Decimal("90.00"),
        # Incorrect grand total: should be 1180, set to 1500
        grand_total=Decimal("1500.00"),
    )

    summary = engine.evaluate(inv)
    assert summary.auto_approvable is False
    assert summary.hard_failures_count > 0
    rule_ids = [r.rule_id for r in summary.rule_results if not r.passed]
    assert "totals_reconcile" in rule_ids


def test_bank_statement_running_balance_pass():
    engine = ValidationEngine()
    stmt = BankStatement(
        bank_name="State Bank of India",
        account_holder="Manmohan Vishwakarma",
        opening_balance=Decimal("10000.00"),
        closing_balance=Decimal("12500.00"),
        transactions=[
            BankTxn(
                date=date(2025, 1, 1),
                description="Opening",
                credit=Decimal("5000.00"),
                debit=Decimal("0.00"),
                balance=Decimal("15000.00"),
            ),
            BankTxn(
                date=date(2025, 1, 5),
                description="ATM Withdrawal",
                credit=Decimal("0.00"),
                debit=Decimal("2500.00"),
                balance=Decimal("12500.00"),
            ),
        ],
    )

    summary = engine.evaluate(stmt)
    assert summary.hard_failures_count == 0
    assert summary.auto_approvable is True


def test_bank_statement_running_balance_break():
    engine = ValidationEngine()
    stmt = BankStatement(
        bank_name="State Bank of India",
        opening_balance=Decimal("10000.00"),
        closing_balance=Decimal("12500.00"),
        transactions=[
            BankTxn(
                date=date(2025, 1, 1),
                credit=Decimal("5000.00"),
                debit=Decimal("0.00"),
                balance=Decimal("15000.00"),
            ),
            # Faulty balance: 15000 - 2500 = 12500, but says 9999
            BankTxn(
                date=date(2025, 1, 5),
                credit=Decimal("0.00"),
                debit=Decimal("2500.00"),
                balance=Decimal("9999.00"),
            ),
        ],
    )

    summary = engine.evaluate(stmt)
    assert summary.auto_approvable is False
    failing_rules = [r.rule_id for r in summary.rule_results if not r.passed]
    assert "running_balance" in failing_rules


def test_receipt_validation():
    engine = ValidationEngine()
    rcpt = Receipt(
        vendor_name="Starbucks",
        date=date(2025, 2, 1),
        subtotal=Decimal("400.00"),
        tax=Decimal("20.00"),
        total=Decimal("420.00"),
    )
    summary = engine.evaluate(rcpt)
    assert summary.hard_failures_count == 0
