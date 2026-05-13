from __future__ import annotations
from typing import Any

from acosplatform.evidence.store import EvidenceEvent, record_evidence
from acosplatform.mcp.client import MCPClient, MCPError
from acosplatform.mcp.registry import get_server
from acosplatform.tools.executor import execute_tool
from acosplatform.tools.registry import list_tools


def list_local_mcp_tools() -> list[dict[str, Any]]:
    return [{"name": t["name"], "description": t["description"], "inputSchema": {"type": "object"}} for t in list_tools()] + [
        {"name": "acos.workflow.execute", "description": "Execute an approved ACOS workflow.", "inputSchema": {"type": "object"}},
        {"name": "acos.evidence.get", "description": "Fetch evidence for a correlation or journey.", "inputSchema": {"type": "object"}},
    ]


def call_mcp_tool(server_id: str, tool_name: str, arguments: dict[str, Any] | None = None, *, context: dict[str, Any] | None = None, timeout_seconds: float = 5.0) -> dict[str, Any]:
    server = get_server(server_id)
    if not server:
        return {"status": "error", "error": f"unknown_mcp_server:{server_id}"}
    if server.get("endpoint", "").startswith("local://"):
        trace = execute_tool(tool_name, arguments, context=context)
        trace["protocol"] = "mcp"
        return trace
    try:
        result = MCPClient(server["endpoint"], token=server.get("token"), timeout_seconds=timeout_seconds).call_tool(tool_name, arguments or {})
        status = "success"
    except MCPError as exc:
        result = {"error": str(exc)}
        status = "error"
    record_evidence(EvidenceEvent(
        event_type="mcp.tool.called",
        tenant_id=(context or {}).get("tenant_id", server.get("tenant_id", "default")),
        correlation_id=(context or {}).get("correlation_id", "corr_mcp"),
        conversation_session_id=(context or {}).get("conversation_session_id"),
        journey_id=(context or {}).get("journey_id"),
        agent_id=(context or {}).get("agent_id"),
        tool_name=tool_name,
        policy_verdict="allow" if status == "success" else "error",
        payload={"server_id": server_id, "tool_name": tool_name, "arguments": arguments or {}, "result": result, "status": status},
    ))
    return {"status": status, "protocol": "mcp", "server_id": server_id, "tool_name": tool_name, "result": result}
