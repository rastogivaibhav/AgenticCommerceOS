"""North-star API key RBAC helpers.

This is intentionally lightweight for pilot/prod transition: API keys are
configured through env vars, can be tenant scoped, and expose role checks used
by REST, GraphQL, and MCP surfaces. A later enterprise cut can replace the
parser with DB-backed key hashes without changing endpoint code.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable


@dataclass(frozen=True)
class NorthstarAuthContext:
    subject: str
    tenant_id: str
    roles: tuple[str, ...]
    raw_key: str | None = None

    def has_any_role(self, required: Iterable[str]) -> bool:
        allowed = {role.lower() for role in self.roles}
        return bool(allowed.intersection({role.lower() for role in required}))


def flag_enabled(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _parse_key_entry(entry: str) -> tuple[str, str, tuple[str, ...]] | None:
    """Parse `key[:tenant[:role|role2]]`, keeping comma compatibility."""
    entry = entry.strip()
    if not entry:
        return None
    parts = entry.split(":")
    key = parts[0].strip()
    tenant = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "default"
    roles_raw = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "admin|ops|analyst|viewer"
    roles = tuple(sorted({r.strip().lower() for r in roles_raw.replace(",", "|").split("|") if r.strip()}))
    return key, tenant, roles


def configured_key_map(env_name: str = "ACOS_NORTHSTAR_API_KEYS") -> dict[str, tuple[str, tuple[str, ...]]]:
    entries = []
    raw = os.environ.get(env_name, "")
    for chunk in raw.replace(";", ",").split(","):
        parsed = _parse_key_entry(chunk)
        if parsed:
            key, tenant, roles = parsed
            entries.append((key, tenant, roles))
    return {key: (tenant, roles) for key, tenant, roles in entries}


def authenticate_api_key(
    api_key: str | None,
    *,
    require_auth_env: str = "ACOS_NORTHSTAR_REQUIRE_AUTH",
    key_env: str = "ACOS_NORTHSTAR_API_KEYS",
    default_tenant: str = "default",
) -> NorthstarAuthContext:
    if not flag_enabled(require_auth_env, "0"):
        return NorthstarAuthContext(subject="dev-open", tenant_id=default_tenant, roles=("admin", "ops", "analyst", "viewer"), raw_key=api_key)
    key_map = configured_key_map(key_env)
    if not api_key or api_key not in key_map:
        raise PermissionError("Invalid or missing API key")
    tenant, roles = key_map[api_key]
    return NorthstarAuthContext(subject=f"api-key:{api_key[:6]}", tenant_id=tenant, roles=roles, raw_key=api_key)


def require_roles(context: NorthstarAuthContext, *required: str) -> None:
    if required and not context.has_any_role(required):
        raise PermissionError(f"Required role missing. Need one of: {', '.join(required)}")


def enforce_tenant(context: NorthstarAuthContext, requested_tenant: str | None) -> str:
    tenant = requested_tenant or context.tenant_id
    if "admin" not in context.roles and tenant != context.tenant_id:
        raise PermissionError("API key is not allowed to access the requested tenant")
    return tenant
