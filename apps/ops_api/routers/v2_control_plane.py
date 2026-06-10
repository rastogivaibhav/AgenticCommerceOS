from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from acosplatform.a2a.orchestrator import (
    CHANNEL_MODES,
    TONE_PROFILES,
    get_task as get_a2a_task,
    get_trace as get_a2a_trace,
    invoke_a2a,
    list_tasks as list_a2a_tasks,
    list_traces as list_a2a_traces,
)
from acosplatform.a2a.vendor_adapter import VENDOR_REGISTRY
from acosplatform.agents.registry import REGISTRY as V2_AGENT_REGISTRY
from acosplatform.capabilities.registry import CAPABILITY_REGISTRY as V2_CAPABILITY_REGISTRY
from acosplatform.evaluation.service import (
    get_evaluation_run as get_v2_evaluation_run,
    list_evaluations as list_v2_evaluations,
    run_evaluation as run_v2_evaluation,
    split_recommendations as v2_split_recommendations,
)
from acosplatform.finops.service import summary as v2_finops_summary
from acosplatform.governance.service import guardrails as v2_guardrail_summary
from acosplatform.memory.service import (
    get_journey_memory as v2_get_journey_memory,
    get_session_memory as v2_get_session_memory,
    list_access_events as v2_list_memory_events,
)
from acosplatform.route_to_production.service import (
    STAGES as V2_RTP_STAGES,
    route_summary as v2_route_summary,
)
from acosplatform.tools.service import TOOLS as V2_TOOLS
from apps.ops_api.dependencies import (
    DEFAULT_A2A_MESSAGE,
    require_northstar_api_key,
    require_northstar_role,
    tenant_for_context,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


class V2AgentRequest(BaseModel):
    agent_id: str | None = None
    name: str
    description: str = ""
    owner_team: str = "unassigned"
    business_owner: str = ""
    technical_owner: str = "ai-platform"
    vendor_stack: str = "internal"
    status: str = "draft"
    risk_level: str = "medium"
    supported_channels: list[str] = Field(default_factory=lambda: ["web"])
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    tone_profile: str = "john_lewis_customer_direct"
    evaluation_score: float = 0.0
    cost_budget_per_run: float = 0.05


class V2CapabilityRequest(BaseModel):
    capability_id: str | None = None
    name: str
    intent_families: list[str] = Field(default_factory=list)
    owner: str = "unassigned"
    risk_level: str = "medium"
    evaluation_threshold: float = 0.85


class V2CapabilityMapRequest(BaseModel):
    agent_id: str


class V2AgentVersionRequest(BaseModel):
    version: str | None = None
    notes: str = ""
    prompt_ref: str | None = None


class V2PromotionRequest(BaseModel):
    target_stage: str = "production"


class V2ToolRequest(BaseModel):
    tool_id: str | None = None
    name: str
    protocol: str = "REST"
    owner: str = "unassigned"
    risk_level: str = "medium"
    allowed_agents: list[str] = Field(default_factory=list)
    allowed_channels: list[str] = Field(default_factory=list)
    approval_required: bool = False


class V2MCPServerRequest(BaseModel):
    server_id: str | None = None
    name: str
    transport: str = "streamable_http"
    endpoint: str = "/mcp"
    allowed_tools: list[str] = Field(default_factory=list)


class V2EvaluationRunRequest(BaseModel):
    agent_id: str = "shopping_agent"


class V2VendorAgentRequest(BaseModel):
    vendor_agent_id: str | None = None
    name: str
    vendor: str = "mock_vendor"
    endpoint: str = "mock://vendor-agent"
    allowed_capabilities: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    enabled: bool = True
    kill_switch: bool = False


class V2A2AInvokeRequest(BaseModel):
    tenant_id: str = "default"
    customer_id: str = "demo-customer"
    channel: str = "web"
    actor_type: str = "customer"
    channel_mode: str = "customer_direct"
    vendor_agent_id: str | None = None
    message: str = DEFAULT_A2A_MESSAGE


@router.get("/agents")
def v2_agents(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    agents = V2_AGENT_REGISTRY.list_agents()
    return {
        "agents": agents,
        "summary": {
            "total": len(agents),
            "production": len([agent for agent in agents if agent.get("status") == "production"]),
            "pilot": len([agent for agent in agents if agent.get("status") == "pilot"]),
            "draft": len([agent for agent in agents if agent.get("status") == "draft"]),
        },
    }


@router.post("/agents")
def v2_create_agent(request: V2AgentRequest, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops")
    return {"agent": V2_AGENT_REGISTRY.upsert_agent(request.model_dump(exclude_none=True))}


@router.get("/agents/{agent_id}")
def v2_agent_detail(agent_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    agent = V2_AGENT_REGISTRY.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent": agent,
        "card": V2_AGENT_REGISTRY.agent_card(agent_id),
        "route_to_production": [
            route for route in v2_route_summary() if route["agent_id"] == agent_id
        ],
    }


@router.post("/agents/{agent_id}/versions")
def v2_create_agent_version(
    agent_id: str,
    request: V2AgentVersionRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    result = V2_AGENT_REGISTRY.create_version(agent_id, request.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"version": result}


@router.post("/agents/{agent_id}/promote")
def v2_promote_agent(
    agent_id: str,
    request: V2PromotionRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    result = V2_AGENT_REGISTRY.promote(agent_id, request.target_stage)
    if result.get("status") == "rejected":
        raise HTTPException(status_code=409, detail=result)
    return result


@router.post("/agents/{agent_id}/retire")
def v2_retire_agent(agent_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops")
    result = V2_AGENT_REGISTRY.retire(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent": result}


@router.get("/agents/{agent_id}/card")
def v2_agent_card(agent_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    card = V2_AGENT_REGISTRY.agent_card(agent_id)
    if not card:
        raise HTTPException(status_code=404, detail="Agent card not found")
    return {"agent_card": card}


@router.get("/capabilities")
def v2_capabilities(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    capabilities = V2_CAPABILITY_REGISTRY.list_capabilities()
    return {
        "capabilities": capabilities,
        "summary": {
            "total": len(capabilities),
            "covered": len(
                [capability for capability in capabilities if capability.get("coverage_status") == "covered"]
            ),
            "gaps": len(
                [capability for capability in capabilities if capability.get("coverage_status") == "gap"]
            ),
        },
    }


@router.post("/capabilities")
def v2_create_capability(
    request: V2CapabilityRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    return {"capability": V2_CAPABILITY_REGISTRY.upsert(request.model_dump(exclude_none=True))}


@router.get("/capabilities/coverage")
def v2_capability_coverage(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return V2_CAPABILITY_REGISTRY.coverage()


@router.post("/capabilities/{capability_id}/map-agent")
def v2_map_capability(
    capability_id: str,
    request: V2CapabilityMapRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    agent = V2_AGENT_REGISTRY.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    capabilities = list(agent.get("capabilities") or [])
    if capability_id not in capabilities:
        capabilities.append(capability_id)
    agent["capabilities"] = capabilities
    return {"agent": agent, "mapped_capability": capability_id}


@router.get("/a2a/agent-cards")
def v2_a2a_cards(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {
        "agent_cards": [
            V2_AGENT_REGISTRY.agent_card(agent["agent_id"])
            for agent in V2_AGENT_REGISTRY.list_agents()
        ]
    }


@router.post("/a2a/invoke")
def v2_a2a_invoke(request: V2A2AInvokeRequest, auth=Depends(require_northstar_api_key)):
    tenant_for_context(auth, request.tenant_id)
    require_northstar_role(auth, "admin", "ops")
    return {
        "trace": invoke_a2a(
            message=request.message,
            tenant_id=request.tenant_id,
            customer_id=request.customer_id,
            channel=request.channel,
            actor_type=request.actor_type,
            channel_mode=request.channel_mode,
            vendor_agent_id=request.vendor_agent_id,
        )
    }


@router.get("/a2a/traces")
def v2_a2a_traces(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"traces": list_a2a_traces(auth.tenant_id)}


@router.get("/a2a/traces/{trace_id}")
def v2_a2a_trace_detail(trace_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    trace = get_a2a_trace(trace_id)
    if not trace or ("admin" not in auth.roles and trace.get("tenant_id") != auth.tenant_id):
        raise HTTPException(status_code=404, detail="A2A trace not found")
    return {"trace": trace}


@router.post("/a2a/tasks")
def v2_a2a_create_task(
    request: V2A2AInvokeRequest,
    auth=Depends(require_northstar_api_key),
):
    tenant_for_context(auth, request.tenant_id)
    require_northstar_role(auth, "admin", "ops")
    trace = invoke_a2a(
        message=request.message,
        tenant_id=request.tenant_id,
        customer_id=request.customer_id,
        channel=request.channel,
        actor_type=request.actor_type,
        channel_mode=request.channel_mode,
        vendor_agent_id=request.vendor_agent_id,
    )
    return {"trace_id": trace["trace_id"], "tasks": trace.get("tasks", []), "trace": trace}


@router.get("/a2a/tasks/{task_id}")
def v2_a2a_task_detail(task_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    task = get_a2a_task(task_id, auth.tenant_id) or get_a2a_task(task_id, "default")
    if not task:
        raise HTTPException(status_code=404, detail="A2A task not found")
    return {"task": task}


@router.get("/a2a/tasks")
def v2_a2a_tasks(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"tasks": list_a2a_tasks(auth.tenant_id)}


@router.get("/channel-modes")
def v2_channel_modes(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"channel_modes": [{"id": key, **value} for key, value in CHANNEL_MODES.items()]}


@router.get("/tone-profiles")
def v2_tone_profiles(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"tone_profiles": TONE_PROFILES}


@router.get("/tools")
def v2_tools(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"tools": V2_TOOLS.list_tools()}


@router.post("/tools")
def v2_create_tool(request: V2ToolRequest, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops")
    return {"tool": V2_TOOLS.upsert_tool(request.model_dump(exclude_none=True))}


@router.get("/mcp/servers")
def v2_mcp_servers(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"mcp_servers": V2_TOOLS.list_mcp_servers()}


@router.post("/mcp/servers")
def v2_create_mcp_server(
    request: V2MCPServerRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    return {"mcp_server": V2_TOOLS.upsert_mcp_server(request.model_dump(exclude_none=True))}


@router.get("/memory/session/{session_id}")
def v2_session_memory(session_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"memory": v2_get_session_memory(session_id, auth.tenant_id)}


@router.get("/memory/journey/{journey_id}")
def v2_journey_memory(journey_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"memory": v2_get_journey_memory(journey_id, auth.tenant_id)}


@router.get("/memory/access-events")
def v2_memory_events(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"access_events": v2_list_memory_events(auth.tenant_id)}


@router.get("/evaluations")
def v2_evaluations(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {
        "evaluations": list_v2_evaluations(),
        "split_recommendations": v2_split_recommendations(),
    }


@router.post("/evaluations/run")
def v2_run_evaluation(
    request: V2EvaluationRunRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops", "evaluator")
    return {"evaluation_run": run_v2_evaluation(request.agent_id, auth.tenant_id)}


@router.get("/evaluations/{run_id}")
def v2_evaluation_detail(run_id: str, auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    run = get_v2_evaluation_run(run_id, auth.tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return {"evaluation_run": run}


@router.get("/guardrails")
def v2_guardrails(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return v2_guardrail_summary()


@router.get("/finops")
def v2_finops(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return v2_finops_summary()


@router.get("/route-to-production")
def v2_route_to_production(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"stages": V2_RTP_STAGES, "agents": v2_route_summary()}


@router.get("/estate-summary")
def v2_estate_summary(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    agents = V2_AGENT_REGISTRY.list_agents()
    capabilities = V2_CAPABILITY_REGISTRY.list_capabilities()
    traces = list_a2a_traces(auth.tenant_id)
    return {
        "summary": {
            "agents": len(agents),
            "capabilities": len(capabilities),
            "covered_capabilities": len(
                [capability for capability in capabilities if capability.get("coverage_status") == "covered"]
            ),
            "a2a_traces": len(traces),
            "production_agents": len(
                [agent for agent in agents if agent.get("status") == "production"]
            ),
            "shared_tools": len(V2_TOOLS.list_tools()),
        },
        "demo_message": DEFAULT_A2A_MESSAGE,
    }


@router.get("/vendor-agents")
def v2_vendor_agents(auth=Depends(require_northstar_api_key)):
    require_northstar_role(auth, "admin", "ops", "analyst", "viewer")
    return {"vendor_agents": VENDOR_REGISTRY.list()}


@router.post("/vendor-agents")
def v2_register_vendor_agent(
    request: V2VendorAgentRequest,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    return {"vendor_agent": VENDOR_REGISTRY.register(request.model_dump(exclude_none=True))}


@router.post("/vendor-agents/{vendor_agent_id}/kill-switch")
def v2_vendor_kill_switch(
    vendor_agent_id: str,
    enabled: bool = False,
    auth=Depends(require_northstar_api_key),
):
    require_northstar_role(auth, "admin", "ops")
    result = VENDOR_REGISTRY.kill(vendor_agent_id, enabled=enabled)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor agent not found")
    return {"vendor_agent": result}
