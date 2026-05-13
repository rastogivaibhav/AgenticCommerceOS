from __future__ import annotations
from typing import Any

_SERVERS: dict[str, dict[str, Any]] = {
    "local-retail": {"id": "local-retail", "name": "Local Retail MCP", "endpoint": "local://retail", "tenant_id": "default", "status": "active"}
}

def register_server(server: dict[str, Any]) -> dict[str, Any]:
    if "id" not in server:
        raise ValueError("MCP server requires id")
    _SERVERS[server["id"]] = server
    return server

def get_server(server_id: str) -> dict[str, Any] | None:
    return _SERVERS.get(server_id)

def list_servers(tenant_id: str | None = None) -> list[dict[str, Any]]:
    servers = list(_SERVERS.values())
    if tenant_id:
        servers = [s for s in servers if s.get("tenant_id") in {tenant_id, "default"}]
    return servers
