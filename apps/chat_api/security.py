"""Security helpers for chat-api auth and Slack signature validation."""

import hashlib
import hmac
import logging
import os
import time
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_JWT_ALGORITHM = "HS256"
_SLACK_SIGNATURE_VERSION = "v0"
_SLACK_MAX_SKEW_SECONDS = 300
_bearer = HTTPBearer(auto_error=True)


def _is_non_dev(environment: str) -> bool:
    normalized = (environment or "").strip().lower()
    return normalized not in {"dev", "development", "local", "test", "testing"}


def _current_environment() -> str:
    return os.environ.get("OPS_ENVIRONMENT", "dev")


def _chat_jwt_secret() -> str:
    return (
        os.environ.get("CHAT_JWT_SECRET", "").strip()
        or os.environ.get("OPS_JWT_SECRET", "").strip()
    )


def _decode_chat_jwt(token: str) -> dict:
    secret = _chat_jwt_secret()
    if not secret:
        if _is_non_dev(_current_environment()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Chat authentication is not configured",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.warning(
            "CHAT_JWT_SECRET/OPS_JWT_SECRET not set in dev/test; accepting bearer token without signature verification"
        )
        return {"sub": "chat-dev", "role": "service", "mode": "dev-bypass"}

    try:
        import jwt  # PyJWT

        return jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
    except Exception as exc:
        logger.warning("Chat JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_chat_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Require and validate bearer auth for chat-api protected routes."""
    return _decode_chat_jwt(credentials.credentials)


def verify_slack_signature(request: Request, raw_body: bytes) -> None:
    """Validate Slack request signature for Slack-originated traffic."""
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "").strip()
    if not signing_secret:
        if _is_non_dev(_current_environment()):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Slack signing secret is not configured",
            )
        logger.warning("SLACK_SIGNING_SECRET is not set in dev/test; skipping Slack signature enforcement")
        return

    signature = request.headers.get("X-Slack-Signature", "").strip()
    timestamp_raw = request.headers.get("X-Slack-Request-Timestamp", "").strip()
    if not signature or not timestamp_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Slack signature headers",
        )

    try:
        timestamp = int(timestamp_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Slack request timestamp",
        )

    if abs(int(time.time()) - timestamp) > _SLACK_MAX_SKEW_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Slack request timestamp is stale",
        )

    signature_base = f"{_SLACK_SIGNATURE_VERSION}:{timestamp_raw}:".encode("utf-8") + raw_body
    computed = hmac.new(signing_secret.encode("utf-8"), signature_base, hashlib.sha256).hexdigest()
    expected = f"{_SLACK_SIGNATURE_VERSION}={computed}"

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Slack request signature",
        )
