"""Authentication helpers — API key (Shopper API) and JWT Bearer (Ops API)."""

import os
import logging
from typing import Iterable
from fastapi import Security, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── API Key (Shopper API) ──────────────────────────────────────────────────────

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _allow_insecure_dev_auth() -> bool:
    """Opt-in local dev bypass. Never enable this in staging/production."""
    return _env_flag_enabled("ALLOW_INSECURE_DEV_AUTH")


def _get_valid_api_keys() -> set:
    """Load valid shopper API keys from environment (comma-separated)."""
    raw = os.environ.get("SHOPPER_API_KEYS", "").strip()
    if raw:
        return {k.strip() for k in raw.split(",") if k.strip()}
    if _allow_insecure_dev_auth():
        logger.warning("SHOPPER_API_KEYS not set — ALLOW_INSECURE_DEV_AUTH enabled (dev-only)")
        return {"dev-key-insecure"}
    logger.error("SHOPPER_API_KEYS not set and insecure dev auth is disabled")
    return set()


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

_JWT_ALGORITHM = "HS256"


def _decode_jwt(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    jwt_secret = os.environ.get("OPS_JWT_SECRET", "").strip()
    if not jwt_secret:
        if _allow_insecure_dev_auth():
            logger.warning("OPS_JWT_SECRET not set — ALLOW_INSECURE_DEV_AUTH enabled (dev-only)")
            return {"sub": "dev-user", "role": "admin"}
        logger.error("OPS_JWT_SECRET not set and insecure dev auth is disabled")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ops authentication is not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        import jwt  # PyJWT
        payload = jwt.decode(token, jwt_secret, algorithms=[_JWT_ALGORITHM])
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


def _extract_roles(token_payload: dict) -> set[str]:
    roles: set[str] = set()

    role = token_payload.get("role")
    if isinstance(role, str) and role.strip():
        roles.add(role.strip().lower())

    claim_roles = token_payload.get("roles")
    if isinstance(claim_roles, str):
        roles.update({r.strip().lower() for r in claim_roles.split(",") if r.strip()})
    elif isinstance(claim_roles, Iterable) and not isinstance(claim_roles, dict):
        roles.update({str(r).strip().lower() for r in claim_roles if str(r).strip()})

    realm_access = token_payload.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles", [])
        if isinstance(realm_roles, Iterable) and not isinstance(realm_roles, dict):
            roles.update({str(r).strip().lower() for r in realm_roles if str(r).strip()})

    return roles


def require_ops_roles(*allowed_roles: str):
    """Return a dependency that enforces role-based access for ops endpoints."""
    required = {r.strip().lower() for r in allowed_roles if r and r.strip()}

    async def _role_dependency(token: dict = Depends(require_ops_token)) -> dict:
        if not required:
            return token
        token_roles = _extract_roles(token)
        if token_roles.isdisjoint(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required one of: {sorted(required)}",
            )
        return token

    return _role_dependency
