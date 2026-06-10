"""Workflow graph executor for connector-aware retail flows."""

from __future__ import annotations

import re
from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from acosplatform.db.repository import (
    find_crm_customer_by_phone,
    get_agent_by_id,
    get_channel_binding,
    get_crm_cases,
    get_crm_customer_by_id,
    save_crm_case,
    save_run,
)
from acosplatform.workflows.service import get_workflow_detail
from integrations.adk.provider import run_adk
from integrations.salesforce.client import execute_salesforce_action
from integrations.shopify.client import execute_shopify_action
from integrations.telegram.client import send_telegram_message
from integrations.whatsapp.client import execute_whatsapp_action
from acosplatform.mcp.tool_router import call_mcp_tool
from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.orchestration.router import classify_intent
from acosplatform.orchestration.agent_registry import get_agent as get_northstar_agent
from acosplatform.evidence.store import EvidenceEvent, record_evidence

ORDER_RE = re.compile(r"\b(ORD[-\s]?\d+)\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


def execute_saved_workflow(
    *,
    workflow_id: str,
    tenant_id: str,
    customer_id: str,
    environment: str,
    message: str,
    order_id: str | None = None,
    channel_binding_id: str | None = None,
    sender_external_id: str | None = None,
    requested_provider: str | None = None,
    allow_live_send: bool = False,
    persist_run: bool = True,
) -> dict[str, Any]:
    detail = get_workflow_detail(workflow_id, environment=environment)
    if not detail:
        raise ValueError("Workflow not found")

    workflow_record = detail.get("workflow") or {}
    selected_version = _pick_selected_version(detail)
    graph = _extract_graph(selected_version)
    if not graph:
        raise ValueError("Workflow graph is missing")

    customer = get_crm_customer_by_id(customer_id)
    if not customer and sender_external_id:
        customer = find_crm_customer_by_phone(_strip_channel_prefix(sender_external_id))
    resolved_customer_id = customer.get("id") if customer else customer_id
    resolved_order_id = order_id or _extract_order_id(message) or (customer or {}).get("last_order_id") or ""
    crm_cases = get_crm_cases(resolved_customer_id) if resolved_customer_id else []
    channel_binding = get_channel_binding(channel_binding_id) if channel_binding_id else None

    state: dict[str, Any] = {
        "tenant_id": tenant_id,
        "environment": environment,
        "message": message,
        "workflow_id": workflow_id,
        "workflow_family": workflow_record.get("workflow_family") or "service",
        "workflow_version": selected_version.get("version") if selected_version else None,
        "channel_binding_id": channel_binding_id,
        "channel_binding": channel_binding or {},
        "sender_external_id": sender_external_id or "",
        "customer": customer,
        "customer_id": resolved_customer_id,
        "order_id": resolved_order_id,
        "crm_cases": list(crm_cases or []),
        "tool_trace": [],
        "node_trace": [],
        "node_results": {},
        "response_text": "",
        "channel_reply": None,
        "human_escalation": None,
        "intent": None,
        "handoffs": [],
        "outcome": None,
    }

    execution = _execute_graph(graph, state, requested_provider=requested_provider, allow_live_send=allow_live_send)
    run_id = f"wf-exec-{uuid4().hex[:10]}"
    result_payload = {
        "workflow_id": workflow_id,
        "workflow_version": state["workflow_version"],
        "node_trace": state["node_trace"],
        "tool_trace": state["tool_trace"],
        "response_text": state["response_text"],
        "channel_reply": state["channel_reply"],
        "human_escalation": state["human_escalation"],
        "outcome": state["outcome"],
        "customer": state["customer"],
        "crm_cases": state["crm_cases"],
        "graph_execution": execution,
    }

    if persist_run:
        save_run(
            run_id=run_id,
            tenant_id=tenant_id,
            customer_id=resolved_customer_id or "anon",
            journey="workflow_execution",
            input_data={
                "message": message,
                "order_id": resolved_order_id,
                "channel_binding_id": channel_binding_id,
                "sender_external_id": sender_external_id,
            },
            output_data=result_payload,
            workflow_id=workflow_id,
            workflow_version=state["workflow_version"],
            environment_id=environment,
            agent_metadata={"node_trace": state["node_trace"]},
            skill_metadata={"tool_trace": state["tool_trace"]},
        )

    return {
        "status": "success",
        "run_id": run_id,
        "journey": workflow_record.get("workflow_family") or "service",
        "workflow": {
            "requested_workflow_id": workflow_id,
            "workflow_id": workflow_id,
            "workflow_version": state["workflow_version"],
            "environment_id": environment,
            "resolution": "graph_active",
        },
        "result": result_payload,
        "customer": state["customer"],
        "response_text": state["response_text"],
        "channel_reply": state["channel_reply"],
        "crm_cases": state["crm_cases"],
        "node_trace": state["node_trace"],
        "tool_trace": state["tool_trace"],
    }


def _pick_selected_version(detail: dict[str, Any]) -> dict[str, Any]:
    versions = detail.get("versions") or []
    active_version = (detail.get("workflow") or {}).get("active_version")
    selected_version = next((item for item in versions if item.get("version") == active_version), None)
    if selected_version is None and versions:
        selected_version = versions[-1]
    return selected_version or {}


def _extract_graph(version: dict[str, Any]) -> dict[str, Any]:
    step_definitions = version.get("step_definitions")
    if isinstance(step_definitions, list):
        return next((entry for entry in step_definitions if isinstance(entry, dict) and "nodes" in entry), {}) or {}
    if isinstance(step_definitions, dict):
        return step_definitions
    return {}


def _execute_graph(
    graph: dict[str, Any],
    state: dict[str, Any],
    *,
    requested_provider: str | None,
    allow_live_send: bool,
) -> dict[str, Any]:
    nodes = {node.get("id"): node for node in (graph.get("nodes") or []) if node.get("id")}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming_count: dict[str, int] = {node_id: 0 for node_id in nodes}
    for edge in graph.get("edges") or []:
        source = edge.get("source")
        target = edge.get("target")
        if source not in nodes or target not in nodes:
            continue
        outgoing.setdefault(source, []).append(edge)
        incoming_count[target] = incoming_count.get(target, 0) + 1

    queue = deque(node_id for node_id, count in incoming_count.items() if count == 0)
    skipped_targets: set[str] = set()

    while queue:
        node_id = queue.popleft()
        node = nodes[node_id]
        result = _execute_node(node, state, requested_provider=requested_provider, allow_live_send=allow_live_send)
        state["node_results"][node_id] = result
        state["node_trace"].append(
            {
                "node_id": node_id,
                "node_type": node.get("type"),
                "label": (node.get("data") or {}).get("label") or node_id,
                **result,
            }
        )

        active_edges = outgoing.get(node_id, [])
        if node.get("type") == "decisionNode":
            decision_label = str(result.get("selected_branch") or "").strip().lower()
            filtered_edges = []
            for edge in active_edges:
                edge_label = str((edge.get("data") or {}).get("label") or "").strip().lower()
                if edge_label == decision_label:
                    filtered_edges.append(edge)
                else:
                    skipped_targets.add(edge.get("target"))
            active_edges = filtered_edges

        for edge in active_edges:
            target = edge.get("target")
            incoming_count[target] = incoming_count.get(target, 0) - 1
            if incoming_count[target] <= 0 and target not in skipped_targets:
                queue.append(target)

    return {
        "completed_nodes": len(state["node_trace"]),
        "outcome": state["outcome"] or "completed",
    }


def _execute_node(
    node: dict[str, Any],
    state: dict[str, Any],
    *,
    requested_provider: str | None,
    allow_live_send: bool,
) -> dict[str, Any]:
    node_type = node.get("type")
    data = node.get("data") or {}

    if node_type == "triggerNode":
        customer_phone = _preferred_sender_target(state)
        trigger = {
            "message": state["message"],
            "order_id": state["order_id"],
            "customer_id": state["customer_id"],
            "customer_phone": customer_phone,
            "channel_binding_id": data.get("bindingId") or state.get("channel_binding_id"),
            "channel": data.get("channel") or "api",
        }
        state["trigger"] = trigger
        return {"status": "ok", "result": trigger}

    if node_type == "intentNode":
        return _execute_intent_node(node, state)

    if node_type == "connectorNode":
        return _execute_connector_node(node, state, allow_live_send=allow_live_send)

    if node_type == "mcpToolNode":
        return _execute_mcp_tool_node(node, state)

    if node_type == "agentNode":
        return _execute_agent_node(node, state, requested_provider=requested_provider)

    if node_type == "decisionNode":
        return _execute_decision_node(node, state)

    if node_type in {"humanNode", "humanHandoffNode"}:
        return _execute_human_node(node, state)

    if node_type == "endNode":
        state["outcome"] = data.get("outcomeType") or "success"
        return {"status": "ok", "result": {"outcome": state["outcome"]}}

    return {"status": "warning", "result": {"message": f"Unsupported node type {node_type}"}}



def _execute_intent_node(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Classify retail intent inside a workflow graph and expose it downstream."""
    data = node.get("data") or {}
    envelope = MessageEnvelope(
        tenant_id=state.get("tenant_id") or "default",
        channel=(state.get("trigger") or {}).get("channel") or data.get("channel") or "workflow",
        channel_user_id=state.get("sender_external_id") or state.get("customer_id") or "workflow-user",
        text=state.get("message") or "",
        customer_id=state.get("customer_id"),
    )
    envelope.conversation_session_id = state.get("conversation_session_id")
    envelope.journey_id = state.get("journey_id")
    envelope.correlation_id = state.get("correlation_id", f"corr_{state.get('workflow_id', 'workflow')}")
    intent = classify_intent(envelope)
    state["intent"] = intent.to_dict()
    state["recommended_agent_id"] = intent.recommended_agent
    return {"status": "ok", "result": state["intent"], "confidence": intent.confidence}

def _execute_connector_node(node: dict[str, Any], state: dict[str, Any], *, allow_live_send: bool) -> dict[str, Any]:
    data = node.get("data") or {}
    connector_type = (data.get("connectorType") or "").strip().lower()
    action = (data.get("action") or "").strip().lower()
    config = _render_value(data.get("config") or {}, state)
    binding_id = data.get("bindingId") or ""
    binding = get_channel_binding(binding_id) if binding_id in {"whatsapp-support", "telegram-ops"} else None
    metadata = (binding or {}).get("metadata") or {}

    if connector_type == "shopify":
        payload = {
            **config,
            "order_id": config.get("order_id") or state.get("order_id"),
            "customer_id": config.get("customer_id") or (state.get("customer") or {}).get("shopify_customer_id"),
            "product_id": config.get("product_id"),
        }
        run = execute_shopify_action(action, payload, timeout_seconds=2.0, retries=0)
        record = _tool_record(node.get("id"), connector_type, action, binding_id, run)
        state["tool_trace"].append(record)
        if action == "get_order":
            state["order"] = run.get("result") or {}
        return {"status": run.get("status", "ok"), "mode": run.get("mode", "sandbox"), "result": run.get("result") or {}, "note": run.get("note")}

    if connector_type == "salesforce":
        payload = {
            **config,
            "contact_id": config.get("contact_id")
            or (state.get("customer") or {}).get("salesforce_contact_id")
            or config.get("contact_key")
            or "",
            "case_id": config.get("case_id"),
            "subject": config.get("subject") or f"Workflow action for {(state.get('customer') or {}).get('name') or 'customer'}",
            "message": state.get("message"),
        }
        run = execute_salesforce_action(action, payload, timeout_seconds=2.0)
        record = _tool_record(node.get("id"), connector_type, action, binding_id, run)
        state["tool_trace"].append(record)
        if action == "get_contact":
            state["salesforce_contact"] = run.get("result") or {}
        if action in {"create_case", "update_case"}:
            state["human_escalation"] = run.get("result") or {}
        return {"status": run.get("status", "ok"), "mode": run.get("mode", "sandbox"), "result": run.get("result") or {}, "note": run.get("note")}

    if connector_type == "whatsapp":
        payload = {
            **config,
            "to": config.get("to") or _preferred_sender_target(state),
            "message": config.get("message") or state.get("response_text") or _compose_response_text(state),
        }
        run = execute_whatsapp_action(
            action,
            payload,
            timeout_seconds=2.0,
            allow_live_send=allow_live_send,
            config_override=metadata or None,
        )
        record = _tool_record(node.get("id"), connector_type, action, binding_id, run)
        state["tool_trace"].append(record)
        state["channel_reply"] = run
        return {"status": run.get("status", "ok"), "mode": run.get("mode", "sandbox"), "result": run.get("result") or {}, "note": run.get("note")}

    if connector_type == "mcp":
        server_id = config.get("server_id") or data.get("serverId") or "local-retail"
        tool_name = config.get("tool_name") or data.get("toolName") or action
        arguments = config.get("arguments") or {k: v for k, v in config.items() if k not in {"server_id", "tool_name", "timeout_seconds"}}
        run = call_mcp_tool(server_id, tool_name, arguments, context={"tenant_id": state.get("tenant_id"), "customer_id": state.get("customer_id"), "correlation_id": state.get("correlation_id", "corr_workflow"), "journey_id": state.get("journey_id"), "message": state.get("message")}, timeout_seconds=float(config.get("timeout_seconds") or 5.0))
        record = _tool_record(node.get("id"), "mcp", tool_name, binding_id, {"status": run.get("status", "success"), "mode": "mcp", "result": run.get("result") or run, "note": run.get("error")})
        state["tool_trace"].append(record)
        state.setdefault("mcp_results", {})[node.get("id") or tool_name] = record.get("result") or {}
        return {"status": record.get("status", "success"), "mode": "mcp", "result": record.get("result") or {}, "note": record.get("note")}

    if connector_type == "telegram":
        run = send_telegram_message(
            config.get("message") or state.get("response_text") or _compose_response_text(state),
            chat_id=config.get("chat_id"),
        )
        record = {
            "node_id": node.get("id"),
            "system": "telegram",
            "tool": "send_message",
            "binding_id": binding_id,
            "mode": run.get("mode", "sandbox"),
            "status": run.get("status", "ok"),
            "note": run.get("note"),
            "result": run.get("result") or {},
        }
        state["tool_trace"].append(record)
        return {"status": run.get("status", "ok"), "mode": run.get("mode", "sandbox"), "result": run.get("result") or {}, "note": run.get("note")}

    return {"status": "warning", "mode": "sandbox", "result": {}, "note": f"unsupported_connector:{connector_type}"}



def _execute_mcp_tool_node(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    data = node.get("data") or {}
    config = _render_value(data.get("config") or {}, state)
    server_id = data.get("serverId") or data.get("server_id") or config.get("server_id") or "local-retail"
    tool_name = data.get("toolName") or data.get("tool_name") or config.get("tool_name") or data.get("action")
    arguments = config.get("arguments") or {k: v for k, v in config.items() if k not in {"server_id", "tool_name", "timeout_seconds", "failClosed"}}
    timeout_seconds = float(config.get("timeout_seconds") or data.get("timeoutSeconds") or 5.0)
    context = {
        "tenant_id": state.get("tenant_id"),
        "customer_id": state.get("customer_id"),
        "workflow_id": state.get("workflow_id"),
        "journey_id": state.get("journey_id"),
        "correlation_id": state.get("correlation_id", state.get("run_id", "corr_workflow")),
        "conversation_session_id": state.get("conversation_session_id"),
        "agent_id": (state.get("agent_result") or {}).get("agent_id"),
        "message": state.get("message"),
    }
    if not tool_name:
        return {"status": "warning", "mode": "mcp", "result": {}, "note": "missing_mcp_tool_name"}
    run = call_mcp_tool(server_id, tool_name, arguments, context=context, timeout_seconds=timeout_seconds)
    record = {
        "node_id": node.get("id"),
        "system": "mcp",
        "tool": tool_name,
        "server_id": server_id,
        "mode": "mcp",
        "status": run.get("status", "success"),
        "result": run.get("result") or run,
        "note": run.get("error"),
    }
    state.setdefault("tool_trace", []).append(record)
    state.setdefault("mcp_results", {})[node.get("id") or tool_name] = record["result"]
    if record["status"] == "error" and config.get("failClosed"):
        state["outcome"] = "failed"
        return {"status": "error", "mode": "mcp", "result": record["result"], "note": record.get("note")}
    return {"status": record["status"], "mode": "mcp", "result": record["result"], "note": record.get("note")}


def _execute_agent_node(node: dict[str, Any], state: dict[str, Any], *, requested_provider: str | None) -> dict[str, Any]:
    data = node.get("data") or {}
    agent_id = data.get("agentId")
    agent = get_agent_by_id(agent_id) if agent_id else None
    provider = requested_provider
    if not provider and agent:
        runtime = (agent.get("code") or {}).get("runtime") or {}
        provider = runtime.get("provider") or agent.get("runtime_provider")

    explanation_context = {
        "customer": state.get("customer") or {},
        "crm_cases": state.get("crm_cases") or [],
        "order": state.get("order") or {},
        "salesforce_contact": state.get("salesforce_contact") or {},
        "message": state.get("message"),
    }
    adk_result = run_adk(
        {
            "message": state.get("message"),
            "tenant_id": state.get("tenant_id"),
            "customer_id": state.get("customer_id"),
            "order_id": state.get("order_id"),
            "crm_profile": state.get("customer") or {},
            "crm_cases": state.get("crm_cases") or [],
            "tool_trace": state.get("tool_trace") or [],
            "explanation_context": explanation_context,
        },
        journey_type=state.get("workflow_family") or "service",
        requested_provider=provider,
        strict_provider=False,
    )
    state["agent_result"] = adk_result
    state["response_text"] = _compose_response_text(state)
    return {
        "status": "ok",
        "result": adk_result,
        "mode": ((adk_result.get("runtime") or {}).get("provider") or "local_fallback"),
        "confidence": _derive_confidence(state),
    }


def _execute_decision_node(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    data = node.get("data") or {}
    rule = str(data.get("routingRule") or "").strip() or "true"
    order_found = bool(state.get("order"))
    customer_found = bool(state.get("customer"))
    confidence = _derive_confidence(state)
    expression = (
        rule.replace("&&", " and ")
        .replace("||", " or ")
        .replace("true", "True")
        .replace("false", "False")
    )
    try:
        outcome = bool(
            eval(
                expression,
                {"__builtins__": {}},
                {
                    "order_found": order_found,
                    "customer_found": customer_found,
                    "confidence": confidence,
                },
            )
        )
    except Exception:
        outcome = order_found
    return {
        "status": "ok",
        "result": {
            "rule": rule,
            "order_found": order_found,
            "customer_found": customer_found,
            "confidence": confidence,
            "outcome": outcome,
        },
        "selected_branch": "yes" if outcome else "no",
    }


def _execute_human_node(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    data = node.get("data") or {}
    summary = data.get("summary") or data.get("label") or _compose_response_text(state)
    handoff = {
        "handoff_id": f"handoff-{uuid4().hex[:10]}",
        "queue": data.get("queue") or data.get("handoffQueue") or "retail_ops",
        "summary": summary,
        "customer_id": state.get("customer_id"),
        "workflow_id": state.get("workflow_id"),
        "reason": data.get("reason") or "workflow_handoff",
        "status": "open",
    }
    state["human_escalation"] = handoff
    state.setdefault("handoffs", []).append(handoff)
    try:
        record_evidence(EvidenceEvent(
            event_type="human.handoff.created",
            tenant_id=state.get("tenant_id") or "default",
            correlation_id=state.get("correlation_id", f"corr_{state.get('workflow_id', 'workflow')}"),
            conversation_session_id=state.get("conversation_session_id"),
            journey_id=state.get("journey_id"),
            workflow_id=state.get("workflow_id"),
            payload=handoff,
        ))
    except Exception:
        pass
    return {"status": "ok", "result": handoff}


def _tool_record(node_id: str, system: str, action: str, binding_id: str, run: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "system": system,
        "tool": action,
        "binding_id": binding_id,
        "mode": run.get("mode", "sandbox"),
        "status": run.get("status", "ok"),
        "note": run.get("note") or run.get("error"),
        "result": run.get("result") or {},
    }


def _compose_response_text(state: dict[str, Any]) -> str:
    customer = state.get("customer") or {}
    customer_name = customer.get("name") or "there"
    order = state.get("order") or {}
    order_id = order.get("order_id") or order.get("name") or state.get("order_id") or "your order"
    raw_status = order.get("fulfillment_status") or order.get("status") or "processing"
    status = str(raw_status).replace("_", " ")
    explanation = (((state.get("agent_result") or {}).get("explanation") or {}).get("explanation_text") or "").strip()
    if state.get("human_escalation"):
        base = f"Hi {customer_name}, I have escalated this request and created a service case for follow-up."
    else:
        base = f"Hi {customer_name}, {order_id} is currently {status}."
    return f"{base} {explanation}".strip()


def _derive_confidence(state: dict[str, Any]) -> float:
    confidence = 0.35
    if state.get("customer"):
        confidence += 0.25
    if state.get("order"):
        confidence += 0.3
    if state.get("salesforce_contact"):
        confidence += 0.1
    return min(confidence, 0.95)


def _extract_order_id(message: str) -> str:
    match = ORDER_RE.search(message or "")
    if not match:
        return ""
    return match.group(1).upper().replace(" ", "-")


def _strip_channel_prefix(value: str) -> str:
    raw = str(value or "").strip()
    if ":" not in raw:
        return raw.lstrip("+")
    return raw.split(":", 1)[1].lstrip("+")


def _preferred_sender_target(state: dict[str, Any]) -> str:
    sender_value = _strip_channel_prefix(state.get("sender_external_id") or "")
    sender_digits = "".join(char for char in sender_value if char.isdigit())
    if sender_digits:
        return sender_digits
    customer_phone = _strip_channel_prefix((state.get("customer") or {}).get("phone") or "")
    customer_digits = "".join(char for char in customer_phone if char.isdigit())
    return customer_digits or sender_value or customer_phone


def _render_value(value: Any, state: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _render_value(item, state) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_value(item, state) for item in value]
    if not isinstance(value, str):
        return value

    def replace_token(match: re.Match[str]) -> str:
        token = match.group(1)
        resolved = _lookup_token(token, state)
        if resolved is None:
            return ""
        return str(resolved)

    return TOKEN_RE.sub(replace_token, value)


def _lookup_token(token: str, state: dict[str, Any]) -> Any:
    current: Any = state
    for part in token.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
