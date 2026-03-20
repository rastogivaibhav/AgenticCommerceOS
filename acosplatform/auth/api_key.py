"""Authentication helpers — API key (Shopper API) and JWT Bearer (Ops API)."""

import os
import logging
from fastapi import Security, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── API Key (Shopper API) ──────────────────────────────────────────────────────

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def _get_valid_api_keys() -> set:
    """Load valid shopper API keys from environment (comma-separated)."""
    raw = os.environ.get("SHOPPER_API_KEYS", "")
    if not raw:
        # Development fallback — logs a warning so it's visible
        logger.warning("SHOPPER_API_KEYS not set — using dev-only key 'dev-key-insecure'")
        return {"dev-key-insecure"}
    return {k.strip() for k in raw.split(",") if k.strip()}


async def require_api_key(api_key: str = Security(_API_KEY_HEADER)) -> str:
    """FastAPI dependency — validates X-API-Key header."""
    if api_key not in _get_valid_api_keys():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key


# ── JWT Bearer (Ops API) ───────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)

_JWT_SECRET = os.environ.get("OPS_JWT_SECRET", "")
_JWT_ALGORITHM = "HS256"


def _decode_jwt(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    try:
        import jwt  # PyJWT
        if not _JWT_SECRET:
            logger.warning("OPS_JWT_SECRET not set — JWT auth is DISABLED (dev mode)")
            return {"sub": "dev-user", "role": "admin"}
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except Exception as exc:
        logger.warning(f"JWT decode failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_ops_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """FastAPI dependency — validates Bearer JWT for Ops endpoints."""
    return _decode_jwt(credentials.credentials)
