from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Iterator
from uuid import uuid4

_LOCK = RLock()


def _db_path() -> Path:
    return Path(os.environ.get("ACOS_OUTBOX_SQLITE_PATH", os.environ.get("ACOS_NORTHSTAR_SQLITE_PATH", "var/acos_northstar.db")))


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def ensure_schema() -> None:
    with _LOCK, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS outbox_events (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                aggregate_id TEXT,
                idempotency_key TEXT UNIQUE,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_outbox_status_created
              ON outbox_events(status, created_at);
            """
        )


def publish_event(event_type: str, payload: dict[str, Any], *, tenant_id: str = "default", aggregate_id: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
    ensure_schema()
    now = datetime.now(UTC).isoformat()
    event = {
        "id": f"evt_{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "event_type": event_type,
        "aggregate_id": aggregate_id,
        "idempotency_key": idempotency_key or f"{event_type}:{aggregate_id or uuid4().hex}",
        "payload": payload,
        "status": "pending",
        "retry_count": 0,
        "last_error": None,
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO outbox_events
              (id, tenant_id, event_type, aggregate_id, idempotency_key, payload_json, status, retry_count, last_error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event["id"], tenant_id, event_type, aggregate_id, event["idempotency_key"], json.dumps(payload, sort_keys=True), event["status"], 0, None, now, now),
        )
    return event


def list_pending(limit: int = 50) -> list[dict[str, Any]]:
    ensure_schema()
    with _LOCK, _connect() as conn:
        rows = conn.execute("SELECT * FROM outbox_events WHERE status = 'pending' ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [_decode(row) for row in rows]


def mark_processed(event_id: str) -> None:
    ensure_schema()
    now = datetime.now(UTC).isoformat()
    with _LOCK, _connect() as conn:
        conn.execute("UPDATE outbox_events SET status = 'processed', updated_at = ? WHERE id = ?", (now, event_id))


def mark_failed(event_id: str, error: str, *, dead_letter_after: int = 3) -> None:
    ensure_schema()
    now = datetime.now(UTC).isoformat()
    with _LOCK, _connect() as conn:
        row = conn.execute("SELECT retry_count FROM outbox_events WHERE id = ?", (event_id,)).fetchone()
        retry_count = int(row["retry_count"] if row else 0) + 1
        status = "dead_letter" if retry_count >= dead_letter_after else "pending"
        conn.execute("UPDATE outbox_events SET status = ?, retry_count = ?, last_error = ?, updated_at = ? WHERE id = ?", (status, retry_count, error, now, event_id))


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["payload"] = json.loads(data.pop("payload_json") or "{}")
    return data
