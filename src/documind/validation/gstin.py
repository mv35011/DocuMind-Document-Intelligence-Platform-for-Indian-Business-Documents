import re
from typing import Optional, Tuple

GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_REGEX = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

# Indian GST State Codes dictionary
GST_STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}


def validate_gstin_format(gstin: Optional[str]) -> bool:
    if not gstin:
        return False
    return bool(GSTIN_REGEX.match(gstin.strip().upper()))


def compute_gstin_checksum(gstin14: str) -> str:
    """Computes the 15th checksum character of a 14-character GSTIN prefix."""
    running_sum = 0
    for idx, char in enumerate(gstin14[:14].upper()):
        v = GSTIN_CHARSET.index(char)
        factor = 1 if (idx % 2 == 0) else 2
        p = v * factor
        running_sum += (p // 36) + (p % 36)

    check_idx = (36 - (running_sum % 36)) % 36
    return GSTIN_CHARSET[check_idx]


def validate_gstin_checksum(gstin: Optional[str]) -> bool:
    if not gstin or len(gstin.strip()) != 15:
        return False
    clean = gstin.strip().upper()
    expected_char = compute_gstin_checksum(clean[:14])
    return clean[14] == expected_char


def parse_gstin_components(gstin: str) -> Optional[Tuple[str, str, str]]:
    """Returns (state_code, pan, state_name) if format is valid."""
    clean = gstin.strip().upper()
    if not validate_gstin_format(clean):
        return None
    state_code = clean[:2]
    pan = clean[2:12]
    state_name = GST_STATE_CODES.get(state_code, "Unknown")
    return state_code, pan, state_name
