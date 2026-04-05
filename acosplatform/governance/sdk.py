"""Governance SDK interfaces and baseline policy engine.

Week-4 foundation:
- authorize
- can_call_tool
- can_access_context
- decision logging
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from acosplatform.db.connection import is_pool_available, transaction

_fallback_decisions: list[dict[str, Any]] = []

READ_ACTION_PREFIXES = ("read.", "list.", "get.", "view.")
ANALYST_READ_TOOL_PREFIXES = ("get", "list", "read", "search", "lookup", "describe")
SENSITIVE_CONTEXT_MARKERS = ("token", "secret", "password", "payment", "card", "pii")


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _extract_roles(subject: dict[str, Any] | None) -> set[str]:
    if not isinstance(subject, dict):
        return set()

    roles: set[str] = set()
    role = subject.get("role")
    if isinstance(role, str) and role.strip():
        roles.add(role.strip().lower())

    claim_roles = subject.get("roles")
    if isinstance(claim_roles, str):
        roles.update({r.strip().lower() for r in claim_roles.split(",") if r.strip()})
    elif isinstance(claim_roles, (list, tuple, set)):
        roles.update({str(r).strip().lower() for r in claim_roles if str(r).strip()})

    realm_access = subject.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles", [])
        if isinstance(realm_roles, (list, tuple, set)):
            roles.update({str(r).strip().lower() for r in realm_roles if str(r).strip()})

    return roles


def _subject_id(subject: dict[str, Any] | None) -> str:
    if not isinstance(subject, dict):
        return "anonymous"
    return (
        str(subject.get("sub") or "").strip()
        or str(subject.get("email") or "").strip()
        or "anonymous"
    )


@dataclass(frozen=True)
class GovernanceDecision:
    allowed: bool
    reason: str
    policy_source: str = "builtin-rbac-v1"
    obligations: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class GovernanceSDK:
    """Interface for governance decisions at runtime."""

    def authorize(
        self,
        *,
        action: str,
        subject: dict[str, Any] | None,
        resource: str,
        tenant_id: str,
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        raise NotImplementedError

    def can_call_tool(
        self,
        *,
        tool_name: str,
        subject: dict[str, Any] | None,
        tenant_id: str,
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        raise NotImplementedError

    def can_access_context(
        self,
        *,
        context_key: str,
        subject: dict[str, Any] | None,
        tenant_id: str,
        access: str = "read",
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        raise NotImplementedError


class DefaultGovernanceSDK(GovernanceSDK):
    """Small, deterministic governance engine for baseline enforcement."""

    def __init__(
        self,
        *,
        persist_decisions: bool = True,
        use_opa: bool | None = None,
        opa_url: str | None = None,
        opa_package: str | None = None,
        opa_timeout_seconds: float | None = None,
    ):
        self.persist_decisions = persist_decisions
        self.use_opa = (
            _env_flag_enabled("GOVERNANCE_USE_OPA")
            if use_opa is None
            else bool(use_opa)
        )
        self.opa_url = (
            (opa_url or "").strip()
            or os.environ.get("GOVERNANCE_OPA_URL", "").strip()
        )
        self.opa_package = (
            (opa_package or "").strip().strip("/")
            or os.environ.get("GOVERNANCE_OPA_PACKAGE", "acos/governance").strip().strip("/")
        )
        timeout_env = os.environ.get("GOVERNANCE_OPA_TIMEOUT_SECONDS", "").strip()
        self.opa_timeout_seconds = (
            float(timeout_env) if timeout_env else 1.0
        ) if opa_timeout_seconds is None else float(opa_timeout_seconds)

    def _persist(
        self,
        *,
        decision: GovernanceDecision,
        action: str,
        resource: str,
        subject: dict[str, Any] | None,
        tenant_id: str,
        context: dict[str, Any] | None,
    ) -> None:
        if not self.persist_decisions:
            return
        log_governance_decision(
            tenant_id=tenant_id,
            subject=_subject_id(subject),
            action=action,
            resource=resource,
            decision="allow" if decision.allowed else "deny",
            reason=decision.reason,
            policy_source=decision.policy_source,
            obligations=list(decision.obligations),
            context=context or {},
        )

    def _opa_decision(
        self,
        *,
        decision_name: str,
        input_doc: dict[str, Any],
        fallback: GovernanceDecision,
    ) -> GovernanceDecision:
        if not (self.use_opa and self.opa_url and self.opa_package):
            return fallback

        endpoint = f"{self.opa_url.rstrip('/')}/v1/data/{self.opa_package}/{decision_name}"
        try:
            import httpx

            response = httpx.post(
                endpoint,
                json={"input": input_doc},
                timeout=self.opa_timeout_seconds,
            )
            if response.status_code >= 400:
                return fallback
            payload = response.json()
        except Exception:
            return fallback

        result = payload.get("result")
        if isinstance(result, bool):
            return GovernanceDecision(
                allowed=result,
                reason="opa_allow" if result else "opa_deny",
                policy_source=f"opa:{self.opa_package}",
            )

        if not isinstance(result, dict):
            return fallback

        allow_value = result.get("allow")
        if allow_value is None:
            allow_value = result.get("allowed")
        if allow_value is None:
            return fallback

        obligations = result.get("obligations") or ()
        if isinstance(obligations, str):
            obligations = [obligations]

        metadata = result.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        return GovernanceDecision(
            allowed=bool(allow_value),
            reason=str(result.get("reason") or fallback.reason),
            policy_source=str(result.get("policy_source") or f"opa:{self.opa_package}"),
            obligations=tuple(str(item) for item in obligations),
            metadata=metadata,
        )

    def authorize(
        self,
        *,
        action: str,
        subject: dict[str, Any] | None,
        resource: str,
        tenant_id: str,
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        roles = _extract_roles(subject)
        normalized_action = (action or "").strip().lower()

        if "admin" in roles:
            decision = GovernanceDecision(allowed=True, reason="admin_override")
        elif not roles:
            decision = GovernanceDecision(allowed=False, reason="missing_role_claims")
        elif "ops" in roles:
            if normalized_action in {"tenant.create", "tenant.update", "governance.policy.write"}:
                decision = GovernanceDecision(allowed=False, reason="ops_cannot_perform_admin_action")
            else:
                decision = GovernanceDecision(allowed=True, reason="ops_allowed")
        elif "analyst" in roles:
            if normalized_action.startswith(READ_ACTION_PREFIXES):
                decision = GovernanceDecision(allowed=True, reason="analyst_read_allowed")
            else:
                decision = GovernanceDecision(
                    allowed=False,
                    reason="analyst_read_only",
                    obligations=("open_change_request",),
                )
        else:
            decision = GovernanceDecision(allowed=False, reason="role_not_recognized")

        decision = self._opa_decision(
            decision_name="authorize",
            input_doc={
                "tenant_id": tenant_id,
                "subject": subject or {},
                "action": normalized_action,
                "resource": resource,
                "context": context or {},
            },
            fallback=decision,
        )

        self._persist(
            decision=decision,
            action=normalized_action,
            resource=resource,
            subject=subject,
            tenant_id=tenant_id,
            context=context,
        )
        return decision

    def can_call_tool(
        self,
        *,
        tool_name: str,
        subject: dict[str, Any] | None,
        tenant_id: str,
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        roles = _extract_roles(subject)
        normalized_tool = (tool_name or "").strip().lower()

        if "admin" in roles:
            decision = GovernanceDecision(allowed=True, reason="admin_tool_access")
        elif "ops" in roles:
            if normalized_tool.startswith("governance."):
                decision = GovernanceDecision(allowed=False, reason="ops_cannot_change_governance")
            else:
                decision = GovernanceDecision(allowed=True, reason="ops_tool_access")
        elif "analyst" in roles:
            if normalized_tool.startswith(ANALYST_READ_TOOL_PREFIXES):
                decision = GovernanceDecision(allowed=True, reason="analyst_read_tool_access")
            else:
                decision = GovernanceDecision(
                    allowed=False,
                    reason="analyst_tool_write_blocked",
                    obligations=("use_read_only_tool",),
                )
        else:
            decision = GovernanceDecision(allowed=False, reason="missing_or_unknown_role")

        decision = self._opa_decision(
            decision_name="can_call_tool",
            input_doc={
                "tenant_id": tenant_id,
                "subject": subject or {},
                "tool_name": normalized_tool,
                "context": context or {},
            },
            fallback=decision,
        )

        self._persist(
            decision=decision,
            action=f"tool.call:{normalized_tool}",
            resource=normalized_tool,
            subject=subject,
            tenant_id=tenant_id,
            context=context,
        )
        return decision

    def can_access_context(
        self,
        *,
        context_key: str,
        subject: dict[str, Any] | None,
        tenant_id: str,
        access: str = "read",
        context: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        roles = _extract_roles(subject)
        key = (context_key or "").strip().lower()
        mode = (access or "read").strip().lower()

        if "admin" in roles:
            decision = GovernanceDecision(allowed=True, reason="admin_context_access")
        elif not roles:
            decision = GovernanceDecision(allowed=False, reason="missing_role_claims")
        elif "analyst" in roles and mode != "read":
            decision = GovernanceDecision(allowed=False, reason="analyst_context_read_only")
        elif "analyst" in roles and any(marker in key for marker in SENSITIVE_CONTEXT_MARKERS):
            decision = GovernanceDecision(
                allowed=False,
                reason="analyst_sensitive_context_blocked",
                obligations=("request_privileged_view",),
            )
        else:
            decision = GovernanceDecision(allowed=True, reason="context_access_allowed")

        decision = self._opa_decision(
            decision_name="can_access_context",
            input_doc={
                "tenant_id": tenant_id,
                "subject": subject or {},
                "context_key": key,
                "access": mode,
                "context": context or {},
            },
            fallback=decision,
        )

        self._persist(
            decision=decision,
            action=f"context.{mode}",
            resource=key,
            subject=subject,
            tenant_id=tenant_id,
            context=context,
        )
        return decision


def log_governance_decision(
    *,
    tenant_id: str,
    subject: str,
    action: str,
    resource: str,
    decision: str,
    reason: str,
    policy_source: str,
    obligations: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "id": f"gdec-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or "default",
        "subject": subject or "anonymous",
        "action": action or "unknown",
        "resource": resource or "*",
        "decision": decision,
        "reason": reason or "",
        "policy_source": policy_source or "builtin-rbac-v1",
        "obligations": obligations or [],
        "context": context or {},
        "created_at": datetime.now(UTC).isoformat(),
    }

    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO governance_decisions (
                               id, tenant_id, subject, action, resource, decision, reason,
                               policy_source, obligations, context
                           )
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            record["id"],
                            record["tenant_id"],
                            record["subject"],
                            record["action"],
                            record["resource"],
                            record["decision"],
                            record["reason"],
                            record["policy_source"],
                            json.dumps(record["obligations"]),
                            json.dumps(record["context"]),
                        ),
                    )
            return record
        except Exception:
            # Keep the runtime non-blocking; fallback log is enough for local/dev.
            pass

    _fallback_decisions.append(record)
    return record


_DEFAULT_SDK = DefaultGovernanceSDK()


def get_governance_sdk() -> GovernanceSDK:
    return _DEFAULT_SDK
