"""Shopper API – customer-facing endpoints.

Security hardening (Sprint 0):
- FIX-01: API key auth via X-API-Key header
- FIX-02: Pydantic JourneyRequest validates all input fields
- FIX-03: CORS restricted to ALLOWED_ORIGINS env var
"""

import os
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from acosplatform.auth.api_key import require_api_key
from acosplatform.models.requests import JourneyRequest
from acosplatform.db.connection import ensure_schema
from acosplatform.journey.engine import run_journey
from acosplatform.middleware.rate_limit import limiter, rate_limit_error_handler, JOURNEY_LIMIT
from acosplatform.observability.metrics import metrics_endpoint
from slowapi.errors import RateLimitExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ACOS Shopper API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Attach rate limiter (FIX-05)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)

# ── CORS — whitelist only (FIX-03) ────────────────────────────────────────────
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,     # Never combine wildcard with credentials
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)


# ── Global exception handler — no stack traces to caller ──────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.on_event("startup")
def startup():
    logger.info("Shopper API starting up...")
    ensure_schema()
    logger.info("Shopper API ready")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/journey")
@app.post("/v1/journey")   # FIX-15: versioned alias
@limiter.limit(JOURNEY_LIMIT)
def journey(
    request: Request,
    payload: JourneyRequest,              # FIX-02: Pydantic validation
    _key: str = Depends(require_api_key), # FIX-01: Auth required
):
    """Execute a commerce journey (also available at /v1/journey).

    Requires X-API-Key header. All fields are validated — message is capped at
    500 chars, customer_id/order_id must be alphanumeric, tenant_id must be a
    known tenant.
    """
    return run_journey(payload.model_dump())


@app.get("/metrics")
def shopper_metrics():
    """Prometheus metrics scrape endpoint (FIX-18). No auth — scrape from internal network only."""
    return metrics_endpoint()


@app.get("/health")
def health():
    """Shallow health check — no auth required."""
    from acosplatform.db.connection import get_connection
    db_ok = get_connection() is not None
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
        "service": "shopper-api",
        "version": os.environ.get("APP_VERSION", "1.0.0"),
    }
