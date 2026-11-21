from datetime import date
from decimal import Decimal
from documind.extraction.normalize import (
    normalize_date,
    normalize_identifier,
    normalize_indian_amount,
    normalize_whitespace,
)


def test_normalize_whitespace():
    assert normalize_whitespace("  Tata   Motors   Limited  ") == "Tata Motors Limited"
    assert normalize_whitespace(None) is None
    assert normalize_whitespace("   ") is None


def test_normalize_identifier():
    assert normalize_identifier(" 27aapfu0939f1zv ") == "27AAPFU0939F1ZV"
    assert normalize_identifier("HDFC-0001234") == "HDFC0001234"
    assert normalize_identifier(None) is None


def test_normalize_indian_amount():
    assert normalize_indian_amount("1,23,456.50") == Decimal("123456.50")
    assert normalize_indian_amount("₹ 1,50,000/-") == Decimal("150000.00")
    assert normalize_indian_amount("Rs. 450.25") == Decimal("450.25")
    assert normalize_indian_amount("1200") == Decimal("1200.00")
    assert normalize_indian_amount("(500.00)") == Decimal("-500.00")
    assert normalize_indian_amount("-2,400.00") == Decimal("-2400.00")
    assert normalize_indian_amount(1500) == Decimal("1500.00")
    assert normalize_indian_amount(None) is None


def test_normalize_date():
    assert normalize_date("2025-02-15") == date(2025, 2, 15)
    assert normalize_date("15/02/2025") == date(2025, 2, 15)
    assert normalize_date("15-02-2025") == date(2025, 2, 15)
    assert normalize_date("15 Feb 2025") == date(2025, 2, 15)
    assert normalize_date("15th February 2025") == date(2025, 2, 15)
    assert normalize_date("Invalid date string") is None
    assert normalize_date(None) is None
