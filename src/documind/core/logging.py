import logging
import re
import structlog
from typing import Any

# Regex to mask bank account numbers (keeping last 4 digits) and GSTIN/PAN strings
ACCOUNT_REGEX = re.compile(r"\b(\d{6,14})(\d{4})\b")


def mask_sensitive_data(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            event_dict[key] = ACCOUNT_REGEX.sub(r"******\2", value)
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_sensitive_data,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level.upper())),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "documind") -> structlog.BoundLogger:
    return structlog.get_logger(name)
