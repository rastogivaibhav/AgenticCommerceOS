"""Startup-time configuration validation."""

import os


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_non_dev(environment: str) -> bool:
    normalized = (environment or "").strip().lower()
    return normalized not in {"dev", "development", "local", "test", "testing"}


def validate_auth_configuration(service: str, environment: str) -> None:
    """Fail startup for non-dev environments with missing or unsafe auth config."""
    if not _is_non_dev(environment):
        return

    issues = []

    if _env_flag_enabled("ALLOW_INSECURE_DEV_AUTH"):
        issues.append("ALLOW_INSECURE_DEV_AUTH must be disabled outside dev/test")

    if service == "shopper-api":
        if not os.environ.get("SHOPPER_API_KEYS", "").strip():
            issues.append("SHOPPER_API_KEYS is required for shopper-api in non-dev environments")
    elif service == "ops-api":
        if not os.environ.get("OPS_JWT_SECRET", "").strip():
            issues.append("OPS_JWT_SECRET is required for ops-api in non-dev environments")
    elif service == "chat-api":
        chat_secret = (
            os.environ.get("CHAT_JWT_SECRET", "").strip()
            or os.environ.get("OPS_JWT_SECRET", "").strip()
        )
        if not chat_secret:
            issues.append("CHAT_JWT_SECRET or OPS_JWT_SECRET is required for chat-api in non-dev environments")
        if not os.environ.get("SLACK_SIGNING_SECRET", "").strip():
            issues.append("SLACK_SIGNING_SECRET is required for chat-api in non-dev environments")

    if issues:
        joined = "; ".join(issues)
        raise RuntimeError(f"Startup configuration validation failed: {joined}")
