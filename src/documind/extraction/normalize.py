import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

# Regex for currency prefixes and suffixes
CURRENCY_CLEAN_REGEX = re.compile(r"[₹\$\€\£]|INR|Rs\.?|\/-", re.IGNORECASE)
WHITESPACE_COLLAPSE_REGEX = re.compile(r"\s+")

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
]


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    cleaned = WHITESPACE_COLLAPSE_REGEX.sub(" ", text).strip()
    return cleaned if cleaned else None


def normalize_identifier(identifier: Optional[str]) -> Optional[str]:
    """Cleans up GSTIN, PAN, IFSC codes: uppercase, alphanumeric only, trimmed."""
    if identifier is None:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9]", "", identifier).upper()
    return cleaned if cleaned else None


def normalize_indian_amount(raw_val: Optional[str | int | float | Decimal]) -> Optional[Decimal]:
    """Parses numbers including Indian numbering format e.g. '1,23,456.50' or '₹ 12,345/-'."""
    if raw_val is None:
        return None
    if isinstance(raw_val, Decimal):
        return raw_val.quantize(Decimal("0.01"))
    if isinstance(raw_val, (int, float)):
        return Decimal(str(raw_val)).quantize(Decimal("0.01"))

    text = str(raw_val).strip()
    # Strip currency signs
    text = CURRENCY_CLEAN_REGEX.sub("", text).strip()
    # Remove grouping commas and spaces
    text = text.replace(",", "").replace(" ", "")

    if not text:
        return None

    # Handle parenthesis for negative values e.g. (1200.00)
    is_negative = False
    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1]
    elif text.startswith("-"):
        is_negative = True
        text = text[1:]

    try:
        val = Decimal(text)
        if is_negative:
            val = -val
        return val.quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def normalize_date(raw_date: Optional[str | date | datetime]) -> Optional[date]:
    """Normalizes multiple human and machine date formats into ISO standard date."""
    if raw_date is None:
        return None
    if isinstance(raw_date, datetime):
        return raw_date.date()
    if isinstance(raw_date, date):
        return raw_date

    text = str(raw_date).strip()
    # Clean standard suffixes (1st, 2nd, 3rd, 4th)
    text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text)

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None
