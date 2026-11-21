import json
import re
from typing import Any, Tuple, Type, TypeVar

try:
    from pydantic import BaseModel, ValidationError

    def parse_and_validate(raw_text: str, schema_cls: Any) -> Tuple[bool, Any | None, str | None]:
        clean_json_str = extract_json_string(raw_text)
        try:
            data = json.loads(clean_json_str)
        except Exception as e:
            return False, None, f"JSON parse error: {str(e)}"

        if not isinstance(data, dict):
            return False, None, "Expected JSON object at root level, got array or primitive"

        try:
            instance = schema_cls.model_validate(data)
            return True, instance, None
        except ValidationError as ve:
            return False, None, f"Pydantic validation errors:\n{ve.json(indent=2)}"

except ImportError:
    def parse_and_validate(raw_text: str, schema_cls: Any) -> Tuple[bool, Any | None, str | None]:  # type: ignore[no-redef]
        clean_json_str = extract_json_string(raw_text)
        try:
            data = json.loads(clean_json_str)
            instance = schema_cls.model_validate(data) if hasattr(schema_cls, "model_validate") else data
            return True, instance, None
        except Exception as e:
            return False, None, str(e)


JSON_BLOCK_REGEX = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")


def extract_json_string(text: str) -> str:
    """Extracts raw JSON payload from markdown fences or bare text."""
    match = JSON_BLOCK_REGEX.search(text)
    if match:
        return match.group(1).strip()
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()
    return text.strip()


def create_repair_prompt(invalid_raw: str, error_msg: str, doc_type: str) -> str:
    """Creates a targeted prompt for one-shot JSON repair."""
    return f"""Your previous JSON output for doc_type '{doc_type}' was invalid.

Error Details:
{error_msg}

Original Output:
{invalid_raw}

Task: Return ONLY valid, corrected JSON matching the schema with null for absent fields. No explanatory prose.
"""
