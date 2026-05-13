"""Context persistence primitives (session + durable memory).

Week-5 foundation for tenant-scoped context and RLS rollout.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from acosplatform.db.connection import is_pool_available, transaction

_fallback_sessions: dict[str, dict[str, Any]] = {}
_fallback_events: list[dict[str, Any]] = []
_fallback_memory: list[dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def start_context_session(
    *,
    tenant_id: str,
    customer_id: str = "anon",
    channel: str = "journey",
    metadata: dict[str, Any] | None = None,
    created_by: str = "system",
) -> dict[str, Any]:
    record = {
        "id": f"ctx-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or "default",
        "customer_id": customer_id or "anon",
        "channel": channel or "journey",
        "status": "active",
        "metadata": metadata or {},
        "created_by": created_by or "system",
        "created_at": _now_iso(),
        "ended_at": None,
    }

    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO context_sessions (
                               id, tenant_id, customer_id, channel, status, metadata, created_by
                           )
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (
                            record["id"],
                            record["tenant_id"],
                            record["customer_id"],
                            record["channel"],
                            record["status"],
                            json.dumps(record["metadata"]),
                            record["created_by"],
                        ),
                    )
            return record
        except Exception:
            pass

    _fallback_sessions[record["id"]] = record
    return record


def append_context_event(
    *,
    session_id: str,
    tenant_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    actor: str = "system",
) -> dict[str, Any]:
    record = {
        "id": f"cev-{uuid.uuid4().hex[:12]}",
        "session_id": session_id,
        "tenant_id": tenant_id or "default",
        "event_type": event_type,
        "payload": payload or {},
        "actor": actor or "system",
        "created_at": _now_iso(),
    }

    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO context_events (session_id, tenant_id, event_type, payload, actor)
                           VALUES (%s, %s, %s, %s, %s)
                           RETURNING id, created_at""",
                        (
                            session_id,
                            record["tenant_id"],
                            record["event_type"],
                            json.dumps(record["payload"]),
                            record["actor"],
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        record["id"] = str(row["id"])
                        record["created_at"] = row["created_at"].isoformat()
            return record
        except Exception:
            pass

    _fallback_events.append(record)
    return record


def upsert_context_memory(
    *,
    tenant_id: str,
    customer_id: str,
    memory_key: str,
    memory_value: dict[str, Any] | list[Any] | str | int | float | bool | None,
    source: str = "runtime",
    freshness_score: float = 1.0,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    expires_at = None
    if ttl_seconds and ttl_seconds > 0:
        expires_at = now + timedelta(seconds=ttl_seconds)

    record = {
        "tenant_id": tenant_id or "default",
        "customer_id": customer_id or "anon",
        "memory_key": memory_key,
        "memory_value": memory_value,
        "source": source,
        "freshness_score": float(freshness_score),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "updated_at": now.isoformat(),
    }

    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO context_memory (
                               tenant_id, customer_id, memory_key, memory_value,
                               source, freshness_score, expires_at
                           )
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (tenant_id, customer_id, memory_key)
                           DO UPDATE SET
                               memory_value = EXCLUDED.memory_value,
                               source = EXCLUDED.source,
                               freshness_score = EXCLUDED.freshness_score,
                               expires_at = EXCLUDED.expires_at,
                               updated_at = NOW()""",
                        (
                            record["tenant_id"],
                            record["customer_id"],
                            record["memory_key"],
                            json.dumps(memory_value),
                            record["source"],
                            record["freshness_score"],
                            expires_at,
                        ),
                    )
            return record
        except Exception:
            pass

    existing = next(
        (
            item
            for item in _fallback_memory
            if item["tenant_id"] == record["tenant_id"]
            and item["customer_id"] == record["customer_id"]
            and item["memory_key"] == record["memory_key"]
        ),
        None,
    )
    if existing:
        existing.update(record)
        return existing

    _fallback_memory.append(record)
    return record


def list_context_events(*, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
    cap = min(max(limit, 1), 1000)
    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT id, session_id, tenant_id, event_type, payload, actor, created_at
                           FROM context_events
                           WHERE session_id=%s
                           ORDER BY created_at DESC
                           LIMIT %s""",
                        (session_id, cap),
                    )
                    rows = cur.fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                result.append(
                    {
                        "id": str(row["id"]),
                        "session_id": row["session_id"],
                        "tenant_id": row["tenant_id"],
                        "event_type": row["event_type"],
                        "payload": row["payload"],
                        "actor": row["actor"],
                        "created_at": row["created_at"].isoformat(),
                    }
                )
            return result
        except Exception:
            pass

    return [e for e in reversed(_fallback_events) if e["session_id"] == session_id][:cap]


def get_context_memory(
    *,
    tenant_id: str,
    customer_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    cap = min(max(limit, 1), 1000)
    if is_pool_available():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT tenant_id, customer_id, memory_key, memory_value, source,
                                  freshness_score, expires_at, updated_at
                           FROM context_memory
                           WHERE tenant_id=%s AND customer_id=%s
                           ORDER BY updated_at DESC
                           LIMIT %s""",
                        (tenant_id, customer_id, cap),
                    )
                    rows = cur.fetchall()
            return [
                {
                    "tenant_id": row["tenant_id"],
                    "customer_id": row["customer_id"],
                    "memory_key": row["memory_key"],
                    "memory_value": row["memory_value"],
                    "source": row["source"],
                    "freshness_score": float(row["freshness_score"]),
                    "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
                    "updated_at": row["updated_at"].isoformat(),
                }
                for row in rows
            ]
        except Exception:
            pass

    scoped = [
        item
        for item in _fallback_memory
        if item["tenant_id"] == tenant_id and item["customer_id"] == customer_id
    ]
    return sorted(scoped, key=lambda item: item["updated_at"], reverse=True)[:cap]

