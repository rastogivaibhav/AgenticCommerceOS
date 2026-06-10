"""Ops API for ACOS control-plane operations."""

import json
import logging
import os
from io import BytesIO
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import requests
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded

from acosplatform.audit.logger import audit
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.config.startup_validation import validate_auth_configuration
from acosplatform.billing.engine import get_cost_summary, get_usage
from acosplatform.db.connection import ensure_schema, check_connection
from acosplatform.db.repository import (
    find_crm_customer_by_phone,
    get_channel_binding,
    get_channel_bindings,
    get_channel_pairing,
    get_channel_pairing_by_route,
    get_channel_pairings,
    get_channel_sender_by_external_id,
    get_channel_senders,
    get_crm_cases,
    get_crm_customer_by_id,
    get_crm_customers,
    get_demo_route,
    get_demo_routes,
    get_events,
    get_orders_for_customer,
    get_product_by_id,
    get_products,
    get_run,
    get_runs,
    get_runs_by_workflow,
    get_agents,
    get_agent_by_id,
    get_skills,
    get_skill_by_id,
    save_channel_binding,
    save_channel_pairing,
    save_channel_sender,
    save_crm_case,
    save_crm_customer,
    save_demo_route,
    save_agent,
    save_skill,
    save_audit_event,
    save_run,
)
from acosplatform.journey.engine import run_journey
from acosplatform.evaluation.scorer import get_experiment_results
from acosplatform.middleware.rate_limit import REPLAY_LIMIT, limiter, rate_limit_error_handler
from acosplatform.models.workflows import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowPromotionRequest,
    WorkflowRollbackRequest,
    WorkflowVersionCreateRequest,
)
from acosplatform.observability.metrics import metrics_endpoint, record_api_error
from acosplatform.retail_ops.service import dispatch_demo_route, ingest_channel_message
from acosplatform.replay.replay_engine import replay
from integrations.adk.provider import (
    DEFAULT_MODEL,
    RUNTIME_PREFERENCE_OPTIONS,
    SUPPORTED_RUNTIME_PROVIDERS,
    get_runtime_capabilities,
    run_adk,
)
from integrations.salesforce.client import execute_salesforce_action, probe_salesforce
from integrations.shopify.client import execute_shopify_action, probe_shopify_admin
from integrations.telegram.client import probe_telegram_bot, send_telegram_message
from integrations.whatsapp.client import execute_whatsapp_action, probe_whatsapp_cloud, verify_whatsapp_webhook
from acosplatform.workflows.service import (
    DEMO_WORKFLOW_ID,
    approve_workflow_version,
    archive_workflow,
    create_workflow_draft,
    create_workflow_version,
    ensure_default_workflow_registry,
    get_workflow_detail,
    list_workflows_with_state,
    promote_workflow_version,
    rollback_workflow_version,
)
from acosplatform.workflows.executor import execute_saved_workflow
from apps.ops_api.routers import experiments, analytics, promotions, runs, approvals, incidents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
OPS_ENVIRONMENT = os.environ.get("OPS_ENVIRONMENT", "dev")
EMBEDDED_UI_DIR = Path("apps/ops_api/ui")
LOCAL_UI_DIR = Path("apps/ops_ui_v2/dist")
UI_DIR = EMBEDDED_UI_DIR if (EMBEDDED_UI_DIR / "index.html").exists() else LOCAL_UI_DIR
SUPPORTED_PLATFORM_MODES = ("normal", "demo")


def _flag_enabled(name: str, default: str = "0") -> bool:
    value = os.environ.get(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


IS_DEV_ENV = OPS_ENVIRONMENT.strip().lower() in {"dev", "development", "local", "test", "testing"}
ALLOW_MOCK_ROUTES = _flag_enabled("ALLOW_MOCK_ROUTES", "0")
ALLOW_NON_DEV_MOCK_ROUTES = _flag_enabled("ALLOW_NON_DEV_MOCK_ROUTES", "0")

app = FastAPI(
    title="ACOS Ops API",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)

_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(experiments.router)
app.include_router(analytics.router)
app.include_router(promotions.router)
app.include_router(promotions.approvals_router)
app.include_router(promotions.audit_router)
app.include_router(runs.router)
app.include_router(approvals.router)
app.include_router(incidents.router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    record_api_error(exc.__class__.__name__, request.url.path)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.on_event("startup")
def startup():
    logger.info("Ops API starting up...")
    _set_platform_mode(os.environ.get("ACOS_PLATFORM_MODE", "normal"))
    _set_runtime_preference(os.environ.get("ACOS_RUNTIME_PREFERENCE", "auto"))
    if ALLOW_MOCK_ROUTES and not IS_DEV_ENV and not ALLOW_NON_DEV_MOCK_ROUTES:
        raise RuntimeError(
            "ALLOW_MOCK_ROUTES=1 is blocked in non-dev unless ALLOW_NON_DEV_MOCK_ROUTES=1 is also set."
        )
    if ALLOW_MOCK_ROUTES and not IS_DEV_ENV:
        logger.warning("Mock/test routes are enabled in non-dev environment.")
    validate_auth_configuration(service="ops-api", environment=OPS_ENVIRONMENT)
    ensure_schema()
    ensure_default_workflow_registry(environment=OPS_ENVIRONMENT)
    _seed_demo_routes()
    logger.info("Ops API ready")


def _actor(token: dict) -> str:
    return token.get("sub") or token.get("email") or "ops-user"


READ_ACCESS = require_ops_roles("admin", "ops", "analyst")
OPERATE_ACCESS = require_ops_roles("admin", "ops")
ADMIN_ACCESS = require_ops_roles("admin")


class CanvasSaveRequest(BaseModel):
    step_definitions: dict


class AgentTestRequest(BaseModel):
    message: str = "Check order status for ORD-1001"
    tenant_id: str = "default"
    customer_id: str = "ops-test-customer"
    journey_type: str = "post_purchase"


class SkillTestRequest(BaseModel):
    input_payload: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default"
    workflow_id: str | None = None
    workflow_version: str | None = None


class BindSkillRequest(BaseModel):
    skill_id: str


class SandboxScenarioRequest(BaseModel):
    tenant_id: str = "default"
    customer_id: str = "sandbox-customer"
    environment_id: str = "dev"
    write_evidence: bool = True


class WorkflowTestRunRequest(BaseModel):
    tenant_id: str = "default"
    environment: str = OPS_ENVIRONMENT
    message: str = "Where is my order ORD-1001?"
    input: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecuteRequest(BaseModel):
    tenant_id: str = "default"
    customer_id: str = "cust_1001"
    environment: str = OPS_ENVIRONMENT
    message: str = "Where is my order ORD-1001?"
    order_id: str | None = None


class RuntimePreferencesRequest(BaseModel):
    platform_mode: str | None = None
    runtime_preference: str | None = None


class ChannelLinkRequest(BaseModel):
    id: str | None = None
    type: str
    tenant_id: str = "default"
    environment: str = OPS_ENVIRONMENT
    identity: str = ""
    default_route: str = "order_status"
    allowed_routes: list[str] = Field(default_factory=lambda: ["order_status", "return_refund", "loyalty_rewards", "vip_escalation"])
    notification_targets: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChannelTestRequest(BaseModel):
    text: str = "ACOS channel test"
    recipient: str = ""
    binding_id: str | None = None


class ChannelPairingRequest(BaseModel):
    route_id: str
    expires_in_hours: int | None = 72


class SenderApprovalRequest(BaseModel):
    customer_id: str | None = None
    display_name: str | None = None


class DemoRouteDispatchRequest(BaseModel):
    message: str = "Where is my order ORD-1001?"
    channel_binding_id: str = "whatsapp-support"
    sender_external_id: str = "whatsapp:+447700900001"
    display_name: str = "Demo Customer"
    tenant_id: str = "default"
    environment: str = OPS_ENVIRONMENT


class CRMCaseCreateRequest(BaseModel):
    customer_id: str
    subject: str
    summary: str = ""
    status: str = "open"
    priority: str = "medium"
    channel: str = "whatsapp"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _runtime_capabilities() -> dict[str, Any]:
    if getattr(app.state, "runtime_preference", None):
        os.environ["ACOS_RUNTIME_PREFERENCE"] = app.state.runtime_preference
    return get_runtime_capabilities()


def _platform_mode() -> str:
    raw_value = getattr(app.state, "platform_mode", None) or os.environ.get("ACOS_PLATFORM_MODE") or "normal"
    normalized = str(raw_value).strip().lower()
    return normalized if normalized in SUPPORTED_PLATFORM_MODES else "normal"


def _data_plane_mode() -> str:
    try:
        return "live" if check_connection() else "demo"
    except Exception:
        return "demo"


def _runtime_preference() -> str:
    raw_value = getattr(app.state, "runtime_preference", None) or os.environ.get("ACOS_RUNTIME_PREFERENCE") or "auto"
    normalized = str(raw_value).strip().lower()
    if normalized in {"", "auto"}:
        return "auto"
    normalized = _PROVIDER_ALIAS.get(normalized, normalized)
    return normalized if normalized in SUPPORTED_RUNTIME_PROVIDERS else "auto"


def _set_platform_mode(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in SUPPORTED_PLATFORM_MODES:
        raise ValueError(f"Unsupported platform mode '{value}'. Expected one of: {', '.join(SUPPORTED_PLATFORM_MODES)}")
    app.state.platform_mode = normalized
    os.environ["ACOS_PLATFORM_MODE"] = normalized
    return normalized


def _set_runtime_preference(value: str) -> str:
    normalized = _runtime_preference() if value is None else str(value or "").strip().lower()
    if normalized in {"", "auto"}:
        normalized = "auto"
    else:
        normalized = _PROVIDER_ALIAS.get(normalized, normalized)
    if normalized != "auto" and normalized not in SUPPORTED_RUNTIME_PROVIDERS:
        raise ValueError(
            f"Unsupported runtime preference '{value}'. Expected one of: {', '.join(RUNTIME_PREFERENCE_OPTIONS)}"
        )
    app.state.runtime_preference = normalized
    os.environ["ACOS_RUNTIME_PREFERENCE"] = normalized
    return normalized


def _roles_from_claims(claims: dict[str, Any]) -> list[str]:
    roles: set[str] = set()
    role = claims.get("role")
    if isinstance(role, str) and role.strip():
        roles.add(role.strip().lower())
    claim_roles = claims.get("roles")
    if isinstance(claim_roles, str):
        roles.update({item.strip().lower() for item in claim_roles.split(",") if item.strip()})
    elif isinstance(claim_roles, list):
        roles.update({str(item).strip().lower() for item in claim_roles if str(item).strip()})
    realm_access = claims.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles")
        if isinstance(realm_roles, list):
            roles.update({str(item).strip().lower() for item in realm_roles if str(item).strip()})
    return sorted(roles)


def _attach_provenance(records: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    return [{**record, "provenance_mode": mode} for record in records]


def _connector_bindings(environment: str = OPS_ENVIRONMENT) -> list[dict[str, Any]]:
    stored_channels = {
        binding.get("id"): binding
        for binding in get_channel_bindings()
        if binding.get("environment") in {environment, OPS_ENVIRONMENT}
    }

    shopify_probe = probe_shopify_admin({"probe": "shop"}, timeout_seconds=1.5, retries=0)
    shopify_status = "healthy" if shopify_probe.get("status") == "ok" else "sandbox"
    shopify_mode = "live" if shopify_probe.get("status") == "ok" else "sandbox"
    salesforce_probe = probe_salesforce(timeout_seconds=1.5)
    salesforce_status = "healthy" if salesforce_probe.get("status") == "ok" else "sandbox"
    salesforce_mode = "live" if salesforce_probe.get("status") == "ok" else "sandbox"
    whatsapp_probe = probe_whatsapp_cloud(
        timeout_seconds=1.5,
        config_override=(stored_channels.get("whatsapp-support") or {}).get("metadata"),
    )
    whatsapp_status = "healthy" if whatsapp_probe.get("status") == "ok" else "sandbox"
    whatsapp_mode = "live" if whatsapp_probe.get("status") == "ok" else "sandbox"
    telegram_probe = probe_telegram_bot(
        timeout_seconds=1.5,
        config_override=(stored_channels.get("telegram-ops") or {}).get("metadata"),
    )
    telegram_status = "healthy" if telegram_probe.get("status") == "ok" else "sandbox"
    telegram_mode = "live" if telegram_probe.get("status") == "ok" else "sandbox"
    shopify_details = {
        "id": "shopify-primary",
        "connector_type": "shopify",
        "display_name": "Shopify Primary Store",
        "environment": environment,
        "status": shopify_status,
        "mode": shopify_mode,
        "supported_actions": [
            "get_order",
            "get_customer",
            "get_product",
            "create_return_intent",
        ],
    }
    if shopify_probe.get("store_domain"):
        shopify_details["store_domain"] = shopify_probe["store_domain"]
    if shopify_probe.get("api_version"):
        shopify_details["api_version"] = shopify_probe["api_version"]

    return [
        shopify_details,
        {
            "id": "salesforce-support",
            "connector_type": "salesforce",
            "display_name": "Salesforce Support Cloud",
            "environment": environment,
            "status": salesforce_status,
            "mode": salesforce_mode,
            "supported_actions": ["get_contact", "get_case", "create_case", "update_case"],
            "instance_url": salesforce_probe.get("instance_url"),
            "api_version": salesforce_probe.get("api_version"),
        },
        {
            "id": "whatsapp-support",
            "connector_type": "whatsapp",
            "display_name": "WhatsApp Support Inbox",
            "environment": environment,
            "status": whatsapp_status,
            "mode": whatsapp_mode,
            "supported_actions": [
                "inbound_message_trigger",
                "send_message",
                "send_template_message",
                "handoff_tag",
            ],
            "phone_number_id": whatsapp_probe.get("phone_number_id"),
            "display_phone_number": whatsapp_probe.get("display_phone_number"),
            "verified_name": whatsapp_probe.get("verified_name"),
        },
        {
            "id": "telegram-ops",
            "connector_type": "telegram",
            "display_name": "Telegram Ops Bot",
            "environment": environment,
            "status": telegram_status,
            "mode": telegram_mode,
            "supported_actions": ["send_message", "webhook_update"],
            "bot_username": telegram_probe.get("username"),
            "default_chat_id": telegram_probe.get("default_chat_id"),
        },
        {
            "id": "commerce-ops",
            "connector_type": "commerce",
            "display_name": "Commerce Ops Adapter",
            "environment": environment,
            "status": "sandbox",
            "mode": "sandbox",
            "supported_actions": ["lookup_policy", "manual_review", "create_note"],
        },
    ]


def _whatsapp_binding_overrides() -> list[dict[str, Any]]:
    overrides = []
    for binding in get_channel_bindings():
        if binding.get("type") != "whatsapp":
            continue
        metadata = binding.get("metadata") or {}
        if metadata.get("verify_token"):
            overrides.append(metadata)
    return overrides


def _runtime_health() -> dict[str, Any]:
    capabilities = _runtime_capabilities()
    return {
        "platform_mode": _platform_mode(),
        "data_mode": _data_plane_mode(),
        "runtime_preference": _runtime_preference(),
        "providers": capabilities,
        "lmstudio": {
            "enabled": capabilities.get("lmstudio_enabled", False),
            "base_url": capabilities.get("lmstudio_base_url"),
            "model": capabilities.get("lmstudio_model"),
        },
        "local_openai_profiles": capabilities.get("local_openai_profiles", {}),
    }


def _seed_demo_routes() -> None:
    canonical_routes = [
        {
            "id": "order_status",
            "name": "Order Status",
            "description": "Track the latest order, explain shipment state, and notify ops.",
            "workflow_id": DEMO_WORKFLOW_ID,
            "workflow_family": "service",
            "supported_channels": ["whatsapp", "telegram"],
            "sample_trigger": "Where is my order ORD-1001?",
            "systems": ["crm", "shopify", "salesforce", "whatsapp", "telegram"],
            "preferred_runtime": "local_openai_host",
            "mode": "sandbox",
        },
        {
            "id": "return_refund",
            "name": "Return / Refund",
            "description": "Prepare a return intent, summarize policy, and escalate when needed.",
            "workflow_id": "wf-service",
            "workflow_family": "service",
            "supported_channels": ["whatsapp", "telegram"],
            "sample_trigger": "I want to return my last order.",
            "systems": ["crm", "shopify", "salesforce", "telegram"],
            "preferred_runtime": "local_fallback",
            "mode": "sandbox",
        },
        {
            "id": "loyalty_rewards",
            "name": "Loyalty Rewards",
            "description": "Retrieve loyalty tier and available benefits before replying.",
            "workflow_id": "wf-engagement",
            "workflow_family": "engagement",
            "supported_channels": ["whatsapp", "telegram"],
            "sample_trigger": "Do I have any loyalty rewards?",
            "systems": ["crm", "salesforce", "telegram"],
            "preferred_runtime": "local_fallback",
            "mode": "sandbox",
        },
        {
            "id": "vip_escalation",
            "name": "VIP Escalation",
            "description": "Escalate priority cases for high-value customers and notify ops.",
            "workflow_id": DEMO_WORKFLOW_ID,
            "workflow_family": "service",
            "supported_channels": ["whatsapp", "telegram"],
            "sample_trigger": "This is my third failed delivery, escalate now.",
            "systems": ["crm", "salesforce", "whatsapp", "telegram"],
            "preferred_runtime": "local_openai_host",
            "mode": "sandbox",
        },
    ]
    for route in canonical_routes:
        save_demo_route(route)


def _sanitize_phone_digits(value: str) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _normalize_whatsapp_sender_external_id(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("whatsapp:"):
        raw = raw.split(":", 1)[1]
    digits = _sanitize_phone_digits(raw)
    if digits:
        return f"whatsapp:+{digits}"
    return f"whatsapp:{raw}" if raw else "whatsapp:unknown"


def _resolve_whatsapp_binding(value: dict[str, Any] | None) -> dict[str, Any] | None:
    candidates = [binding for binding in get_channel_bindings() if binding.get("type") == "whatsapp"]
    if not candidates:
        return get_channel_binding("whatsapp-support")

    metadata = (value or {}).get("metadata") or {}
    incoming_phone_number_id = str(metadata.get("phone_number_id") or "").strip()
    incoming_display_phone = _sanitize_phone_digits(metadata.get("display_phone_number") or "")

    if incoming_phone_number_id:
        for binding in candidates:
            binding_metadata = binding.get("metadata") or {}
            if str(binding_metadata.get("phone_number_id") or "").strip() == incoming_phone_number_id:
                return binding

    if incoming_display_phone:
        for binding in candidates:
            binding_metadata = binding.get("metadata") or {}
            known_numbers = [
                binding_metadata.get("display_phone_number"),
                binding_metadata.get("start_chat_number"),
                binding_metadata.get("default_recipient"),
            ]
            if incoming_display_phone in {_sanitize_phone_digits(item) for item in known_numbers if item}:
                return binding

    return next((binding for binding in candidates if binding.get("id") == "whatsapp-support"), candidates[0])


def _whatsapp_contact_directory(value: dict[str, Any] | None) -> dict[str, str]:
    directory: dict[str, str] = {}
    contacts = (value or {}).get("contacts") or []
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        name = (
            ((contact.get("profile") or {}).get("name"))
            or contact.get("wa_id")
            or contact.get("input")
            or "WhatsApp sender"
        )
        for key in (contact.get("wa_id"), contact.get("input")):
            digits = _sanitize_phone_digits(key or "")
            if digits:
                directory[digits] = str(name)
    return directory


def _extract_whatsapp_message_text(message: dict[str, Any] | None) -> str:
    payload = message or {}
    text_body = ((payload.get("text") or {}).get("body") or "").strip()
    if text_body:
        return text_body

    button_text = ((payload.get("button") or {}).get("text") or "").strip()
    if button_text:
        return button_text

    interactive = payload.get("interactive") or {}
    for key in ("button_reply", "list_reply"):
        reply = interactive.get(key) or {}
        title = str(reply.get("title") or "").strip()
        reply_id = str(reply.get("id") or "").strip()
        description = str(reply.get("description") or "").strip()
        parts = [part for part in (title, description, reply_id) if part]
        if parts:
            return " | ".join(parts)

    for field in ("caption",):
        value = str(payload.get(field) or "").strip()
        if value:
            return value

    return ""


def _record_whatsapp_webhook_event(
    *,
    action: str,
    binding: dict[str, Any] | None,
    resource_id: str,
    payload: dict[str, Any],
) -> None:
    try:
        save_audit_event(
            "whatsapp-webhook",
            action,
            "channel_binding",
            (binding or {}).get("id") or resource_id,
            tenant_id=(binding or {}).get("tenant_id") or "default",
            environment_id=(binding or {}).get("environment") or OPS_ENVIRONMENT,
            payload=payload,
        )
    except Exception as exc:
        logger.warning("Failed to save WhatsApp audit event: %s", exc)


def _build_whatsapp_pairing_link(binding: dict[str, Any], pair_code: str) -> str:
    metadata = binding.get("metadata") or {}
    chat_number = (
        metadata.get("start_chat_number")
        or metadata.get("display_phone_number")
        or metadata.get("default_recipient")
        or ""
    )
    digits = _sanitize_phone_digits(chat_number)
    if not digits:
        return ""
    message = f"PAIR {pair_code}"
    return f"https://wa.me/{digits}?text={quote(message)}"


def _build_telegram_pairing_link(binding: dict[str, Any], pair_code: str) -> str:
    metadata = binding.get("metadata") or {}
    username = str(metadata.get("bot_username") or "").strip().lstrip("@")
    if not username:
        return ""
    return f"https://t.me/{username}?start=pair_{pair_code}"


def _build_pairing_start_link(binding: dict[str, Any], pair_code: str) -> str:
    channel_type = (binding.get("type") or "").strip().lower()
    if channel_type == "telegram":
        return _build_telegram_pairing_link(binding, pair_code)
    if channel_type == "whatsapp":
        return _build_whatsapp_pairing_link(binding, pair_code)
    return ""


def _build_pairing_payload(binding: dict[str, Any], route: dict[str, Any], pairing: dict[str, Any], request: Request) -> dict[str, Any]:
    base_url = str(request.base_url).rstrip("/")
    start_link = _build_pairing_start_link(binding, pairing.get("pair_code", ""))
    qr_url = f"{base_url}/api/v1/channels/pairings/{pairing.get('id')}/qr.svg"
    return {
        **pairing,
        "channel_type": binding.get("type"),
        "binding_identity": binding.get("identity") or binding.get("id"),
        "route_name": route.get("name") or route.get("id"),
        "sample_trigger": (pairing.get("metadata") or {}).get("sample_trigger") or route.get("sample_trigger") or "",
        "start_link": start_link,
        "manual_pair_text": f"PAIR {pairing.get('pair_code')}",
        "qr_url": qr_url,
        "pairing_mode": "scan_to_start",
        "start_ready": bool(start_link),
    }


def _ensure_channel_pairing(binding: dict[str, Any], route: dict[str, Any], request: Request, expires_in_hours: int = 72) -> dict[str, Any]:
    existing = get_channel_pairing_by_route(binding.get("id"), route.get("id"))
    if existing:
        return _build_pairing_payload(binding, route, existing, request)

    pair_code = uuid4().hex[:8].upper()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=max(int(expires_in_hours or 72), 1))
    saved = save_channel_pairing(
        {
            "id": f"pair-{uuid4().hex[:10]}",
            "channel_binding_id": binding.get("id"),
            "route_id": route.get("id"),
            "pair_code": pair_code,
            "status": "active",
            "metadata": {
                "channel_type": binding.get("type"),
                "sample_trigger": route.get("sample_trigger") or "",
            },
            "expires_at": expires_at,
        }
    )
    return _build_pairing_payload(binding, route, saved, request)


def _extract_order_reference(message: str, payload: dict[str, Any]) -> str:
    order_id = str(payload.get("order_id") or "").strip()
    if order_id:
        return order_id
    upper_message = message.upper()
    for token in upper_message.replace("?", " ").replace(",", " ").split():
        if token.startswith("ORD-"):
            return token
    return ""


def _agent_tool_trace(agent: dict[str, Any], message: str, customer_id: str, tenant_id: str) -> list[dict[str, Any]]:
    order_id = _extract_order_reference(message, {"order_id": None}) or (get_crm_customer_by_id(customer_id) or {}).get("last_order_id", "")
    trace: list[dict[str, Any]] = []
    bindings = list(agent.get("connector_bindings") or [])
    if "shopify-primary" in bindings:
        shopify_run = execute_shopify_action("get_order", {"order_id": order_id})
        trace.append(
            {
                "system": "shopify",
                "tool": "get_order",
                "mode": shopify_run.get("mode", "sandbox"),
                "status": shopify_run.get("status", "ok"),
                "note": shopify_run.get("note"),
                "result": shopify_run.get("result"),
            }
        )
    if "salesforce-support" in bindings:
        customer = get_crm_customer_by_id(customer_id)
        salesforce_run = execute_salesforce_action(
            "get_contact",
            {"contact_id": (customer or {}).get("salesforce_contact_id")},
        )
        trace.append(
            {
                "system": "salesforce",
                "tool": "get_contact",
                "mode": salesforce_run.get("mode", "sandbox"),
                "status": salesforce_run.get("status", "ok"),
                "note": salesforce_run.get("note"),
                "result": salesforce_run.get("result"),
            }
        )
    if "whatsapp-support" in bindings:
        whatsapp_run = execute_whatsapp_action(
            "send_message",
            {"to": "+440000000000", "message": f"Agent test for {tenant_id}: {message}"},
            allow_live_send=False,
            config_override=(get_channel_binding("whatsapp-support") or {}).get("metadata"),
        )
        trace.append(
            {
                "system": "whatsapp",
                "tool": "send_message",
                "mode": whatsapp_run.get("mode", "sandbox"),
                "status": whatsapp_run.get("status", "ok"),
                "note": whatsapp_run.get("note"),
                "result": whatsapp_run.get("result"),
            }
        )
    if "telegram-ops" in bindings:
        telegram_run = send_telegram_message(
            f"Agent test for {tenant_id}: {message}",
            chat_id=None,
            config_override=(get_channel_binding("telegram-ops") or {}).get("metadata"),
        )
        trace.append(
            {
                "system": "telegram",
                "tool": "send_message",
                "mode": telegram_run.get("mode", "sandbox"),
                "status": telegram_run.get("status", "ok"),
                "note": telegram_run.get("note"),
                "result": telegram_run.get("result"),
            }
        )
    trace.append(
        {
            "system": "crm",
            "tool": "get_customer_profile",
            "mode": "mock",
            "status": "ok" if get_crm_customer_by_id(customer_id) else "not_found",
            "result": get_crm_customer_by_id(customer_id) or {},
        }
    )
    return trace


def _build_agent_scorecard(agent: dict[str, Any]) -> dict[str, Any]:
    scorecard = dict(agent.get("scorecard") or {})
    scorecard.setdefault("connector_health_status", "unknown")
    scorecard.setdefault("contract_validation_status", "unknown")
    scorecard.setdefault("recent_run_failure_rate", None)
    scorecard.setdefault("last_successful_run_at", None)
    scorecard["last_test_at"] = agent.get("last_test_at")
    scorecard["last_test_status"] = agent.get("last_test_status") or "unknown"
    scorecard["evidence_links"] = [
        {"type": "workflow", "id": workflow_id}
        for workflow_id in list(agent.get("used_by_workflow_ids") or [])
    ]
    return scorecard


def _validate_contract_payload(
    schema: dict[str, Any],
    payload: dict[str, Any],
    *,
    target: str,
) -> list[str]:
    errors: list[str] = []
    if not schema:
        return errors

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    for field_name in required:
        if field_name not in payload:
            errors.append(f"{target}: missing required field '{field_name}'")

    for field_name, definition in properties.items():
        if field_name not in payload:
            continue
        expected_type = definition.get("type")
        python_type = type_map.get(expected_type)
        if python_type and not isinstance(payload[field_name], python_type):
            errors.append(
                f"{target}: field '{field_name}' expected {expected_type}, got {type(payload[field_name]).__name__}"
            )

    return errors


def _write_evidence_file(prefix: str, payload: dict[str, Any]) -> str:
    evidence_dir = Path("deploy/k8s/observability/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-").replace("+00:00", "Z")
    filename = f"{prefix}-{stamp}.json"
    file_path = evidence_dir / filename
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(file_path)


_RETRYABLE_HTTP_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def _build_local_connector_output(
    *,
    skill_id: str,
    execution_mode: str,
    input_payload: dict[str, Any],
    reason: str | None = None,
    degraded: bool = False,
    error: str | None = None,
    attempts: int = 1,
) -> dict[str, Any]:
    connector_meta = {
        "source": "local_fallback",
        "degraded": degraded,
        "attempts": attempts,
        "reason": reason,
        "error": error,
    }
    output_payload = {
        "status": "ok",
        "skill_id": skill_id,
        "execution_mode": execution_mode,
        "echo": input_payload,
        "connector": connector_meta,
    }
    return {
        "connector_source": "local_fallback",
        "degraded": degraded,
        "error": error,
        "attempts": attempts,
        "output_payload": output_payload,
    }


def _run_generic_http_probe(
    *,
    url: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    retries: int,
    headers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    attempts = 0
    max_attempts = max(retries + 1, 1)
    timeout = max(float(timeout_seconds), 0.2)
    last_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers or {},
                timeout=timeout,
            )
            status_code = response.status_code
            if status_code in _RETRYABLE_HTTP_STATUS_CODES and attempt < max_attempts:
                last_error = f"http_{status_code}"
                continue
            if status_code >= 400:
                return {
                    "ok": False,
                    "attempts": attempts,
                    "status_code": status_code,
                    "error": f"HTTP {status_code}",
                }
            try:
                body = response.json() if response.content else {}
            except ValueError:
                return {
                    "ok": False,
                    "attempts": attempts,
                    "status_code": status_code,
                    "error": "remote_response_invalid_json",
                }
            if not isinstance(body, dict):
                return {
                    "ok": False,
                    "attempts": attempts,
                    "status_code": status_code,
                    "error": "remote_response_not_object",
                }
            return {
                "ok": True,
                "attempts": attempts,
                "status_code": status_code,
                "body": body,
            }
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            if attempt < max_attempts:
                continue
            break

    return {
        "ok": False,
        "attempts": attempts,
        "status_code": None,
        "error": last_error or "remote_probe_failed",
    }


def _run_http_connector_skill_test(
    *,
    skill: dict[str, Any],
    input_payload: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any]:
    skill_id = str(skill.get("id") or "unknown")
    execution_mode = "http_connector"
    timeout_seconds = max(_safe_int(skill.get("timeout_seconds", 15), 15), 1)
    retries = max(_safe_int(skill.get("retries", 0), 0), 0)

    tenant_route: dict[str, Any] = {}
    try:
        from acosplatform.tenancy.manager import get_tenant_config

        connectors = (get_tenant_config(tenant_id).get("connectors") or {})
        tenant_route = connectors.get("shopify") or {}
    except Exception:
        tenant_route = {}

    configured_url = (
        str(input_payload.get("connector_url") or "").strip()
        or str(tenant_route.get("url") or tenant_route.get("endpoint") or "").strip()
    )
    route_mode = str(tenant_route.get("mode") or "remote").strip().lower()

    if configured_url and route_mode != "local":
        http_probe = _run_generic_http_probe(
            url=configured_url,
            payload=input_payload,
            timeout_seconds=timeout_seconds,
            retries=retries,
            headers=(tenant_route.get("headers") or {}),
        )
        if http_probe["ok"]:
            output_payload = {
                "status": "ok",
                "skill_id": skill_id,
                "execution_mode": execution_mode,
                "connector_response": http_probe.get("body") or {},
                "connector": {
                    "source": "remote_http",
                    "url": configured_url,
                    "attempts": http_probe.get("attempts", 1),
                    "status_code": http_probe.get("status_code"),
                    "degraded": False,
                },
            }
            return {
                "connector_source": "remote_http",
                "degraded": False,
                "error": None,
                "attempts": http_probe.get("attempts", 1),
                "output_payload": output_payload,
            }
        return _build_local_connector_output(
            skill_id=skill_id,
            execution_mode=execution_mode,
            input_payload=input_payload,
            degraded=True,
            error=http_probe.get("error"),
            reason="remote_connector_failed",
            attempts=http_probe.get("attempts", 1),
        )

    shopify_probe = probe_shopify_admin(
        input_payload,
        timeout_seconds=float(timeout_seconds),
        retries=retries,
    )
    if shopify_probe.get("status") == "ok":
        output_payload = {
            "status": "ok",
            "skill_id": skill_id,
            "execution_mode": execution_mode,
            "connector_response": shopify_probe.get("result") or {},
            "connector": {
                "source": "shopify_admin_api",
                "probe": shopify_probe.get("probe"),
                "store_domain": shopify_probe.get("store_domain"),
                "api_version": shopify_probe.get("api_version"),
                "attempts": shopify_probe.get("attempts", 1),
                "status_code": shopify_probe.get("status_code"),
                "degraded": False,
            },
        }
        return {
            "connector_source": "shopify_admin_api",
            "degraded": False,
            "error": None,
            "attempts": shopify_probe.get("attempts", 1),
            "output_payload": output_payload,
        }

    if shopify_probe.get("status") == "error":
        return _build_local_connector_output(
            skill_id=skill_id,
            execution_mode=execution_mode,
            input_payload=input_payload,
            degraded=True,
            error=shopify_probe.get("error"),
            reason="shopify_probe_failed",
            attempts=int(shopify_probe.get("attempts", 1) or 1),
        )

    return _build_local_connector_output(
        skill_id=skill_id,
        execution_mode=execution_mode,
        input_payload=input_payload,
        degraded=False,
        reason=shopify_probe.get("reason") or "shopify_not_configured",
        attempts=1,
    )


def _run_external_connector_checks(tenant_id: str) -> list[dict[str, Any]]:
    check = probe_shopify_admin({"probe": "shop"})
    status = check.get("status")
    normalized_status = "pass" if status == "ok" else ("skip" if status == "skipped" else "fail")
    return [
        {
            "name": "shopify_admin_api",
            "status": normalized_status,
            "tenant_id": tenant_id,
            "connector_source": check.get("connector_source"),
            "probe": check.get("probe"),
            "details": {
                "reason": check.get("reason"),
                "error": check.get("error"),
                "store_domain": check.get("store_domain"),
                "api_version": check.get("api_version"),
                "attempts": check.get("attempts", 1),
            },
        }
    ]


def _mock_routes_allowed() -> bool:
    return IS_DEV_ENV or ALLOW_MOCK_ROUTES


_PROVIDER_ALIAS = {
    "google adk": "google_genai",
    "google_genai": "google_genai",
    "lmstudio": "local_openai_host",
    "lmstudio_local": "local_openai_host",
    "lmstudio_host": "local_openai_host",
    "local_openai_host": "local_openai_host",
    "local llm": "local_openai_host",
    "local_llm": "local_openai_host",
    "docker llm": "local_openai_docker",
    "docker_llm": "local_openai_docker",
    "lmstudio_docker": "local_openai_docker",
    "local_openai_docker": "local_openai_docker",
    "local fallback": "local_fallback",
    "local_fallback": "local_fallback",
}


def _to_provider_key(raw_provider: Any) -> str:
    if not isinstance(raw_provider, str):
        capabilities = _runtime_capabilities()
        return capabilities.get("preferred_provider_resolved") or capabilities.get("active_provider", "local_fallback")
    normalized = raw_provider.strip().lower()
    return _PROVIDER_ALIAS.get(normalized, normalized)


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_agent_payload(agent: dict[str, Any]) -> dict[str, Any]:
    payload = dict(agent)
    bound_skills = payload.get("bound_skills") or payload.get("skills") or []
    payload["bound_skills"] = list(bound_skills)
    payload["skills"] = list(payload.get("skills") or payload["bound_skills"])
    payload["runtime_provider"] = _to_provider_key(payload.get("runtime_provider") or payload.get("tech_stack"))
    payload["model_name"] = payload.get("model_name") or DEFAULT_MODEL
    payload["agent_version"] = payload.get("agent_version") or "v1"
    payload["purpose"] = (payload.get("purpose") or "").strip() or (
        f"Operate {payload.get('subsystem', 'General').lower()} workflows for {payload.get('name', 'agent')}."
    )
    payload["connector_bindings"] = list(payload.get("connector_bindings") or [])
    payload["used_by_workflow_ids"] = list(payload.get("used_by_workflow_ids") or [])
    code_payload = payload.get("code") if isinstance(payload.get("code"), dict) else {}
    payload["code"] = {
        "system_prompt": code_payload.get("system_prompt") or payload["purpose"],
        "tool_bindings": list(code_payload.get("tool_bindings") or payload["bound_skills"]),
        "runtime": {
            "provider": payload["runtime_provider"],
            "model": payload["model_name"],
        },
    }
    payload["scorecard"] = payload.get("scorecard") or {
        "connector_health_status": "healthy" if payload["connector_bindings"] else "unknown",
        "contract_validation_status": "pass" if payload["bound_skills"] or payload["code"]["system_prompt"] else "unknown",
        "recent_run_failure_rate": None,
        "last_successful_run_at": None,
    }
    payload["last_test_status"] = payload.get("last_test_status") or "unknown"
    return payload


def _mint_dev_role_token(role: str, subject: str = "dev-user") -> str:
    normalized_role = (role or "ops").strip().lower()
    if normalized_role not in {"admin", "ops", "analyst"}:
        normalized_role = "ops"

    jwt_secret = os.environ.get("OPS_JWT_SECRET", "").strip()
    if not jwt_secret:
        if _flag_enabled("ALLOW_INSECURE_DEV_AUTH", "0"):
            return "dev-token"
        raise RuntimeError("OPS_JWT_SECRET is not configured for local role bootstrap")

    import jwt

    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": normalized_role,
        "roles": [normalized_role],
        "iss": "acos-local-dev",
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(hours=24)).timestamp()),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def _normalize_skill_payload(skill: dict[str, Any]) -> dict[str, Any]:
    payload = dict(skill)
    payload["execution_mode"] = payload.get("execution_mode") or "local"
    payload["timeout_seconds"] = _safe_int(payload.get("timeout_seconds", 15), 15)
    payload["retries"] = _safe_int(payload.get("retries", 0), 0)
    payload["input_schema"] = payload.get("input_schema") or {
        "type": "object",
        "properties": {},
        "required": [],
    }
    payload["output_schema"] = payload.get("output_schema") or {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
    }
    return payload


@app.get("/runs")
def list_runs(
    tenant_id: str = None,
    limit: int = 100,
    _claims: dict = Depends(READ_ACCESS),
):
    if limit > 1000:
        limit = 1000
    return {"runs": get_runs(tenant_id=tenant_id, limit=limit)}


@app.get("/runs/{run_id}")
def get_run_detail(
    run_id: str,
    _claims: dict = Depends(READ_ACCESS),
):
    run = get_run(run_id)
    if not run:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"run": run, "events": get_events(run_id)}


@app.post("/replay/{run_id}")
@app.post("/v1/replay/{run_id}")
@limiter.limit(REPLAY_LIMIT)
def replay_run(
    request: Request,
    run_id: str,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    return replay(run_id)


@app.get("/products")
def list_products(request: Request, _claims: dict = Depends(READ_ACCESS)):
    category = request.query_params.get("category")
    return {"products": get_products(category=category)}


@app.get("/products/{product_id}")
def get_product(product_id: str, _claims: dict = Depends(READ_ACCESS)):
    product = get_product_by_id(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return product


@app.get("/orders/{customer_id}")
def list_orders(customer_id: str, _claims: dict = Depends(READ_ACCESS)):
    return {"orders": get_orders_for_customer(customer_id)}


@app.get("/dashboard")
def dashboard(_claims: dict = Depends(READ_ACCESS)):
    from acosplatform.db.repository import get_dashboard

    return {
        "metrics": get_dashboard(),
        "billing": get_cost_summary(),
        "experiments": get_experiment_results(),
    }


@app.get("/billing")
def billing(tenant_id: str = None, _claims: dict = Depends(READ_ACCESS)):
    if tenant_id:
        return {"usage": get_usage(tenant_id)}
    return {"summary": get_cost_summary(), "by_tenant": get_usage()}


def _ops_context_payload(claims: dict[str, Any]) -> dict[str, Any]:
    roles = _roles_from_claims(claims)
    primary_role = roles[0] if roles else "viewer"
    capabilities = _runtime_capabilities()
    return {
        "user_id": claims.get("sub") or claims.get("email") or "ops-user",
        "display_name": claims.get("name") or claims.get("email") or claims.get("sub") or "ACOS Operator",
        "roles": roles,
        "primary_role": primary_role,
        "tenant_id": "default",
        "available_tenants": ["default"],
        "environment": OPS_ENVIRONMENT,
        "mode": _platform_mode(),
        "mode_options": list(SUPPORTED_PLATFORM_MODES),
        "data_mode": _data_plane_mode(),
        "runtime_preference": _runtime_preference(),
        "runtime_preference_options": list(RUNTIME_PREFERENCE_OPTIONS),
        "runtime_provider": capabilities.get("preferred_provider_resolved") or capabilities.get("active_provider"),
    }


@app.get("/api/v1/ops/context")
def ops_context(claims: dict = Depends(READ_ACCESS)):
    return _ops_context_payload(claims)


@app.patch("/api/v1/runtime/preferences")
def update_runtime_preferences(
    payload: RuntimePreferencesRequest,
    claims: dict = Depends(OPERATE_ACCESS),
):
    try:
        if payload.platform_mode is not None:
            _set_platform_mode(payload.platform_mode)
        if payload.runtime_preference is not None:
            _set_runtime_preference(payload.runtime_preference)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {
        "status": "success",
        "context": _ops_context_payload(claims),
        "runtime": _runtime_health(),
    }


@app.get("/api/v1/connectors/bindings")
def list_connector_bindings(
    environment: str = OPS_ENVIRONMENT,
    _claims: dict = Depends(READ_ACCESS),
):
    bindings = _connector_bindings(environment=environment)
    page_mode = "live" if any(binding.get("mode") == "live" for binding in bindings) else "sandbox"
    return {"mode": page_mode, "bindings": bindings}


@app.get("/api/v1/runtime/providers")
def runtime_provider_health(_claims: dict = Depends(READ_ACCESS)):
    return _runtime_health()


@app.get("/api/v1/runtime/providers/lmstudio/health")
def lmstudio_health(_claims: dict = Depends(READ_ACCESS)):
    runtime = _runtime_health()
    return runtime["lmstudio"]


@app.get("/api/v1/channels")
def list_channels(_claims: dict = Depends(READ_ACCESS)):
    stored = {binding.get("id"): binding for binding in get_channel_bindings()}
    connector_status = {binding.get("id"): binding for binding in _connector_bindings()}
    channels = []
    for binding in stored.values():
        connector = connector_status.get(binding.get("id"), {})
        channels.append(
            {
                **binding,
                "status": connector.get("status", binding.get("status", "sandbox")),
                "mode": connector.get("mode", binding.get("mode", "sandbox")),
                "health": connector,
            }
        )
    page_mode = "live" if any(channel.get("mode") == "live" for channel in channels) else "sandbox"
    return {"mode": page_mode, "channels": channels}


@app.get("/api/v1/channels/{binding_id}/pairings")
def list_channel_pairings(binding_id: str, request: Request, _claims: dict = Depends(READ_ACCESS)):
    binding = get_channel_binding(binding_id)
    if not binding:
        return JSONResponse(status_code=404, content={"error": "Channel not found"})
    pairings = []
    for route_id in binding.get("allowed_routes") or [binding.get("default_route")]:
        route = get_demo_route(route_id)
        if not route:
            continue
        pairings.append(_ensure_channel_pairing(binding, route, request))
    return {"status": "success", "binding_id": binding_id, "pairings": pairings}


@app.post("/api/v1/channels/{binding_id}/pairings")
def create_channel_pairing(
    binding_id: str,
    payload: ChannelPairingRequest,
    request: Request,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    binding = get_channel_binding(binding_id)
    if not binding:
        return JSONResponse(status_code=404, content={"error": "Channel not found"})
    route = get_demo_route(payload.route_id)
    if not route:
        return JSONResponse(status_code=404, content={"error": "Demo route not found"})
    pairing = _ensure_channel_pairing(binding, route, request, expires_in_hours=payload.expires_in_hours or 72)
    return {"status": "success", "pairing": pairing}


@app.post("/api/v1/channels/telegram/link")
def link_telegram_channel(payload: ChannelLinkRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    metadata = dict(payload.metadata or {})
    probe = probe_telegram_bot(config_override=metadata)
    saved = save_channel_binding(
        {
            "id": payload.id or "telegram-ops",
            "type": "telegram",
            "tenant_id": payload.tenant_id,
            "environment": payload.environment,
            "identity": payload.identity or probe.get("display_name") or "Telegram Ops Bot",
            "default_route": payload.default_route,
            "allowed_routes": payload.allowed_routes,
            "notification_targets": payload.notification_targets,
            "status": "healthy" if probe.get("status") == "ok" else "sandbox",
            "mode": "live" if probe.get("status") == "ok" else "sandbox",
            "metadata": {
                **metadata,
                "bot_username": probe.get("username") or metadata.get("bot_username") or "",
                "default_chat_id": metadata.get("default_chat_id") or "",
            },
        }
    )
    return {"status": "success", "channel": saved, "probe": probe}


@app.get("/api/v1/channels/pairings/{pairing_id}/qr.svg")
def channel_pairing_qr(pairing_id: str, request: Request):
    pairing = get_channel_pairing(pairing_id)
    if not pairing:
        return JSONResponse(status_code=404, content={"error": "Pairing not found"})
    binding = get_channel_binding(pairing.get("channel_binding_id"))
    route = get_demo_route(pairing.get("route_id"))
    if not binding or not route:
        return JSONResponse(status_code=404, content={"error": "Pairing target not found"})

    start_link = _build_pairing_start_link(binding, pairing.get("pair_code", ""))
    if not start_link:
        fallback_text = f"PAIR {pairing.get('pair_code')}"
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320' viewBox='0 0 320 320'>"
            "<rect width='320' height='320' fill='#F6F7FB'/>"
            "<rect x='12' y='12' width='296' height='296' rx='16' fill='#ffffff' stroke='#d0d7e2'/>"
            "<text x='160' y='120' text-anchor='middle' font-family='Arial, sans-serif' font-size='18' fill='#1f2937'>"
            "Scan-to-start unavailable"
            "</text>"
            f"<text x='160' y='170' text-anchor='middle' font-family='Courier New, monospace' font-size='20' fill='#111827'>{fallback_text}</text>"
            "<text x='160' y='208' text-anchor='middle' font-family='Arial, sans-serif' font-size='12' fill='#6b7280'>"
            "Add bot username or start chat number to enable QR deep-links."
            "</text>"
            "</svg>"
        )
        return Response(content=svg, media_type="image/svg+xml")

    import qrcode
    import qrcode.image.svg

    image = qrcode.make(start_link, image_factory=qrcode.image.svg.SvgImage, box_size=10, border=3)
    buffer = BytesIO()
    image.save(buffer)
    return Response(content=buffer.getvalue(), media_type="image/svg+xml")


@app.post("/api/v1/channels/whatsapp/link")
def link_whatsapp_channel(payload: ChannelLinkRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    metadata = dict(payload.metadata or {})
    probe = probe_whatsapp_cloud(config_override=metadata)
    saved = save_channel_binding(
        {
            "id": payload.id or "whatsapp-support",
            "type": "whatsapp",
            "tenant_id": payload.tenant_id,
            "environment": payload.environment,
            "identity": payload.identity or probe.get("verified_name") or "WhatsApp Support",
            "default_route": payload.default_route,
            "allowed_routes": payload.allowed_routes,
            "notification_targets": payload.notification_targets,
            "status": "healthy" if probe.get("status") == "ok" else "sandbox",
            "mode": "live" if probe.get("status") == "ok" else "sandbox",
            "metadata": {
                **metadata,
                "phone_number_id": probe.get("phone_number_id") or metadata.get("phone_number_id") or "",
                "verified_name": probe.get("verified_name") or metadata.get("verified_name") or "",
                "display_phone_number": probe.get("display_phone_number") or metadata.get("display_phone_number") or "",
            },
        }
    )
    return {"status": "success", "channel": saved, "probe": probe}


@app.post("/api/v1/channels/{binding_id}/test")
def send_channel_test(binding_id: str, payload: ChannelTestRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    binding = get_channel_binding(binding_id)
    if not binding:
        return JSONResponse(status_code=404, content={"error": "Channel not found"})
    metadata = binding.get("metadata") or {}
    if binding.get("type") == "telegram":
        result = send_telegram_message(
            payload.text,
            chat_id=payload.recipient or metadata.get("default_chat_id"),
            config_override=metadata,
        )
    elif binding.get("type") == "whatsapp":
        result = execute_whatsapp_action(
            "send_message",
            {"to": payload.recipient or metadata.get("default_recipient") or metadata.get("start_chat_number"), "message": payload.text},
            allow_live_send=True,
            config_override=metadata,
        )
    else:
        return JSONResponse(status_code=400, content={"error": "Unsupported channel type"})
    return {"status": "success", "binding_id": binding_id, "delivery": result}


@app.get("/api/v1/channels/approvals")
def list_channel_approvals(_claims: dict = Depends(READ_ACCESS)):
    approvals_payload = []
    for sender in get_channel_senders(approval_status="pending"):
        approvals_payload.append(
            {
                **sender,
                "channel": (get_channel_binding(sender.get("channel_binding_id")) or {}).get("type"),
            }
        )
    return {"approvals": approvals_payload}


@app.post("/api/v1/channels/approvals/{sender_id}/approve")
def approve_channel_sender(sender_id: str, payload: SenderApprovalRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    sender = next((item for item in get_channel_senders() if item.get("id") == sender_id), None)
    if not sender:
        return JSONResponse(status_code=404, content={"error": "Sender approval request not found"})
    sender["approval_status"] = "approved"
    if payload.customer_id:
        sender["customer_id"] = payload.customer_id
    if payload.display_name:
        sender["display_name"] = payload.display_name
    sender = save_channel_sender(sender)
    return {"status": "success", "sender": sender}


@app.get("/api/v1/demo/routes")
def list_demo_routes_endpoint(_claims: dict = Depends(READ_ACCESS)):
    routes = get_demo_routes()
    page_mode = "live" if any(route.get("mode") == "live" for route in routes) else "sandbox"
    return {"mode": page_mode, "routes": routes}


@app.post("/api/v1/demo/routes/{route_id}/simulate")
def simulate_demo_route(route_id: str, payload: DemoRouteDispatchRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    existing_sender = get_channel_sender_by_external_id(payload.channel_binding_id, payload.sender_external_id)
    sender = existing_sender or save_channel_sender(
        {
            "id": f"sender-{uuid4().hex[:10]}",
            "channel_binding_id": payload.channel_binding_id,
            "sender_external_id": payload.sender_external_id,
            "display_name": payload.display_name,
            "customer_id": "cust_1001" if payload.sender_external_id.endswith("0001") else None,
            "approval_status": "approved",
            "last_message": payload.message,
            "last_seen_at": _utc_iso(),
            "metadata": {"simulated": True},
        }
    )
    if sender.get("approval_status") != "approved":
        sender["approval_status"] = "approved"
        sender = save_channel_sender(sender)
    result = dispatch_demo_route(
        route_id=route_id,
        channel_binding_id=payload.channel_binding_id,
        sender=sender,
        message=payload.message,
        tenant_id=payload.tenant_id,
        environment=payload.environment,
    )
    return result


@app.get("/api/mock/crm/customers")
def list_mock_crm_customers(_claims: dict = Depends(READ_ACCESS)):
    return {"customers": get_crm_customers()}


@app.get("/api/mock/crm/customers/{customer_id}")
def get_mock_crm_customer(customer_id: str, _claims: dict = Depends(READ_ACCESS)):
    customer = get_crm_customer_by_id(customer_id)
    if not customer:
        return JSONResponse(status_code=404, content={"error": "Customer not found"})
    return {"customer": customer, "cases": get_crm_cases(customer_id)}


@app.get("/api/mock/crm/cases")
def list_mock_crm_cases(customer_id: str | None = None, _claims: dict = Depends(READ_ACCESS)):
    return {"cases": get_crm_cases(customer_id)}


@app.post("/api/mock/crm/cases")
def create_mock_crm_case(payload: CRMCaseCreateRequest, _claims: dict = Depends(OPERATE_ACCESS)):
    case = save_crm_case(
        {
            "id": f"case_{uuid4().hex[:8]}",
            "customer_id": payload.customer_id,
            "tenant_id": "default",
            "subject": payload.subject,
            "status": payload.status,
            "priority": payload.priority,
            "channel": payload.channel,
            "summary": payload.summary,
            "metadata": {"created_via": "ops_api"},
        }
    )
    return {"status": "success", "case": case}


@app.get("/api/v1/connectors/whatsapp/webhook")
@app.get("/connectors/whatsapp/webhook")
def whatsapp_webhook_verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    verified, challenge = verify_whatsapp_webhook(hub_mode or "", hub_verify_token or "", hub_challenge or "")
    if not verified:
        for metadata in _whatsapp_binding_overrides():
            verified, challenge = verify_whatsapp_webhook(
                hub_mode or "",
                hub_verify_token or "",
                hub_challenge or "",
                config_override=metadata,
            )
            if verified:
                break
    if not verified:
        return JSONResponse(status_code=403, content={"error": "Webhook verification failed"})
    return HTMLResponse(content=challenge, status_code=200)


@app.post("/api/v1/connectors/whatsapp/webhook")
@app.post("/connectors/whatsapp/webhook")
async def whatsapp_webhook_ingest(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid WhatsApp webhook payload"})

    entries = payload.get("entry") if isinstance(payload, dict) else []
    processed = []
    ignored = 0
    for entry in entries if isinstance(entries, list) else []:
        changes = entry.get("changes") if isinstance(entry, dict) else []
        for change in changes if isinstance(changes, list) else []:
            value = change.get("value") if isinstance(change, dict) else {}
            binding = _resolve_whatsapp_binding(value if isinstance(value, dict) else {})
            channel_binding_id = (binding or {}).get("id") or "whatsapp-support"
            tenant_id = (binding or {}).get("tenant_id") or "default"
            environment = (binding or {}).get("environment") or OPS_ENVIRONMENT
            contact_directory = _whatsapp_contact_directory(value if isinstance(value, dict) else {})
            messages = value.get("messages") if isinstance(value, dict) else []
            statuses = value.get("statuses") if isinstance(value, dict) else []

            for status in statuses if isinstance(statuses, list) else []:
                _record_whatsapp_webhook_event(
                    action="channel.whatsapp.status",
                    binding=binding,
                    resource_id=str(status.get("id") or channel_binding_id),
                    payload={
                        "status": status.get("status"),
                        "recipient_id": status.get("recipient_id"),
                        "message_id": status.get("id"),
                        "errors": status.get("errors") or [],
                    },
                )

            for message in messages if isinstance(messages, list) else []:
                sender_key = str(message.get("from") or "").strip()
                sender_external_id = _normalize_whatsapp_sender_external_id(sender_key)
                display_name = contact_directory.get(_sanitize_phone_digits(sender_key), "WhatsApp sender")
                body = _extract_whatsapp_message_text(message)
                message_type = str(message.get("type") or "unknown").strip()

                if not body:
                    ignored += 1
                    ignored_payload = {
                        "message_id": message.get("id"),
                        "message_type": message_type,
                        "sender_external_id": sender_external_id,
                        "reason": "unsupported_or_empty_message",
                    }
                    processed.append({"status": "ignored", **ignored_payload})
                    _record_whatsapp_webhook_event(
                        action="channel.whatsapp.inbound.ignored",
                        binding=binding,
                        resource_id=str(message.get("id") or sender_external_id),
                        payload=ignored_payload,
                    )
                    continue

                _record_whatsapp_webhook_event(
                    action="channel.whatsapp.inbound.received",
                    binding=binding,
                    resource_id=str(message.get("id") or sender_external_id),
                    payload={
                        "message_id": message.get("id"),
                        "message_type": message_type,
                        "sender_external_id": sender_external_id,
                        "binding_id": channel_binding_id,
                        "tenant_id": tenant_id,
                        "preview": body[:280],
                    },
                )
                result = ingest_channel_message(
                    channel_binding_id=channel_binding_id,
                    sender_external_id=sender_external_id,
                    display_name=display_name,
                    message=body,
                    tenant_id=tenant_id,
                    environment=environment,
                )
                processed.append(
                    {
                        "binding_id": channel_binding_id,
                        "tenant_id": tenant_id,
                        "message_id": message.get("id"),
                        "message_type": message_type,
                        **result,
                    }
                )
    return {
        "status": "accepted",
        "entries": len(entries) if isinstance(entries, list) else 0,
        "ignored": ignored,
        "processed": processed,
    }


@app.post("/api/v1/connectors/telegram/webhook")
async def telegram_webhook_ingest(request: Request):
    payload = await request.json()
    message = payload.get("message") if isinstance(payload, dict) else {}
    text = message.get("text") or ""
    chat = message.get("chat") or {}
    sender_external_id = f"telegram:{chat.get('id')}"
    display_name = chat.get("title") or chat.get("username") or str(chat.get("id") or "Telegram sender")
    result = ingest_channel_message(
        channel_binding_id="telegram-ops",
        sender_external_id=sender_external_id,
        display_name=display_name,
        message=text,
        tenant_id="default",
        environment=OPS_ENVIRONMENT,
    )
    return {"status": "accepted", "processed": [result]}


@app.get("/api/v1/agents")
@app.get("/agents")
def list_agents(_claims: dict = Depends(READ_ACCESS)):
    mode = _data_plane_mode()
    return {
        "mode": mode,
        "operating_mode": _platform_mode(),
        "agents": _attach_provenance(get_agents(), mode),
        "runtime_capabilities": _runtime_capabilities(),
    }


@app.get("/api/v1/agents/providers")
def agent_provider_capabilities(_claims: dict = Depends(READ_ACCESS)):
    return _runtime_capabilities()


@app.get("/api/v1/agents/{agent_id}")
@app.get("/agents/{agent_id}")
def agent_detail(agent_id: str, _claims: dict = Depends(READ_ACCESS)):
    agent = get_agent_by_id(agent_id)
    if not agent:
        return JSONResponse(status_code=404, content={"error": "Agent not found"})
    mode = _data_plane_mode()
    return {
        "mode": mode,
        "operating_mode": _platform_mode(),
        "agent": {**agent, "provenance_mode": mode},
        "scorecard": _build_agent_scorecard(agent),
    }


@app.post("/api/v1/agents")
@app.post("/agents")
def create_agent(agent: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    if not agent.get("id") or not agent.get("name"):
        return JSONResponse(status_code=400, content={"error": "Agent requires id and name"})
    prepared = _normalize_agent_payload(agent)
    saved = save_agent(prepared)
    return {"status": "success", "agent": saved}


@app.patch("/api/v1/agents/{agent_id}")
@app.patch("/agents/{agent_id}")
def update_agent(agent_id: str, updates: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    target = get_agent_by_id(agent_id)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Agent not found"})
    patch = dict(updates)
    if "runtime_provider" in patch or "tech_stack" in patch:
        patch["runtime_provider"] = _to_provider_key(patch.get("runtime_provider") or patch.get("tech_stack"))
    if "bound_skills" in patch and "skills" not in patch:
        patch["skills"] = list(patch.get("bound_skills") or [])
    target.update(patch)
    saved = save_agent(_normalize_agent_payload(target))
    return {"status": "success", "agent": saved}


@app.post("/api/v1/agents/{agent_id}/bind-skill")
@app.post("/agents/{agent_id}/bind-skill")
def bind_skill_to_agent(
    agent_id: str,
    payload: BindSkillRequest,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    agent = get_agent_by_id(agent_id)
    if not agent:
        return JSONResponse(status_code=404, content={"error": "Agent not found"})
    skill = get_skill_by_id(payload.skill_id)
    if not skill:
        return JSONResponse(status_code=404, content={"error": "Skill not found"})

    bound_skills = list(agent.get("bound_skills") or agent.get("skills") or [])
    if payload.skill_id not in bound_skills:
        bound_skills.append(payload.skill_id)
    agent["bound_skills"] = bound_skills
    agent["skills"] = sorted(set(list(agent.get("skills") or []) + [payload.skill_id]))
    saved = save_agent(_normalize_agent_payload(agent))
    return {"status": "success", "agent": saved}


@app.post("/api/v1/agents/{agent_id}/test")
@app.post("/agents/{agent_id}/test")
def test_agent(
    agent_id: str,
    payload: AgentTestRequest,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    started = perf_counter()
    agent = get_agent_by_id(agent_id)
    if not agent:
        return JSONResponse(status_code=404, content={"error": "Agent not found"})

    provider = _to_provider_key(agent.get("runtime_provider"))
    if provider not in SUPPORTED_RUNTIME_PROVIDERS:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Unsupported runtime provider",
                "provider": provider,
                "supported_providers": list(SUPPORTED_RUNTIME_PROVIDERS),
            },
        )

    adk_result = run_adk(
        {
            "message": payload.message,
            "tenant_id": payload.tenant_id,
            "customer_id": payload.customer_id,
        },
        journey_type=payload.journey_type,
        requested_provider=provider,
        strict_provider=True,
    )
    runtime = adk_result.get("runtime", {})
    used_skills = adk_result.get("skills_used", [])
    runtime_errors = list(adk_result.get("errors") or [])
    contract_errors = list(adk_result.get("contract_errors") or [])
    configured_bound = list(agent.get("bound_skills") or agent.get("skills") or [])
    resolved_provider = provider if provider == "local_fallback" else runtime.get("provider", provider)
    duration_ms = round((perf_counter() - started) * 1000, 3)
    system_tool_trace = _agent_tool_trace(agent, payload.message, payload.customer_id, payload.tenant_id)

    result = {
        "request_id": f"agt-test-{uuid4().hex[:10]}",
        "trace_id": f"trace-{uuid4().hex[:8]}",
        "timestamp": _utc_iso(),
        "status": "pass" if not runtime_errors and not contract_errors else "fail",
        "agent_id": agent_id,
        "journey_type": payload.journey_type,
        "tenant_id": payload.tenant_id,
        "runtime_provider": resolved_provider,
        "configured_runtime_provider": provider,
        "model_name": runtime.get("model_name", agent.get("model_name", DEFAULT_MODEL)),
        "agent_version": agent.get("agent_version", "v1"),
        "bound_skills": configured_bound,
        "bound_skills_executed": [skill for skill in used_skills if not configured_bound or skill in configured_bound],
        "duration_ms": duration_ms,
        "runtime": runtime,
        "adk_result": adk_result,
        "system_tools_used": system_tool_trace,
    }
    if runtime_errors or contract_errors:
        result["errors"] = runtime_errors + contract_errors
        result["error"] = result["errors"][0]
    agent["last_test_at"] = result["timestamp"]
    agent["last_test_status"] = result["status"]
    agent["scorecard"] = {
        **_build_agent_scorecard(agent),
        "last_test_at": result["timestamp"],
        "last_test_status": result["status"],
        "tool_trace": system_tool_trace,
    }
    save_agent(agent)
    return result


@app.get("/api/v1/skills")
@app.get("/skills")
def list_skills(_claims: dict = Depends(READ_ACCESS)):
    return {"skills": get_skills()}


@app.post("/api/v1/skills")
@app.post("/skills")
def create_skill(skill: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    if not skill.get("id") or not skill.get("name"):
        return JSONResponse(status_code=400, content={"error": "Skill requires id and name"})
    prepared = _normalize_skill_payload(skill)
    saved = save_skill(prepared)
    return {"status": "success", "skill": saved}


@app.patch("/api/v1/skills/{skill_id}")
@app.patch("/skills/{skill_id}")
def update_skill(skill_id: str, updates: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    target = get_skill_by_id(skill_id)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Skill not found"})
    patch = dict(updates)
    if "timeout_seconds" in patch:
        patch["timeout_seconds"] = _safe_int(patch["timeout_seconds"], target.get("timeout_seconds", 15))
    if "retries" in patch:
        patch["retries"] = _safe_int(patch["retries"], target.get("retries", 0))
    target.update(patch)
    saved = save_skill(target)
    return {"status": "success", "skill": saved}


@app.post("/api/v1/skills/{skill_id}/test")
@app.post("/skills/{skill_id}/test")
def test_skill(
    skill_id: str,
    payload: SkillTestRequest,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    started = perf_counter()
    skill = get_skill_by_id(skill_id)
    if not skill:
        return JSONResponse(status_code=404, content={"error": "Skill not found"})

    input_payload = payload.input_payload or {}
    input_errors = _validate_contract_payload(
        schema=skill.get("input_schema") or {},
        payload=input_payload,
        target="input_schema",
    )
    if input_errors:
        return JSONResponse(
            status_code=400,
            content={
                "status": "fail",
                "request_id": f"sk-test-{uuid4().hex[:10]}",
                "timestamp": _utc_iso(),
                "skill_id": skill_id,
                "contract_validation": {
                    "input_valid": False,
                    "output_valid": False,
                    "errors": input_errors,
                },
            },
        )

    execution_mode = (skill.get("execution_mode") or "local").strip().lower()
    connector_metadata: dict[str, Any] = {
        "source": "local_fallback",
        "degraded": False,
        "attempts": 1,
        "error": None,
    }
    if execution_mode == "http_connector":
        connector_run = _run_http_connector_skill_test(
            skill=skill,
            input_payload=input_payload,
            tenant_id=payload.tenant_id,
        )
        connector_source = connector_run.get("connector_source", "local_fallback")
        output_payload = connector_run.get("output_payload") or {}
        connector_metadata = {
            "source": connector_source,
            "degraded": bool(connector_run.get("degraded", False)),
            "attempts": int(connector_run.get("attempts", 1) or 1),
            "error": connector_run.get("error"),
        }
    else:
        connector_source = "local_fallback"
        output_payload = {
            "status": "ok",
            "skill_id": skill_id,
            "execution_mode": execution_mode,
            "echo": input_payload,
        }
    output_errors = _validate_contract_payload(
        schema=skill.get("output_schema") or {},
        payload=output_payload,
        target="output_schema",
    )
    duration_ms = round((perf_counter() - started) * 1000, 3)
    return {
        "status": "pass" if not output_errors else "fail",
        "request_id": f"sk-test-{uuid4().hex[:10]}",
        "trace_id": f"trace-{uuid4().hex[:8]}",
        "timestamp": _utc_iso(),
        "skill_id": skill_id,
        "tenant_id": payload.tenant_id,
        "workflow_id": payload.workflow_id,
        "workflow_version": payload.workflow_version,
        "duration_ms": duration_ms,
        "connector_source": connector_source,
        "connector_metadata": connector_metadata,
        "contract_validation": {
            "input_valid": True,
            "output_valid": not output_errors,
            "errors": output_errors,
        },
        "output_payload": output_payload,
    }


@app.post("/api/v1/sandbox/execute-scenarios")
@app.post("/sandbox/execute-scenarios")
def execute_sandbox_scenarios(
    payload: SandboxScenarioRequest,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    if not _mock_routes_allowed():
        return JSONResponse(
            status_code=403,
            content={"error": "Sandbox scenarios are disabled. Set ALLOW_MOCK_ROUTES=1 to enable."},
        )

    scenarios = [
        ("order_status", "Where is my order ORD-1001?"),
        ("return_eligibility", "I want to return my last order"),
        ("refund_triage", "I need a refund for my order"),
        ("loyalty_fallback", "Show my loyalty status and rewards"),
    ]

    results: list[dict[str, Any]] = []
    for scenario_name, message in scenarios:
        run_started = perf_counter()
        try:
            run_result = run_journey(
                {
                    "message": message,
                    "tenant_id": payload.tenant_id,
                    "customer_id": payload.customer_id,
                    "environment_id": payload.environment_id,
                    "auth_subject": {"sub": "ops-sandbox-runner", "role": "ops"},
                }
            )
            journey = run_result.get("journey")
            result_payload = run_result.get("result", {})
            passed = (
                (scenario_name == "order_status" and journey == "post_purchase")
                or (scenario_name in {"return_eligibility", "refund_triage"} and journey == "service")
                or (scenario_name == "loyalty_fallback" and journey in {"engagement", "discovery"})
            )
            results.append(
                {
                    "scenario": scenario_name,
                    "status": "pass" if passed else "fail",
                    "journey": journey,
                    "run_id": run_result.get("run_id"),
                    "trace_id": run_result.get("trace", {}).get("trace_id"),
                    "workflow_id": run_result.get("workflow", {}).get("workflow_id"),
                    "workflow_version": run_result.get("workflow", {}).get("workflow_version"),
                    "provider": result_payload.get("agent", {}).get("runtime", {}).get("provider"),
                    "model_name": result_payload.get("agent", {}).get("runtime", {}).get("model_name"),
                    "duration_ms": round((perf_counter() - run_started) * 1000, 3),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "scenario": scenario_name,
                    "status": "fail",
                    "error": str(exc),
                    "duration_ms": round((perf_counter() - run_started) * 1000, 3),
                }
            )

    passed = len([row for row in results if row.get("status") == "pass"])
    external_checks = _run_external_connector_checks(payload.tenant_id)
    external_passed = len([row for row in external_checks if row.get("status") == "pass"])
    external_failed = len([row for row in external_checks if row.get("status") == "fail"])
    external_skipped = len([row for row in external_checks if row.get("status") == "skip"])
    summary = {
        "executed": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "overall_status": "pass" if passed >= 3 else "fail",
        "external_checks": {
            "executed": len(external_checks),
            "passed": external_passed,
            "failed": external_failed,
            "skipped": external_skipped,
        },
    }
    artifact = {
        "timestamp": _utc_iso(),
        "suite": "agentic-commerce-sandbox",
        "tenant_id": payload.tenant_id,
        "environment_id": payload.environment_id,
        "summary": summary,
        "results": results,
        "external_checks": external_checks,
    }
    evidence_file = None
    if payload.write_evidence:
        evidence_file = _write_evidence_file("agentic-commerce-sandbox", artifact)
    return {
        "summary": summary,
        "results": results,
        "external_checks": external_checks,
        "evidence_file": evidence_file,
    }


@app.get("/api/v1/tenants")
@app.get("/tenants")
def list_tenants_endpoint(_claims: dict = Depends(READ_ACCESS)):
    from acosplatform.tenancy.manager import list_tenants
    return {"tenants": list_tenants()}


@app.post("/api/v1/tenants")
@app.post("/tenants")
def create_tenant(tenant: dict, token: dict = Depends(ADMIN_ACCESS)):
    from acosplatform.tenancy.manager import add_tenant
    try:
        record = add_tenant(tenant["id"], {k: v for k, v in tenant.items() if k != "id"})
    except (ValueError, KeyError) as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})
    actor = _actor(token)
    audit("tenant.created", actor=actor, resource=f"/tenants/{record['id']}")
    save_audit_event(actor, "tenant.created", "tenant", record["id"], payload=record)
    return {"status": "success", "tenant": record}


@app.patch("/api/v1/tenants/{tenant_id}")
@app.patch("/tenants/{tenant_id}")
def update_tenant_endpoint(tenant_id: str, updates: dict, token: dict = Depends(ADMIN_ACCESS)):
    from acosplatform.tenancy.manager import update_tenant
    record = update_tenant(tenant_id, updates)
    actor = _actor(token)
    audit("tenant.updated", actor=actor, resource=f"/tenants/{tenant_id}")
    save_audit_event(actor, "tenant.updated", "tenant", tenant_id, payload=updates)
    return {"status": "success", "tenant": record}


@app.get("/api/v1/workflows")
@app.get("/workflows")
def list_workflows(
    tenant_id: str = None,
    environment: str = OPS_ENVIRONMENT,
    _claims: dict = Depends(READ_ACCESS),
):
    mode = _data_plane_mode()
    return {
        "mode": mode,
        "operating_mode": _platform_mode(),
        "environment": environment,
        "recommended_demo_workflow_id": DEMO_WORKFLOW_ID,
        "workflows": list_workflows_with_state(tenant_id=tenant_id, environment=environment),
    }


@app.get("/api/v1/workflows/{workflow_id}")
@app.get("/workflows/{workflow_id}")
def workflow_detail(
    workflow_id: str,
    environment: str = OPS_ENVIRONMENT,
    _claims: dict = Depends(READ_ACCESS),
):
    detail = get_workflow_detail(workflow_id, environment=environment)
    if not detail:
        return JSONResponse(status_code=404, content={"error": "Workflow not found"})
    return {
        **detail,
        "mode": _data_plane_mode(),
        "operating_mode": _platform_mode(),
    }


@app.patch("/api/v1/workflows/{workflow_id}")
@app.patch("/workflows/{workflow_id}")
def workflow_update(
    workflow_id: str,
    payload: CanvasSaveRequest,
    token: dict = Depends(OPERATE_ACCESS),
    environment: str = OPS_ENVIRONMENT,
):
    version_payload = WorkflowVersionCreateRequest(
        change_summary="Canvas save",
        validation_status="draft",
        step_definitions=[payload.step_definitions],
    )
    try:
        version = create_workflow_version(
            workflow_id=workflow_id,
            payload=version_payload,
            actor=_actor(token),
            environment=environment,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    return {"version": version}


@app.post("/api/v1/workflows/{workflow_id}/test-run")
@app.post("/workflows/{workflow_id}/test-run")
def workflow_test_run(
    workflow_id: str,
    payload: WorkflowTestRunRequest,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    try:
        result = execute_saved_workflow(
            workflow_id=workflow_id,
            tenant_id=payload.tenant_id,
            customer_id="ops-test-customer",
            environment=payload.environment or OPS_ENVIRONMENT,
            message=payload.message or str((payload.input or {}).get("message") or ""),
            order_id=str((payload.input or {}).get("order_id") or ""),
            channel_binding_id=str((payload.input or {}).get("channel_binding_id") or "whatsapp-support"),
            sender_external_id=str((payload.input or {}).get("sender_external_id") or "whatsapp:+447700900001"),
            allow_live_send=bool((payload.input or {}).get("send_live")),
            persist_run=True,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})

    tool_trace = result.get("tool_trace") or []
    runtime_mode = "mixed" if any(item.get("mode") == "live" for item in tool_trace) else "sandbox"
    agent_nodes = [
        {
            "node_id": item.get("node_id"),
            "agent_id": ((item.get("result") or {}).get("runtime") or {}).get("provider"),
            "agent_name": item.get("label"),
            "status": item.get("status"),
        }
        for item in (result.get("node_trace") or [])
        if item.get("node_type") == "agentNode"
    ]
    return {
        "status": "pass",
        "run_id": result.get("run_id"),
        "mode": runtime_mode,
        "workflow_id": workflow_id,
        "workflow_version": (result.get("workflow") or {}).get("workflow_version"),
        "tenant_id": payload.tenant_id,
        "environment": payload.environment,
        "connector_results": tool_trace,
        "agent_summary": agent_nodes,
        "message": payload.message,
        "node_trace": result.get("node_trace") or [],
        "response_text": result.get("response_text"),
    }


@app.post("/api/v1/workflows/{workflow_id}/execute")
@app.post("/workflows/{workflow_id}/execute")
def workflow_execute(
    workflow_id: str,
    payload: WorkflowExecuteRequest,
    claims: dict = Depends(OPERATE_ACCESS),
):
    try:
        result = execute_saved_workflow(
            workflow_id=workflow_id,
            tenant_id=payload.tenant_id,
            customer_id=payload.customer_id,
            environment=payload.environment or OPS_ENVIRONMENT,
            message=payload.message,
            order_id=payload.order_id,
            channel_binding_id="whatsapp-support",
            sender_external_id="",
            allow_live_send=True,
            persist_run=True,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})

    return {
        "status": "success",
        "requested_workflow_id": workflow_id,
        "requested_workflow_family": (get_workflow_detail(workflow_id, environment=payload.environment or OPS_ENVIRONMENT) or {}).get("workflow", {}).get("workflow_family"),
        "journey": result.get("journey"),
        "run_id": result.get("run_id"),
        "trace": {"trace_id": result.get("run_id")},
        "context": {"customer_id": payload.customer_id},
        "workflow": result.get("workflow"),
        "result": result.get("result"),
        "execution_mode": "graph_live" if check_connection() else "graph_demo",
        "node_trace": result.get("node_trace") or [],
        "response_text": result.get("response_text"),
    }


@app.get("/api/v1/workflows/{workflow_id}/runs")
@app.get("/workflows/{workflow_id}/runs")
def workflow_runs(
    workflow_id: str,
    limit: int = 100,
    _claims: dict = Depends(READ_ACCESS),
):
    if limit > 500:
        limit = 500
    return {"runs": get_runs_by_workflow(workflow_id, limit=limit)}


@app.post("/api/v1/workflows")
@app.post("/workflows")
def workflow_create(
    payload: WorkflowCreateRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return create_workflow_draft(payload, actor=_actor(token), environment=OPS_ENVIRONMENT)
    except ValueError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions")
@app.post("/workflows/{workflow_id}/versions")
def workflow_version_create(
    workflow_id: str,
    payload: WorkflowVersionCreateRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return create_workflow_version(
            workflow_id=workflow_id,
            payload=payload,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions/{version}/approve")
@app.post("/workflows/{workflow_id}/versions/{version}/approve")
def workflow_version_approve(
    workflow_id: str,
    version: str,
    payload: WorkflowApprovalRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return approve_workflow_version(
            workflow_id=workflow_id,
            version=version,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
            approval_note=payload.approval_note,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions/{version}/promote")
@app.post("/workflows/{workflow_id}/versions/{version}/promote")
def workflow_version_promote(
    workflow_id: str,
    version: str,
    payload: WorkflowPromotionRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return promote_workflow_version(
            workflow_id=workflow_id,
            version=version,
            target_environment=payload.target_environment,
            actor=_actor(token),
            approval_note=payload.approval_note,
            source_environment=payload.source_environment,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    except RuntimeError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/rollback")
@app.post("/workflows/{workflow_id}/rollback")
def workflow_rollback(
    workflow_id: str,
    payload: WorkflowRollbackRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return rollback_workflow_version(
            workflow_id=workflow_id,
            target_environment=payload.target_environment,
            actor=_actor(token),
            to_version=payload.to_version,
            reason=payload.reason,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    except RuntimeError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.delete("/api/v1/workflows/{workflow_id}")
@app.delete("/workflows/{workflow_id}")
def workflow_delete(
    workflow_id: str,
    token: dict = Depends(OPERATE_ACCESS),
    reason: str = "",
):
    try:
        return archive_workflow(
            workflow_id=workflow_id,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
            reason=reason,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.get("/analytics/export")
def export_analytics(
    format: str = "csv",
    _claims: dict = Depends(READ_ACCESS),
):
    """Export analytics data in CSV or JSON format."""
    import csv
    import io
    from datetime import datetime

    if format not in ["csv", "json"]:
        return JSONResponse(status_code=400, content={"error": "Invalid format. Use 'csv' or 'json'"})

    runs = get_runs(limit=10000)

    if format == "csv":
        output = io.StringIO()
        if runs:
            writer = csv.DictWriter(
                output,
                fieldnames=['id', 'journey', 'score', 'cost', 'created_at']
            )
            writer.writeheader()
            for run in runs:
                writer.writerow({
                    'id': run.get('id', ''),
                    'journey': run.get('journey', ''),
                    'score': run.get('score', 0),
                    'cost': run.get('cost', 0),
                    'created_at': run.get('created_at', ''),
                })
        return {
            "content": output.getvalue(),
            "filename": f"analytics-{datetime.now().strftime('%Y-%m-%d')}.csv"
        }

    return {
        "content": runs,
        "filename": f"analytics-{datetime.now().strftime('%Y-%m-%d')}.json"
    }


@app.get("/loyalty/{customer_id}")
def get_loyalty(customer_id: str, _claims: dict = Depends(READ_ACCESS)):
    from acosplatform.plugins.loyalty import get_status
    return get_status(customer_id)


@app.get("/metrics")
def ops_metrics(_claims: dict = Depends(READ_ACCESS)):
    return metrics_endpoint()


@app.get("/health")
def health():
    db_ok = check_connection()
    ui_ready = (UI_DIR / "index.html").exists()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
        "ui": "built" if ui_ready else "missing",
        "service": "ops-api",
        "environment": OPS_ENVIRONMENT,
        "version": APP_VERSION,
    }


def _validate_redirect_url(redirect_url: str) -> str:
    """
    DEF-017: Validate redirect URL against whitelist.
    Only allow specific UI paths, reject external URLs and protocol-relative URLs.
    """
    # Allowed redirect destinations within the UI
    ALLOWED_REDIRECTS = {
        "/ui/workflows",
        "/ui/agents",
        "/ui/skills",
        "/ui/channels",
        "/ui/analytics",
        "/ui/tenants",
        "/ui/demo-routes",
    }

    url = redirect_url.strip()

    # Reject protocol-relative URLs (//evil.com) and full URLs
    if url.startswith("//") or url.startswith("http://") or url.startswith("https://"):
        logger.warning(f"Invalid redirect attempt: external URL detected: {url}")
        return "/ui/workflows"  # Safe default

    # Validate against whitelist
    if url in ALLOWED_REDIRECTS:
        return url

    logger.warning(f"Invalid redirect attempt: {url} not in whitelist")
    return "/ui/workflows"  # Safe default


@app.get("/dev/auth/bootstrap", response_class=HTMLResponse)
def dev_auth_bootstrap(token: str, redirect: str = "/ui/workflows"):
    """Dev-only helper: writes ops token into browser localStorage and redirects."""
    env = OPS_ENVIRONMENT.strip().lower()
    if env not in {"dev", "development", "local", "test", "testing"}:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    # DEF-017: Validate redirect URL
    safe_redirect = _validate_redirect_url(redirect)
    token_json = json.dumps(token)
    redirect_json = json.dumps(safe_redirect)

    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>ACOS Dev Auth Bootstrap</title>
          <style>
            body {{
              font-family: Segoe UI, Arial, sans-serif;
              background: #0b1220;
              color: #e5e7eb;
              display: grid;
              place-items: center;
              min-height: 100vh;
              margin: 0;
            }}
            .card {{
              border: 1px solid #334155;
              background: #111827;
              border-radius: 12px;
              padding: 20px;
              max-width: 540px;
              width: calc(100% - 32px);
            }}
            code {{
              background: #1f2937;
              padding: 2px 6px;
              border-radius: 6px;
            }}
          </style>
        </head>
        <body>
          <div class="card">
            <h1>Switching Role Token...</h1>
            <p>Setting <code>ops_token</code> and redirecting to UI.</p>
          </div>
          <script>
            localStorage.setItem("ops_token", {token_json});
            window.location.replace({redirect_json});
          </script>
        </body>
        </html>
        """
    )


@app.get("/dev/auth/bootstrap/{role}", response_class=HTMLResponse)
def dev_auth_bootstrap_role(role: str, redirect: str = "/ui/workflows"):
    env = OPS_ENVIRONMENT.strip().lower()
    if env not in {"dev", "development", "local", "test", "testing"}:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    try:
        token = _mint_dev_role_token(role)
    except RuntimeError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    return dev_auth_bootstrap(token=token, redirect=redirect)


@app.get("/", response_class=HTMLResponse)
def serve_ui_root():
    if (UI_DIR / "index.html").exists():
        return RedirectResponse(url="/ui/", status_code=307)
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>ACOS Control Plane</title>
          <style>
            body { font-family: Segoe UI, Arial, sans-serif; padding: 40px; background: #f6f7fb; color: #1f2937; }
            .card { max-width: 720px; margin: 40px auto; background: white; border: 1px solid #d8dee9; border-radius: 16px; padding: 24px; }
            h1 { margin-top: 0; }
            code { background: #eef2ff; padding: 2px 6px; border-radius: 6px; }
          </style>
        </head>
        <body>
          <div class="card">
            <h1>ACOS Control Plane</h1>
            <p>The React UI has not been built yet.</p>
            <p>Build it from <code>apps/ops_ui_v2</code> and refresh this page.</p>
          </div>
        </body>
        </html>
        """
    )


def _serve_ui_file(path: str = ""):
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>ACOS Control Plane</title>
            </head>
            <body>
              <p>The React UI has not been built yet.</p>
            </body>
            </html>
            """,
            status_code=503,
        )

    if not path or path == "/":
        return FileResponse(index_file)

    requested = (UI_DIR / path.lstrip("/")).resolve()
    try:
        requested.relative_to(UI_DIR.resolve())
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    if requested.exists() and requested.is_file():
        return FileResponse(requested)
    return FileResponse(index_file)


@app.get("/ui", response_class=HTMLResponse)
@app.get("/ui/", response_class=HTMLResponse)
def serve_ui_index():
    return _serve_ui_file()


@app.get("/ui/{path:path}", response_class=HTMLResponse)
def serve_ui_path(path: str):
    return _serve_ui_file(path)
