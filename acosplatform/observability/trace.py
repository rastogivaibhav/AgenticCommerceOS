"""Lightweight trace envelope and event capture for journey runs."""

from __future__ import annotations

import uuid
from collections import deque
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_trace_context: ContextVar[dict[str, Any] | None] = ContextVar("acos_trace_context", default=None)
_trace_events: deque[dict[str, Any]] = deque(maxlen=5000)


def begin_trace_envelope(
    *,
    run_id: str,
    tenant_id: str,
    journey: str,
    workflow_id: str | None,
    workflow_version: str | None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create a trace envelope and set it as active context."""
    envelope = {
        "trace_id": trace_id or f"trace-{uuid.uuid4().hex[:8]}",
        "run_id": run_id,
        "tenant_id": tenant_id,
        "journey": journey,
        "workflow_id": workflow_id,
        "workflow_version": workflow_version,
        "started_at": _now(),
    }
    _trace_context.set(envelope)
    log_trace_event("trace_started")
    return envelope


def update_trace_envelope(**fields: Any) -> dict[str, Any]:
    envelope = dict(get_trace_envelope())
    envelope.update(fields)
    _trace_context.set(envelope)
    return envelope


def get_trace_envelope() -> dict[str, Any]:
    return dict(_trace_context.get() or {})


def log_trace_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    envelope = get_trace_envelope()
    event = {
        "timestamp": _now(),
        "event_type": event_type,
        "payload": payload or {},
        **envelope,
    }
    _trace_events.append(event)
    return event


def end_trace_envelope(status: str = "success", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event = log_trace_event("trace_finished", {"status": status, **(payload or {})})
    clear_trace_envelope()
    return event


def clear_trace_envelope() -> None:
    _trace_context.set(None)


def get_recent_trace_events(
    limit: int = 100,
    tenant_id: str | None = None,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    events = list(_trace_events)
    if tenant_id:
        events = [event for event in events if event.get("tenant_id") == tenant_id]
    if run_id:
        events = [event for event in events if event.get("run_id") == run_id]
    return list(reversed(events[-limit:]))


def _now() -> str:
    return datetime.now(UTC).isoformat()
