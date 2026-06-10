from __future__ import annotations

from typing import Any
import httpx

class MCPError(RuntimeError):
    pass

class MCPClient:
    def __init__(self, endpoint: str, *, token: str | None = None, timeout_seconds: float = 5.0):
        self.endpoint = endpoint
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"jsonrpc": "2.0", "id": "acos", "method": method, "params": params or {}}
        try:
            response = httpx.post(self.endpoint, json=payload, headers=self._headers(), timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network defensive
            raise MCPError(str(exc)) from exc
        if "error" in data:
            raise MCPError(str(data["error"]))
        return data.get("result", {})

    def initialize(self) -> dict[str, Any]:
        return self._rpc("initialize", {"client": "acos"})

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._rpc("tools/list")
        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None, timeout_seconds: float | None = None) -> dict[str, Any]:
        if timeout_seconds:
            old = self.timeout_seconds
            self.timeout_seconds = timeout_seconds
            try:
                return self._rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})
            finally:
                self.timeout_seconds = old
        return self._rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})

    def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "endpoint": self.endpoint, "initialize": self.initialize()}
