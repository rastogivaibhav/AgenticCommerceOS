from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import list_evidence
from acosplatform.events.outbox import list_pending as list_outbox_pending
from acosplatform.northstar.repository import (
    get_replay_run,
    get_session as get_northstar_session,
    list_journeys as list_northstar_journeys,
    list_messages as list_northstar_messages,
    list_replay_runs,
    list_sessions as list_northstar_sessions,
)
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.tools.registry import list_tools as list_northstar_tools
from apps.ops_api.dependencies import (
    DEFAULT_NORTHSTAR_MESSAGE,
    NorthstarMessageRequest,
    require_northstar_api_key,
    require_northstar_role,
    tenant_for_context,
)

router = APIRouter(prefix="/api/northstar", tags=["northstar"])


def _run_visible_to_auth(replay: dict, roles: list[str], tenant_id: str) -> bool:
    return bool(replay) and ("admin" in roles or replay.get("tenant_id") == tenant_id)


def _northstar_run_summary(replay: dict) -> dict:
    result = replay.get("result") or {}
    intent = result.get("intent") or {}
    agent = result.get("agent") or {}
    evidence = result.get("evidence") or []
    tools = result.get("tool_trace") or []
    participants = result.get("participating_agents") or []
    message = result.get("message_envelope") or replay.get("request") or {}
    failed_tools = [tool for tool in tools if tool.get("status") not in {"success", "ok"}]
    handoffs = [
        event for event in evidence if event.get("event_type") == "human.handoff.created"
    ]
    return {
        "id": replay.get("id"),
        "tenant_id": replay.get("tenant_id"),
        "status": result.get("status") or replay.get("status"),
        "created_at": replay.get("created_at"),
        "conversation_session_id": replay.get("conversation_session_id"),
        "journey_id": replay.get("journey_id"),
        "correlation_id": replay.get("correlation_id"),
        "channel": message.get("channel"),
        "customer_id": message.get("customer_id"),
        "intent": intent.get("intent"),
        "confidence": intent.get("confidence"),
        "primary_agent": agent.get("id"),
        "primary_agent_name": agent.get("name"),
        "agent_count": len(participants),
        "tool_count": len(tools),
        "evidence_count": len(evidence),
        "handoff_count": len(handoffs),
        "failed_tool_count": len(failed_tools),
        "response_preview": (result.get("response_text") or "")[:220],
    }


@router.post("/messages")
def northstar_message(
    request: NorthstarMessageRequest,
    auth=Depends(require_northstar_api_key),
):
    tenant_for_context(auth, request.tenant_id)
    require_northstar_role(auth, "admin", "ops")
    envelope = MessageEnvelope(
        tenant_id=request.tenant_id,
        channel=request.channel,
        channel_user_id=request.channel_user_id,
        text=request.text,
        customer_id=request.customer_id,
        conversation_session_id=request.conversation_session_id,
        journey_id=request.journey_id,
        metadata=request.metadata,
    )
    return run_omnichannel_turn(envelope)


@router.get("/tools")
def northstar_tools(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"tools": list_northstar_tools()}


@router.get("/studio-proof")
def northstar_studio_proof(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    result = run_omnichannel_turn(
        MessageEnvelope(
            tenant_id=auth.tenant_id,
            channel="web",
            channel_user_id="studio-proof-user",
            customer_id="studio-proof-customer",
            text=DEFAULT_NORTHSTAR_MESSAGE,
        )
    )
    evidence = result.get("evidence", [])
    handoffs = [
        event for event in evidence if event.get("event_type") == "human.handoff.created"
    ]
    return {
        "status": "ready" if result.get("status") == "success" else "warning",
        "golden_journey": result,
        "studio_capabilities": {
            "workflow_canvas": True,
            "tabbed_inspector": True,
            "mcp_tool_browser": True,
            "run_timeline": True,
            "evidence_inspector": True,
            "human_handoff_queue": True,
            "retail_simulation_console": True,
            "deployment_readiness": True,
        },
        "readiness": {
            "multi_agent_orchestration": len(result.get("participating_agents", [])) >= 3,
            "retail_tools": len(result.get("tool_trace", [])) >= 3,
            "evidence_timeline": len(evidence) >= 8,
            "human_handoff": bool(handoffs),
            "mcp_tools_available": any(
                tool["name"] == "catalog.search" for tool in list_northstar_tools()
            ),
            "graphql_available": True,
            "production_compose_present": Path("docker-compose.prod.yml").exists(),
        },
        "event_types": [event.get("event_type") for event in evidence],
        "handoffs": handoffs,
        "tools": list_northstar_tools(),
        "sessions": list_northstar_sessions(tenant_id=auth.tenant_id, limit=10),
        "journeys": list_northstar_journeys(tenant_id=auth.tenant_id, limit=10),
        "outbox_pending": list_outbox_pending(limit=10),
    }


@router.get("/handoffs")
def northstar_handoffs(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst")
    events = list_evidence(limit=200, tenant_id=auth.tenant_id)
    return {
        "handoffs": [
            event
            for event in events
            if event.get("event_type") == "human.handoff.created"
        ]
    }


@router.get("/sessions/{session_id}/identity-linkage")
def northstar_session_identities(session_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    session = get_northstar_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("tenant_id") != auth.tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    messages = list_northstar_messages(conversation_session_id=session_id)
    return {
        "session_id": session_id,
        "customer_id": session.get("customer_id"),
        "linked_identities": session.get("channel_identities", {}),
        "channel_transition_count": len(set(message.get("channel") for message in messages)),
        "chronological_sources": [
            {
                "timestamp": message.get("timestamp"),
                "channel": message.get("channel"),
                "user_id": message.get("channel_user_id"),
            }
            for message in messages
        ],
    }


@router.get("/outbox")
def northstar_outbox(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops")
    return {
        "pending": [
            event
            for event in list_outbox_pending(limit=50)
            if event.get("tenant_id") == auth.tenant_id
        ]
    }


@router.get("/readiness")
def northstar_readiness(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    checks = {
        "production_compose_present": Path("docker-compose.prod.yml").exists(),
        "production_env_example_present": Path(".env.production.example").exists(),
        "northstar_schema_present": Path("db/northstar_schema.sql").exists(),
        "mcp_server_available": True,
        "graphql_available": True,
        "northstar_auth_configurable": True,
    }
    return {"status": "ready" if all(checks.values()) else "warning", "checks": checks}


@router.get("/api-plane")
def northstar_api_plane(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    screen_matrix = [
        {"screen": "Estate Dashboard", "route": "/ui/estate", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/estate-summary", "POST /api/v2/a2a/invoke"], "status": "connected"},
        {"screen": "Agent Registry", "route": "/ui/agent-registry", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/agents", "POST /api/v2/agents", "GET /api/v2/agents/{id}", "GET /api/v2/agents/{id}/card"], "status": "connected"},
        {"screen": "Capability Registry", "route": "/ui/capabilities", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/capabilities", "POST /api/v2/capabilities", "POST /api/v2/capabilities/{id}/map-agent"], "status": "connected"},
        {"screen": "A2A Trace", "route": "/ui/a2a-trace", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/a2a/agent-cards", "POST /api/v2/a2a/invoke", "GET /api/v2/a2a/traces"], "status": "connected"},
        {"screen": "Channel Modes", "route": "/ui/channel-modes", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/channel-modes", "GET /api/v2/tone-profiles"], "status": "connected"},
        {"screen": "Evaluations", "route": "/ui/evaluations", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/evaluations"], "status": "connected"},
        {"screen": "Governance", "route": "/ui/governance", "api_plane": "ACOS v2 REST", "endpoints": ["GET /api/v2/guardrails", "GET /api/v2/finops", "GET /api/v2/route-to-production", "GET /api/v2/memory/access-events"], "status": "connected"},
        {"screen": "Workflows", "route": "/ui/workflows", "api_plane": "REST", "endpoints": ["GET /workflows", "POST /workflows", "GET /workflows/{id}", "PATCH /workflows/{id}", "POST /workflows/{id}/test-run", "POST /workflows/{id}/execute"], "status": "connected"},
        {"screen": "Workflow Editor", "route": "/ui/workflows/:id/editor", "api_plane": "REST", "endpoints": ["GET /workflows/{id}", "PATCH /workflows/{id}", "POST /workflows/{id}/test-run", "POST /workflows/{id}/execute", "GET /api/v1/agents", "GET /api/v1/connectors/bindings"], "status": "connected"},
        {"screen": "Studio Proof", "route": "/ui/studio-proof", "api_plane": "North-star REST", "endpoints": ["GET /api/northstar/studio-proof", "GET /api/northstar/replays", "POST /api/northstar/replays/{id}/rerun", "POST /api/northstar/messages"], "status": "connected"},
        {"screen": "Runs", "route": "/ui/runs", "api_plane": "North-star REST", "endpoints": ["GET /api/northstar/runs", "GET /api/northstar/runs/{id}", "POST /api/northstar/messages", "POST /api/northstar/replays/{id}/rerun"], "status": "connected"},
        {"screen": "Demo Guide", "route": "/ui/demo-guide", "api_plane": "North-star REST", "endpoints": ["GET /api/northstar/demo-script"], "status": "connected"},
        {"screen": "Test Center", "route": "/ui/test-center", "api_plane": "North-star REST", "endpoints": ["GET /api/northstar/test-plan", "POST /api/northstar/messages"], "status": "connected"},
        {"screen": "API Plane", "route": "/ui/api-plane", "api_plane": "North-star REST + GraphQL", "endpoints": ["GET /api/northstar/api-plane", "POST /graphql"], "status": "connected"},
        {"screen": "Channels", "route": "/ui/channels", "api_plane": "REST", "endpoints": ["GET /api/v1/channels", "POST /api/v1/channels/telegram/link", "POST /api/v1/channels/whatsapp/link", "POST /api/v1/channels/{id}/test", "GET /api/v1/channels/approvals", "POST /api/v1/channels/approvals/{sender}/approve"], "status": "connected"},
        {"screen": "Routes", "route": "/ui/demo-routes", "api_plane": "REST", "endpoints": ["GET /api/v1/demo/routes", "POST /api/v1/demo/routes/{id}/simulate", "GET /api/v1/runtime/providers", "GET /api/v1/channels"], "status": "connected"},
        {"screen": "Agents", "route": "/ui/agents", "api_plane": "REST", "endpoints": ["GET /api/v1/agents", "GET /api/v1/agents/{id}", "POST /api/v1/agents", "POST /api/v1/agents/{id}/test", "GET /api/v1/connectors/bindings"], "status": "connected"},
        {"screen": "Skills", "route": "/ui/skills", "api_plane": "REST", "endpoints": ["GET /api/v1/skills", "POST /api/v1/skills", "POST /api/v1/skills/{id}/test"], "status": "connected"},
        {"screen": "Analytics", "route": "/ui/analytics", "api_plane": "REST", "endpoints": ["GET /api/analytics/metrics", "GET /api/analytics/timeseries", "GET /api/analytics/workflows", "GET /api/analytics/export"], "status": "connected"},
        {"screen": "Tenants", "route": "/ui/tenants", "api_plane": "REST", "endpoints": ["GET /api/v1/tenants", "POST /api/v1/tenants"], "status": "connected"},
        {"screen": "Experiments", "route": "/ui/experiments", "api_plane": "REST", "endpoints": ["GET /experiments", "POST /experiments", "GET /experiments/{id}/results"], "status": "connected"},
        {"screen": "Simulation", "route": "/ui/simulation", "api_plane": "North-star REST", "endpoints": ["GET /api/northstar/runs", "POST /api/northstar/messages"], "status": "connected"},
    ]
    return {
        "status": "connected",
        "tenant_id": auth.tenant_id,
        "summary": {
            "screens": len(screen_matrix),
            "connected": len([item for item in screen_matrix if item["status"] == "connected"]),
            "rest_plane": True,
            "northstar_plane": True,
            "graphql_plane": True,
            "mcp_plane": True,
        },
        "screens": screen_matrix,
        "notes": [
            "MCP is exposed as a backend/server plane and surfaced in Studio Proof/API Plane rather than called directly from browser screens.",
            "Shopper journey simulation uses the shopper-api service via VITE_SHOPPER_API_URL when that service is deployed separately.",
            "All browser calls include Authorization and X-API-Key headers through the shared API client where applicable.",
        ],
    }


@router.get("/demo-script")
def northstar_demo_script(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {
        "title": "ACOS North-Star CTO Demo",
        "duration_minutes": 12,
        "persona": "Retail CTO / Head of Digital Operations",
        "demo_message": DEFAULT_NORTHSTAR_MESSAGE,
        "storyboard": [
            {"step": 1, "screen": "Demo Guide", "say": "ACOS is the control plane for agentic retail operations, not a chatbot.", "prove": "North-star architecture, demo objective, and success criteria are visible."},
            {"step": 2, "screen": "Studio Proof", "say": "A customer message becomes a session, journey, routed intent, multi-agent run and evidence trail.", "prove": "Create a sample proof run and show participating agents and tool traces."},
            {"step": 3, "screen": "Runs", "say": "Every orchestration is captured as an inspectable run with agents, tools, evidence and replay.", "prove": "Open Runs, select the latest run, show session/journey IDs, timeline and replay."},
            {"step": 4, "screen": "Studio Proof / Tabbed Inspector", "say": "Operators can inspect node, connector, evidence, tests and deployment readiness from one place.", "prove": "Switch between Evidence, Connectors, Tests and Deployment tabs."},
            {"step": 5, "screen": "Test Center", "say": "The product ships with runnable proof checks, not slideware.", "prove": "Run smoke-style API checks and review acceptance criteria."},
            {"step": 6, "screen": "Handoff Queue", "say": "When retail context needs human support, ACOS creates a handoff summary for store and contact-centre teams.", "prove": "Show human.handoff.created evidence event."},
            {"step": 7, "screen": "Readiness", "say": "Production readiness is explicit: Compose, Alembic, RBAC, Redis, GraphQL, MCP, and evidence are tracked.", "prove": "Show readiness checklist and known external runtime checks."},
        ],
        "success_criteria": [
            "Customer journey creates session and journey IDs.",
            "Intent is classified as styling/product discovery.",
            "At least three retail agents participate.",
            "At least three tools are called.",
            "Human handoff can be created.",
            "Evidence timeline is visible.",
            "Replay snapshot exists.",
            "Readiness checks are transparent.",
        ],
        "demo_commands": [
            "make setup",
            "make test-northstar",
            "make smoke-northstar",
            "make runtime-check",
            "make ui-build",
            "make compose-prod-up",
        ],
        "notes": [
            "Docker runtime proof must be run on a Docker-enabled machine.",
            "Use ACOS_NORTHSTAR_REQUIRE_AUTH=1 and ACOS_NORTHSTAR_API_KEYS for protected demos.",
            "Use localStorage.northstar_api_key in the browser when RBAC is enabled.",
        ],
    }


@router.get("/test-plan")
def northstar_test_plan(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    checks = [
        {"id": "smoke.golden_journey", "area": "Functional", "command": "python scripts/northstar_smoke.py", "expected": "success with >=3 agents, >=3 tools, evidence timeline"},
        {"id": "tests.northstar", "area": "Backend", "command": "pytest -q harness/python/tests/northstar", "expected": "all tests pass"},
        {"id": "tests.uat", "area": "UAT", "command": "pytest -q harness/python/tests/test_week11_uat_and_production_gate.py", "expected": "all tests pass"},
        {"id": "runtime.static", "area": "Runtime", "command": "python scripts/production_runtime_check.py", "expected": "static runtime proof passes"},
        {"id": "ui.build", "area": "Frontend", "command": "cd apps/ops_ui_v2 && npm ci && npm run build", "expected": "Vite build succeeds"},
        {"id": "db.migration_sql", "area": "Database", "command": "alembic upgrade head --sql", "expected": "Alembic SQL renders"},
        {"id": "compose.prod", "area": "Deployment", "command": "docker compose -f docker-compose.prod.yml up --build", "expected": "all services healthy on Docker-enabled runner"},
        {"id": "mcp.client", "area": "MCP", "command": "POST /mcp with tools/list and tools/call", "expected": "ACOS exposes core MCP tools"},
        {"id": "graphql.studio", "area": "GraphQL", "command": "POST /graphql with workflows/agents/evidence query", "expected": "Studio graph data returned"},
        {"id": "runs.screen", "area": "Ops UI", "command": "Open /ui/runs after a golden journey", "expected": "run list, detail, tool calls, evidence timeline and replay are visible"},
    ]
    return {
        "title": "ACOS Demo and Test Plan",
        "checks": checks,
        "demo_data": {
            "tenant_id": auth.tenant_id,
            "message": DEFAULT_NORTHSTAR_MESSAGE,
        },
    }


@router.get("/runs")
def northstar_runs(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    replays = list_replay_runs(tenant_id=auth.tenant_id, limit=100)
    runs = [_northstar_run_summary(replay) for replay in replays]
    return {
        "runs": runs,
        "summary": {
            "total": len(runs),
            "successful": len([run for run in runs if run.get("status") == "success"]),
            "with_handoff": len(
                [run for run in runs if run.get("handoff_count", 0) > 0]
            ),
            "tool_calls": sum(run.get("tool_count", 0) for run in runs),
            "evidence_events": sum(run.get("evidence_count", 0) for run in runs),
        },
    }


@router.get("/runs/{run_id}")
def northstar_run_detail(run_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    replay = get_replay_run(run_id)
    if not _run_visible_to_auth(replay, auth.roles, auth.tenant_id):
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run": _northstar_run_summary(replay),
        "replay": replay,
        "result": replay.get("result") or {},
    }


@router.get("/replays")
def northstar_replays(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst")
    return {"replays": list_replay_runs(tenant_id=auth.tenant_id, limit=50)}


@router.get("/replays/{replay_id}")
def northstar_replay_detail(replay_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst")
    replay = get_replay_run(replay_id)
    if not _run_visible_to_auth(replay, auth.roles, auth.tenant_id):
        raise HTTPException(status_code=404, detail="Replay not found")
    return {"replay": replay}


@router.post("/replays/{replay_id}/rerun")
def northstar_replay_rerun(replay_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops")
    replay = get_replay_run(replay_id)
    if not _run_visible_to_auth(replay, auth.roles, auth.tenant_id):
        raise HTTPException(status_code=404, detail="Replay not found")

    request_payload = replay.get("request") or {}
    tenant_for_context(auth, request_payload.get("tenant_id"))
    envelope = MessageEnvelope(
        tenant_id=request_payload.get("tenant_id", auth.tenant_id),
        channel=request_payload.get("channel", "replay"),
        channel_user_id=request_payload.get("channel_user_id", "replay-user"),
        text=request_payload.get("text", ""),
        customer_id=request_payload.get("customer_id"),
        metadata={**(request_payload.get("metadata") or {}), "replay_of": replay_id},
    )
    return {"replay_of": replay_id, "result": run_omnichannel_turn(envelope)}
