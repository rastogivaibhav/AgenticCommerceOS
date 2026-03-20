"""Rate limiting middleware for ACOS — FIX-05.

Uses slowapi (built on limits library) to protect all endpoints.
Limits are configurable via environment variables.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# ── Limits (configurable via env) ─────────────────────────────────────────────
JOURNEY_LIMIT = os.environ.get("RATE_LIMIT_JOURNEY", "60/minute")
OPS_LIMIT = os.environ.get("RATE_LIMIT_OPS", "120/minute")
REPLAY_LIMIT = os.environ.get("RATE_LIMIT_REPLAY", "10/minute")

limiter = Limiter(key_func=get_remote_address, default_limits=[OPS_LIMIT])


def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a clean 429 with no internal detail."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "retry_after": str(exc.limit.reset_time) if hasattr(exc.limit, "reset_time") else "60s",
        },
        headers={"Retry-After": "60"},
    )
