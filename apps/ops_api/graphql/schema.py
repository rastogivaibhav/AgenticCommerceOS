from __future__ import annotations

from typing import Any
import strawberry
from strawberry.fastapi import GraphQLRouter

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.db.repository import get_agents, get_runs
from acosplatform.evidence.store import list_evidence
from acosplatform.models.workflows import WorkflowApprovalRequest, WorkflowCreateRequest, WorkflowPromotionRequest
from acosplatform.orchestration.agent_registry import list_agents as list_northstar_agents
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.sessions.spine import get_journey, get_session
from acosplatform.tools.registry import list_tools
from acosplatform.workflows.service import (
    approve_workflow_version,
    create_workflow_draft,
    list_workflows_with_state,
    promote_workflow_version,
)


@strawberry.type
class KeyValue:
    key: str
    value: str


def _kv(data: dict[str, Any] | None) -> list[KeyValue]:
    return [KeyValue(key=str(k), value=str(v)) for k, v in (data or {}).items()]


@strawberry.type
class WorkflowGQL:
    id: str
    name: str
    family: str
    status: str
    environment: str
    active_version: str | None = None


@strawberry.type
class AgentGQL:
    id: str
    name: str
    role: str
    tools: list[str]


@strawberry.type
class ToolGQL:
    name: str
    description: str
    protocol: str


@strawberry.type
class RunGQL:
    id: str
    status: str
    workflow_id: str | None = None
    customer_id: str | None = None


@strawberry.type
class EvidenceGQL:
    id: str
    event_type: str
    correlation_id: str
    journey_id: str | None
    agent_id: str | None
    tool_name: str | None
    payload: list[KeyValue]


@strawberry.type
class MutationResult:
    ok: bool
    status: str
    message: str
    payload: list[KeyValue]


@strawberry.input
class WorkflowDraftInput:
    name: str
    tenant_id: str = "default"
    workflow_family: str = "discovery"
    description: str = ""
    business_owner: str = "acos-team"
    change_summary: str = "GraphQL-created workflow draft"
    environment: str = "dev"


@strawberry.input
class ApprovalInput:
    workflow_id: str
    version: str
    approval_note: str = "Approved from GraphQL Studio"
    environment: str = "dev"


@strawberry.input
class PromotionInput:
    workflow_id: str
    version: str
    target_environment: str = "dev"
    source_environment: str | None = None
    approval_note: str = "Promoted from GraphQL Studio"


@strawberry.input
class DryRunInput:
    text: str
    tenant_id: str = "default"
    channel: str = "studio"
    channel_user_id: str = "studio-user"
    customer_id: str | None = None


@strawberry.input
class GenerateAgentInput:
    intent: str
    name: str | None = None
    role: str | None = None


@strawberry.type
class Query:
    @strawberry.field
    def workflows(self, environment: str = "dev") -> list[WorkflowGQL]:
        rows = list_workflows_with_state(environment=environment)
        return [WorkflowGQL(id=str(r.get("id")), name=str(r.get("name") or r.get("id")), family=str(r.get("workflow_family") or r.get("family") or "retail"), status=str(r.get("status") or "active"), environment=environment, active_version=r.get("active_version")) for r in rows]

    @strawberry.field
    def agents(self) -> list[AgentGQL]:
        repo_agents = []
        try:
            repo_agents = get_agents()
        except Exception:
            repo_agents = []
        if repo_agents:
            return [AgentGQL(id=str(a.get("id")), name=str(a.get("name")), role=str(a.get("purpose") or a.get("role") or "Retail agent"), tools=list(a.get("bound_skills") or a.get("skills") or [])) for a in repo_agents]
        return [AgentGQL(id=a.id, name=a.name, role=a.role, tools=a.tools) for a in list_northstar_agents()]

    @strawberry.field
    def tools(self) -> list[ToolGQL]:
        return [ToolGQL(name=t["name"], description=t["description"], protocol=t["protocol"]) for t in list_tools()]

    @strawberry.field
    def runs(self, limit: int = 20) -> list[RunGQL]:
        rows = get_runs(limit=limit)
        return [RunGQL(id=str(r.get("id") or r.get("run_id")), status=str(r.get("status") or "completed"), workflow_id=r.get("workflow_id"), customer_id=r.get("customer_id")) for r in rows]

    @strawberry.field
    def evidence(self, correlation_id: str | None = None, journey_id: str | None = None) -> list[EvidenceGQL]:
        return [EvidenceGQL(id=e["id"], event_type=e["event_type"], correlation_id=e["correlation_id"], journey_id=e.get("journey_id"), agent_id=e.get("agent_id"), tool_name=e.get("tool_name"), payload=_kv(e.get("payload"))) for e in list_evidence(correlation_id=correlation_id, journey_id=journey_id)]

    @strawberry.field
    def session(self, id: str) -> list[KeyValue]:
        return _kv(get_session(id) or {})

    @strawberry.field
    def journey(self, id: str) -> list[KeyValue]:
        return _kv(get_journey(id) or {})


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_workflow_draft(self, input: WorkflowDraftInput) -> MutationResult:
        try:
            payload = WorkflowCreateRequest(
                tenant_id=input.tenant_id,
                name=input.name,
                workflow_family=input.workflow_family,  # type: ignore[arg-type]
                description=input.description,
                business_owner=input.business_owner,
                change_summary=input.change_summary,
            )
            result = create_workflow_draft(payload, actor="graphql-studio", environment=input.environment)
            workflow = result.get("workflow") or {}
            return MutationResult(ok=True, status="created", message="Workflow draft created", payload=_kv({"workflow_id": workflow.get("id"), "version": (result.get("version") or {}).get("version")}))
        except Exception as exc:
            return MutationResult(ok=False, status="error", message=str(exc), payload=[])

    @strawberry.mutation
    def run_dry_test(self, input: DryRunInput) -> MutationResult:
        envelope = MessageEnvelope(tenant_id=input.tenant_id, channel=input.channel, channel_user_id=input.channel_user_id, text=input.text, customer_id=input.customer_id)
        result = run_omnichannel_turn(envelope)
        payload = {
            "status": result.get("status"),
            "intent": (result.get("intent") or {}).get("intent"),
            "agent": (result.get("agent") or {}).get("id"),
            "participating_agents": ",".join(a.get("id", "") for a in result.get("participating_agents", [])),
            "tool_count": len(result.get("tool_trace") or []),
            "evidence_count": len(result.get("evidence") or []),
            "response_text": result.get("response_text"),
        }
        return MutationResult(ok=True, status="success", message="Dry run completed", payload=_kv(payload))

    @strawberry.mutation
    def approve_workflow(self, input: ApprovalInput) -> MutationResult:
        try:
            result = approve_workflow_version(input.workflow_id, input.version, actor="graphql-studio", environment=input.environment, approval_note=input.approval_note)
            return MutationResult(ok=True, status="approved", message="Workflow approved", payload=_kv({"workflow_id": input.workflow_id, "version": (result.get("version") or {}).get("version"), "already_approved": result.get("already_approved")}))
        except Exception as exc:
            return MutationResult(ok=False, status="error", message=str(exc), payload=[])

    @strawberry.mutation
    def promote_workflow(self, input: PromotionInput) -> MutationResult:
        try:
            result = promote_workflow_version(input.workflow_id, input.version, target_environment=input.target_environment, actor="graphql-studio", approval_note=input.approval_note, source_environment=input.source_environment)
            return MutationResult(ok=True, status="promoted", message="Workflow promoted", payload=_kv({"workflow_id": input.workflow_id, "version": (result.get("version") or {}).get("version"), "target_environment": input.target_environment}))
        except Exception as exc:
            return MutationResult(ok=False, status="error", message=str(exc), payload=[])

    @strawberry.mutation
    def generate_agent(self, input: GenerateAgentInput) -> MutationResult:
        agent_id = f"generated_{input.intent.lower().replace(' ', '_')}"
        name = input.name or f"{input.intent.replace('_', ' ').title()} Agent"
        role = input.role or f"Generated retail agent for {input.intent} journeys"
        tools = [t["name"] for t in list_tools() if input.intent.split("_")[0] in t["name"] or t["name"] in {"catalog.search", "case.create"}]
        return MutationResult(ok=True, status="generated", message="Agent generated", payload=_kv({"agent_id": agent_id, "name": name, "role": role, "tools": ",".join(tools)}))


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema)
