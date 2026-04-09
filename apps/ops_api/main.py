"""Ops API for ACOS control-plane operations."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

import requests
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded

from acosplatform.audit.logger import audit
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.config.startup_validation import validate_auth_configuration
from acosplatform.billing.engine import get_cost_summary, get_usage
from acosplatform.db.connection import ensure_schema, check_connection
from acosplatform.db.repository import (
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
    save_agent,
    save_skill,
    save_audit_event,
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
from acosplatform.replay.replay_engine import replay
from integrations.adk.provider import (
    DEFAULT_MODEL,
    SUPPORTED_RUNTIME_PROVIDERS,
    get_runtime_capabilities,
    run_adk,
)
from integrations.shopify.client import probe_shopify_admin
from acosplatform.workflows.service import (
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
from apps.ops_api.routers import experiments, analytics, workflows, promotions, runs, approvals, incidents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
OPS_ENVIRONMENT = os.environ.get("OPS_ENVIRONMENT", "dev")
EMBEDDED_UI_DIR = Path("apps/ops_api/ui")
LOCAL_UI_DIR = Path("apps/ops_ui_v2/dist")
UI_DIR = EMBEDDED_UI_DIR if (EMBEDDED_UI_DIR / "index.html").exists() else LOCAL_UI_DIR


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
app.mount("/ui", StaticFiles(directory=UI_DIR, html=True, check_dir=False), name="ui")

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
app.include_router(workflows.router)
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
    if ALLOW_MOCK_ROUTES and not IS_DEV_ENV and not ALLOW_NON_DEV_MOCK_ROUTES:
        raise RuntimeError(
            "ALLOW_MOCK_ROUTES=1 is blocked in non-dev unless ALLOW_NON_DEV_MOCK_ROUTES=1 is also set."
        )
    if ALLOW_MOCK_ROUTES and not IS_DEV_ENV:
        logger.warning("Mock/test routes are enabled in non-dev environment.")
    validate_auth_configuration(service="ops-api", environment=OPS_ENVIRONMENT)
    ensure_schema()
    ensure_default_workflow_registry(environment=OPS_ENVIRONMENT)
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


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _runtime_capabilities() -> dict[str, Any]:
    return get_runtime_capabilities()


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
    "local fallback": "local_fallback",
    "local_fallback": "local_fallback",
}


def _to_provider_key(raw_provider: Any) -> str:
    if not isinstance(raw_provider, str):
        return _runtime_capabilities().get("active_provider", "local_fallback")
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
    return payload


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


@app.get("/api/v1/agents")
@app.get("/agents")
def list_agents(_claims: dict = Depends(READ_ACCESS)):
    return {"agents": get_agents(), "runtime_capabilities": _runtime_capabilities()}


@app.get("/api/v1/agents/providers")
def agent_provider_capabilities(_claims: dict = Depends(READ_ACCESS)):
    return _runtime_capabilities()


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
    saved = save_agent(target)
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
    saved = save_agent(agent)
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
    )
    runtime = adk_result.get("runtime", {})
    used_skills = adk_result.get("skills_used", [])
    configured_bound = list(agent.get("bound_skills") or agent.get("skills") or [])
    resolved_provider = provider if provider == "local_fallback" else runtime.get("provider", provider)
    duration_ms = round((perf_counter() - started) * 1000, 3)

    result = {
        "request_id": f"agt-test-{uuid4().hex[:10]}",
        "trace_id": f"trace-{uuid4().hex[:8]}",
        "timestamp": _utc_iso(),
        "status": "pass" if not adk_result.get("contract_errors") else "fail",
        "agent_id": agent_id,
        "journey_type": payload.journey_type,
        "tenant_id": payload.tenant_id,
        "runtime_provider": resolved_provider,
        "model_name": runtime.get("model_name", agent.get("model_name", DEFAULT_MODEL)),
        "agent_version": agent.get("agent_version", "v1"),
        "bound_skills": configured_bound,
        "bound_skills_executed": [skill for skill in used_skills if not configured_bound or skill in configured_bound],
        "duration_ms": duration_ms,
        "runtime": runtime,
        "adk_result": adk_result,
    }
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
    return {
        "environment": environment,
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
    return detail


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


@app.get("/dev/auth/bootstrap", response_class=HTMLResponse)
def dev_auth_bootstrap(token: str, redirect: str = "/ui/agents"):
    """Dev-only helper: writes ops token into browser localStorage and redirects."""
    env = OPS_ENVIRONMENT.strip().lower()
    if env not in {"dev", "development", "local", "test", "testing"}:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    safe_redirect = redirect if redirect.startswith("/ui/") else "/ui/"
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
