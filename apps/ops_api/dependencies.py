"""Shared auth and request helpers for the ops API routers."""

from __future__ import annotations

import os
from typing import Any

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from acosplatform.auth.northstar import (
    NorthstarAuthContext,
    authenticate_api_key,
    enforce_tenant,
    require_roles,
)

OPS_ENVIRONMENT = os.environ.get("OPS_ENVIRONMENT", "dev")
DEFAULT_NORTHSTAR_MESSAGE = (
    "I need an outfit for a winter wedding under GBP200, available for pickup near Reading"
)
DEFAULT_A2A_MESSAGE = (
    "I'm buying a cot mattress for a newborn under GBP250, and I need to know "
    "if my previous nursery order can be returned."
)


def require_northstar_api_key(
    x_api_key: str | None = Header(default=None),
) -> NorthstarAuthContext:
    """Optional RBAC guard for north-star pilot endpoints."""
    try:
        return authenticate_api_key(x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def require_northstar_role(context: NorthstarAuthContext, *roles: str) -> None:
    try:
        require_roles(context, *roles)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def tenant_for_context(
    context: NorthstarAuthContext,
    requested_tenant: str | None = None,
) -> str:
    try:
        return enforce_tenant(context, requested_tenant)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


class NorthstarMessageRequest(BaseModel):
    tenant_id: str = "default"
    channel: str = "web"
    channel_user_id: str = "demo-user"
    text: str
    customer_id: str | None = None
    conversation_session_id: str | None = None
    journey_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    expires_in_hours: int | None = 72
