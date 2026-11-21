from datetime import date
from decimal import Decimal
from typing import List
from documind.extraction.schemas.gst_invoice import GSTInvoice
from documind.validation.engine import RuleResult
from documind.validation.gstin import validate_gstin_checksum, validate_gstin_format

ALLOWED_GST_RATES = {
    Decimal("0.0"),
    Decimal("0.25"),
    Decimal("3.0"),
    Decimal("5.0"),
    Decimal("12.0"),
    Decimal("18.0"),
    Decimal("28.0"),
    Decimal("40.0"),
}

GST_START_DATE = date(2017, 7, 1)
TOLERANCE = Decimal("1.00")


def evaluate_gst_invoice_rules(inv: GSTInvoice) -> List[RuleResult]:
    results: List[RuleResult] = []

    # 1. Required Fields (hard)
    missing = []
    if not inv.invoice_number:
        missing.append("invoice_number")
    if not inv.invoice_date:
        missing.append("invoice_date")
    if not inv.supplier or not inv.supplier.name:
        missing.append("supplier.name")
    if inv.grand_total is None:
        missing.append("grand_total")

    results.append(
        RuleResult(
            rule_id="required_fields",
            severity="hard",
            passed=(len(missing) == 0),
            message=f"Missing mandatory fields: {', '.join(missing)}" if missing else "Mandatory fields present",
            fields=missing or ["invoice_number", "invoice_date", "supplier.name", "grand_total"],
        )
    )

    # 2. Supplier GSTIN format & checksum (hard)
    if inv.supplier and inv.supplier.gstin:
        fmt_ok = validate_gstin_format(inv.supplier.gstin)
        results.append(
            RuleResult(
                rule_id="supplier_gstin_format",
                severity="hard",
                passed=fmt_ok,
                message="Supplier GSTIN matches standard 15-character format" if fmt_ok else "Supplier GSTIN format invalid",
                fields=["supplier.gstin"],
            )
        )
        if fmt_ok:
            chk_ok = validate_gstin_checksum(inv.supplier.gstin)
            results.append(
                RuleResult(
                    rule_id="supplier_gstin_checksum",
                    severity="hard",
                    passed=chk_ok,
                    message="Supplier GSTIN check-digit matches algorithm" if chk_ok else "Supplier GSTIN checksum failed",
                    fields=["supplier.gstin"],
                )
            )

    # 3. Buyer GSTIN format & checksum (hard if present)
    if inv.buyer and inv.buyer.gstin:
        b_fmt_ok = validate_gstin_format(inv.buyer.gstin)
        results.append(
            RuleResult(
                rule_id="buyer_gstin_format",
                severity="hard",
                passed=b_fmt_ok,
                message="Buyer GSTIN format valid" if b_fmt_ok else "Buyer GSTIN format invalid",
                fields=["buyer.gstin"],
            )
        )
        if b_fmt_ok:
            b_chk_ok = validate_gstin_checksum(inv.buyer.gstin)
            results.append(
                RuleResult(
                    rule_id="buyer_gstin_checksum",
                    severity="hard",
                    passed=b_chk_ok,
                    message="Buyer GSTIN check-digit valid" if b_chk_ok else "Buyer GSTIN checksum failed",
                    fields=["buyer.gstin"],
                )
            )

    # 4. Tax Type Consistency (hard)
    # If supplier state equals place of supply then intra-state (CGST + SGST equal, IGST null or 0).
    # Otherwise inter-state (IGST present, CGST/SGST null or 0).
    supp_state = None
    if inv.supplier and inv.supplier.gstin and len(inv.supplier.gstin) >= 2:
        supp_state = inv.supplier.gstin[:2]
    elif inv.supplier and inv.supplier.state_code:
        supp_state = inv.supplier.state_code

    pos = inv.place_of_supply
    if supp_state and pos:
        # Check if place of supply starts with the state code or equals state
        is_intra = (pos == supp_state) or (len(pos) >= 2 and pos[:2] == supp_state)
        cgst = inv.cgst or Decimal("0.0")
        sgst = inv.sgst or Decimal("0.0")
        igst = inv.igst or Decimal("0.0")

        if is_intra:
            # Intra-state: CGST should equal SGST within tolerance, IGST should be ~0
            cgst_sgst_equal = abs(cgst - sgst) <= TOLERANCE
            igst_zero = igst <= TOLERANCE
            passed = cgst_sgst_equal and igst_zero
            msg = "Intra-state GST consistent (CGST==SGST, IGST=0)" if passed else f"Intra-state tax mismatch: CGST={cgst}, SGST={sgst}, IGST={igst}"
        else:
            # Inter-state: IGST present, CGST and SGST should be ~0
            passed = (cgst <= TOLERANCE and sgst <= TOLERANCE and igst > 0)
            msg = "Inter-state GST consistent (IGST charged)" if passed else f"Inter-state tax mismatch: CGST={cgst}, SGST={sgst}, IGST={igst}"

        results.append(
            RuleResult(
                rule_id="tax_type_consistent",
                severity="hard",
                passed=passed,
                message=msg,
                fields=["place_of_supply", "cgst", "sgst", "igst"],
            )
        )

    # 5. GST Rates Allowed (soft)
    rate_fails = []
    for idx, item in enumerate(inv.line_items):
        if item.gst_rate is not None:
            # Match within 0.05
            if not any(abs(item.gst_rate - allowed) < Decimal("0.05") for allowed in ALLOWED_GST_RATES):
                rate_fails.append(f"item[{idx}].gst_rate={item.gst_rate}")

    results.append(
        RuleResult(
            rule_id="gst_rate_allowed",
            severity="soft",
            passed=(len(rate_fails) == 0),
            message=f"Non-standard GST rate(s) found: {', '.join(rate_fails)}" if rate_fails else "All item GST rates valid",
            fields=["line_items.gst_rate"],
        )
    )

    # 6. Line Math (soft)
    line_math_fails = []
    for idx, item in enumerate(inv.line_items):
        if item.quantity is not None and item.unit_price is not None and item.taxable_value is not None:
            expected_taxable = (item.quantity * item.unit_price) - (item.discount or Decimal("0.0"))
            if abs(expected_taxable - item.taxable_value) > TOLERANCE:
                line_math_fails.append(f"item[{idx}] math mismatch: qty*price-disc={expected_taxable} vs taxable={item.taxable_value}")

    results.append(
        RuleResult(
            rule_id="line_math",
            severity="soft",
            passed=(len(line_math_fails) == 0),
            message="; ".join(line_math_fails) if line_math_fails else "Line items calculation matches",
            fields=["line_items.taxable_value", "line_items.quantity", "line_items.unit_price"],
        )
    )

    # 7. Totals Reconcile (hard)
    if inv.taxable_total is not None and inv.line_items:
        sum_taxable = sum((i.taxable_value or Decimal("0.0")) for i in inv.line_items)
        lines_reconcile = abs(sum_taxable - inv.taxable_total) <= TOLERANCE
        results.append(
            RuleResult(
                rule_id="taxable_lines_reconcile",
                severity="hard",
                passed=lines_reconcile,
                message="Sum of line taxable values matches taxable_total" if lines_reconcile else f"Sum of lines ({sum_taxable}) != taxable_total ({inv.taxable_total})",
                fields=["taxable_total", "line_items.taxable_value"],
            )
        )

    if inv.grand_total is not None and inv.taxable_total is not None:
        computed_grand = (
            inv.taxable_total
            + (inv.cgst or Decimal("0.0"))
            + (inv.sgst or Decimal("0.0"))
            + (inv.igst or Decimal("0.0"))
            + (inv.cess or Decimal("0.0"))
            + (inv.round_off or Decimal("0.0"))
        )
        grand_reconciles = abs(computed_grand - inv.grand_total) <= TOLERANCE
        results.append(
            RuleResult(
                rule_id="totals_reconcile",
                severity="hard",
                passed=grand_reconciles,
                message="Grand total equals taxable total plus taxes and adjustments" if grand_reconciles else f"Grand total mismatch: computed {computed_grand} vs extracted {inv.grand_total}",
                fields=["grand_total", "taxable_total", "cgst", "sgst", "igst", "cess", "round_off"],
            )
        )

    # 8. Dates Sane (soft)
    if inv.invoice_date:
        today = date.today()
        is_after_gst = inv.invoice_date >= GST_START_DATE
        is_not_future = inv.invoice_date <= today
        dates_ok = is_after_gst and is_not_future
        results.append(
            RuleResult(
                rule_id="dates_sane",
                severity="soft",
                passed=dates_ok,
                message="Invoice date is realistic (post-GST, not future)" if dates_ok else f"Unrealistic invoice date: {inv.invoice_date}",
                fields=["invoice_date"],
            )
        )

    return results
