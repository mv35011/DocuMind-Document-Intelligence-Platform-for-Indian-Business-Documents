from documind.validation.gstin import (
    compute_gstin_checksum,
    parse_gstin_components,
    validate_gstin_checksum,
    validate_gstin_format,
)

# Known valid GSTINs with mathematically verified Base-36 checksums
VALID_GSTINS = [
    "27AAPFU0939F1ZV",  # Maharashtra
    "29AABCT1332L1ZA",  # Karnataka
    "06AABCU9603R1ZR",  # Haryana
    "27AABCT1332L1ZE",  # Maharashtra
]

INVALID_GSTINS = [
    "27AAPFU0939F1Z0",  # Checksum mismatch
    "27AAPFU0939F1Z",   # Length 14 (too short)
    "27AAPFU0939F1ZVA", # Length 16 (too long)
    "INVALIDGSTIN123",
]


def test_gstin_format_valid():
    for gstin in VALID_GSTINS:
        assert validate_gstin_format(gstin) is True


def test_gstin_format_invalid():
    assert validate_gstin_format("INVALID") is False
    assert validate_gstin_format("27AAPFU0939F1Z") is False
    assert validate_gstin_format(None) is False


def test_gstin_checksum_algorithm():
    # Verify the 15th character calculated matches the known check character
    for gstin in VALID_GSTINS:
        calculated_check = compute_gstin_checksum(gstin[:14])
        assert calculated_check == gstin[14]
        assert validate_gstin_checksum(gstin) is True


def test_gstin_checksum_invalid():
    # Tamper with the check digit
    tampered = "27AAPFU0939F1Z0"
    assert validate_gstin_checksum(tampered) is False


def test_parse_gstin_components():
    res = parse_gstin_components("27AAPFU0939F1ZV")
    assert res is not None
    state_code, pan, state_name = res
    assert state_code == "27"
    assert pan == "AAPFU0939F"
    assert state_name == "Maharashtra"
