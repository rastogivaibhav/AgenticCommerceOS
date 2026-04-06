"""Chat Gateway API – Slack integration and message handling."""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.chat_api.config import config
from apps.chat_api.routers import message, jobs, workflows

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ACOS Chat Gateway API",
    version=config.version,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)


# Global exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.on_event("startup")
def startup():
    logger.info("Chat Gateway API starting up...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Version: {config.version}")

    if config.slack.is_configured():
        logger.info("Slack integration configured")
    else:
        logger.warning("Slack integration not fully configured (missing SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET)")

    logger.info("Chat Gateway API ready")


# Include routers
app.include_router(message.router)
app.include_router(jobs.router)
app.include_router(workflows.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    slack_configured = config.slack.is_configured()
    return {
        "status": "ok",
        "service": "chat-api",
        "environment": config.environment,
        "version": config.version,
        "slack_configured": slack_configured,
    }
