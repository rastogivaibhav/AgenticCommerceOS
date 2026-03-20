"""Prompt injection detection and message sanitization for ADK prompts."""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate prompt injection attempts
_INJECTION_RE = re.compile(
    r"(ignore\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|prompts?|context)|"
    r"you\s+are\s+now\s+a|"
    r"new\s+instructions?:|"
    r"disregard\s+(the\s+)?(above|previous|all)|"
    r"forget\s+(everything|all\s+previous)|"
    r"act\s+as\s+(if\s+you\s+are|a\s+different)|"
    r"system\s*prompt|"
    r"reveal\s+(your|the)\s+(instructions?|system|prompt)|"
    r"print\s+(your|the)\s+(system|instructions?))",
    re.IGNORECASE,
)

_MAX_MESSAGE_LENGTH = 500  # hard cap — matches Pydantic model


def sanitize_user_message(message: str) -> str:
    """
    Sanitize a user-supplied message before embedding in an LLM prompt.

    - Truncates to _MAX_MESSAGE_LENGTH chars
    - Replaces detected injection patterns with a safe placeholder
    - Strips null bytes and control characters
    """
    # Strip null bytes and non-printable control chars (keep newlines/tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", message)

    # Hard length cap
    cleaned = cleaned[:_MAX_MESSAGE_LENGTH]

    # Injection detection
    if _INJECTION_RE.search(cleaned):
        logger.warning(f"Prompt injection attempt detected — message suppressed. Original: {message[:80]!r}")
        return "[message filtered by safety policy]"

    return cleaned
