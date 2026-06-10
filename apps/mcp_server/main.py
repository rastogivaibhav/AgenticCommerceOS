"""Minimal Streamable-HTTP-style JSON-RPC MCP server for ACOS tools.

This deliberately keeps to JSON-RPC request/response semantics so external agent
clients can discover and call ACOS-backed retail tools during pilots.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from acosplatform.config.startup_validation import validate_auth_configuration
from acosplatform.evidence.store import list_evidence
from acosplatform.mcp.tool_router import list_local_mcp_tools
from acosplatform.tools.executor import execute_tool
from acosplatform.workflows.executor import execute_saved_workflow
from acosplatform.auth.northstar import NorthstarAuthContext, authenticate_api_key, enforce_tenant, require_roles

def require_mcp_api_key(x_api_key: str | None = Header(default=None)) -> NorthstarAuthContext:
    """Optional RBAC guard for hosted MCP access.

    Set ACOS_MCP_REQUIRE_AUTH=1 and ACOS_MCP_API_KEYS=key:tenant:role|role2
    to require X-API-Key on /mcp. Local pilot tests remain open by default.
    """
    try:
        return authenticate_api_key(
            x_api_key,
            require_auth_env="ACOS_MCP_REQUIRE_AUTH",
            key_env="ACOS_MCP_API_KEYS",
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


app = FastAPI(title="ACOS MCP Server", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    validate_auth_configuration(service="mcp-server", environment=os.environ.get("OPS_ENVIRONMENT", "dev"))


def _require_roles_http(auth: NorthstarAuthContext, *roles: str) -> None:
    try:
        require_roles(auth, *roles)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _tenant_http(auth: NorthstarAuthContext, tenant_id: str | None) -> str:
    try:
        return enforce_tenant(auth, tenant_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _ok(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


@app.post("/mcp")
async def mcp_endpoint(request: Request, auth: NorthstarAuthContext = Depends(require_mcp_api_key)):
    payload = await request.json()
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}
    if method == "initialize":
        return JSONResponse(_ok(request_id, {"serverInfo": {"name": "acos-mcp-server", "version": "0.1.0"}, "capabilities": {"tools": {}}}))
    if method == "tools/list":
        _require_roles_http(auth, "admin", "ops", "analyst", "viewer")
        return JSONResponse(_ok(request_id, {"tools": list_local_mcp_tools()}))
    if method == "tools/call":
        _require_roles_http(auth, "admin", "ops")
        name = params.get("name")
        arguments = params.get("arguments") or {}
        context = arguments.pop("_context", {}) if isinstance(arguments, dict) else {}
        if isinstance(context, dict):
            context.setdefault("tenant_id", auth.tenant_id)
        if name == "acos.workflow.execute":
            result = execute_saved_workflow(
                workflow_id=arguments.get("workflow_id", "wf-service"),
                tenant_id=_tenant_http(auth, arguments.get("tenant_id")),
                customer_id=arguments.get("customer_id", "cust_1001"),
                environment=arguments.get("environment", "dev"),
                message=arguments.get("message", "Where is my order ORD-1001?"),
                persist_run=arguments.get("persist_run", False),
            )
        elif name == "acos.evidence.get":
            result = {
                "events": list_evidence(
                    correlation_id=arguments.get("correlation_id"),
                    journey_id=arguments.get("journey_id"),
                    tenant_id=_tenant_http(auth, arguments.get("tenant_id")),
                )
            }
        elif name and (name.startswith("catalog.") or name.startswith("inventory.") or name.startswith("orders.") or name.startswith("returns.") or name.startswith("loyalty.") or name == "case.create"):
            result = execute_tool(name, arguments, context=context)
        else:
            return JSONResponse(_error(request_id, -32601, f"Unknown ACOS MCP tool: {name}"), status_code=404)
        return JSONResponse(_ok(request_id, {"content": [{"type": "json", "json": result}], "structuredContent": result}))
    return JSONResponse(_error(request_id, -32601, f"Unknown method: {method}"), status_code=404)


@app.get("/health")
def health():
    return {"status": "ok", "service": "acos-mcp-server"}
