"""In-process evidence store used by the ACOS north-star spine.

This module is intentionally dependency-light so it can run in local demos and tests
before a tenant-specific Postgres evidence table is available. Production adapters can
swap the storage functions without changing orchestration contracts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from acosplatform.northstar import repository as northstar_repository


@dataclass(slots=True)
class EvidenceEvent:
    event_type: str
    tenant_id: str
    correlation_id: str
    conversation_session_id: str | None = None
    journey_id: str | None = None
    agent_id: str | None = None
    workflow_id: str | None = None
    tool_name: str | None = None
    policy_verdict: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"ev_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


_LOCK = RLock()
_EVENTS: list[EvidenceEvent] = []


def record_evidence(event: EvidenceEvent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(event, dict):
        event = EvidenceEvent(**event)
    data = asdict(event)
    with _LOCK:
        _EVENTS.append(event)
    try:
        northstar_repository.save_evidence_event(data)
    except Exception:
        # Evidence must never break the customer path; the in-process store remains a fallback.
        pass
    return data


def list_evidence(
    *,
    correlation_id: str | None = None,
    journey_id: str | None = None,
    tenant_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    try:
        persisted = northstar_repository.list_evidence_events(
            correlation_id=correlation_id,
            journey_id=journey_id,
            tenant_id=tenant_id,
            limit=limit,
        )
        if persisted:
            return persisted
    except Exception:
        pass
    with _LOCK:
        events = list(_EVENTS)
    if correlation_id:
        events = [item for item in events if item.correlation_id == correlation_id]
    if journey_id:
        events = [item for item in events if item.journey_id == journey_id]
    if tenant_id:
        events = [item for item in events if item.tenant_id == tenant_id]
    return [asdict(item) for item in events[-limit:]]


def clear_evidence() -> None:
    with _LOCK:
        _EVENTS.clear()
    try:
        northstar_repository.reset_all()
    except Exception:
        pass
