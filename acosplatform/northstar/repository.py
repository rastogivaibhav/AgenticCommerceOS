"""Durable repository for the ACOS north-star runtime.

The first north-star cut used in-memory stores so the golden journey could be
validated quickly. This repository makes the same contracts durable without
requiring a separate service: SQLite is the default local/pilot store, while the
interface is intentionally small enough to swap to Postgres repositories later.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Iterator

from acosplatform.northstar import postgres_repository

_DB_LOCK = RLock()


def _use_postgres() -> bool:
    return os.environ.get("ACOS_NORTHSTAR_STORE", "sqlite").strip().lower() in {"postgres", "postgresql", "pg"}

def _try_postgres(function_name: str, *args: Any, **kwargs: Any) -> Any:
    if not _use_postgres():
        raise RuntimeError("postgres backend not enabled")
    fn = getattr(postgres_repository, function_name)
    return fn(*args, **kwargs)


def _db_path() -> Path:
    configured = os.environ.get("ACOS_NORTHSTAR_SQLITE_PATH")
    if configured:
        return Path(configured)
    return Path("var/acos_northstar.db")


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
    with _DB_LOCK, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                primary_channel TEXT NOT NULL,
                channel_identities_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS channel_identity_index (
                tenant_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                channel_user_id TEXT NOT NULL,
                conversation_session_id TEXT NOT NULL,
                PRIMARY KEY (tenant_id, channel, channel_user_id)
            );
            CREATE TABLE IF NOT EXISTS journeys (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                conversation_session_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_journeys_session_status
              ON journeys(conversation_session_id, status);
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                conversation_session_id TEXT,
                journey_id TEXT,
                channel TEXT NOT NULL,
                channel_user_id TEXT NOT NULL,
                customer_id TEXT,
                correlation_id TEXT NOT NULL,
                text TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
              ON messages(conversation_session_id, created_at);
            CREATE TABLE IF NOT EXISTS evidence_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                conversation_session_id TEXT,
                journey_id TEXT,
                agent_id TEXT,
                workflow_id TEXT,
                tool_name TEXT,
                policy_verdict TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_correlation
              ON evidence_events(correlation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_evidence_journey
              ON evidence_events(journey_id, created_at);
            CREATE TABLE IF NOT EXISTS replay_runs (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                conversation_session_id TEXT,
                journey_id TEXT,
                correlation_id TEXT NOT NULL,
                request_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'captured',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_replay_tenant_created
              ON replay_runs(tenant_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_replay_correlation
              ON replay_runs(correlation_id);
            """
        )


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in ("channel_identities_json", "payload_json"):
        if key in data:
            target = key.replace("_json", "")
            try:
                data[target] = json.loads(data.pop(key) or "{}")
            except json.JSONDecodeError:
                data[target] = {}
    return data


def reset_all() -> None:
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        for table in ("replay_runs", "evidence_events", "messages", "journeys", "channel_identity_index", "conversation_sessions"):
            conn.execute(f"DELETE FROM {table}")


def get_session(session_id: str) -> dict[str, Any] | None:
    if _use_postgres():
        return _try_postgres("get_session", session_id)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        row = conn.execute("SELECT * FROM conversation_sessions WHERE id = ?", (session_id,)).fetchone()
    return _decode_row(row)


def find_session_by_identity(tenant_id: str, channel: str, channel_user_id: str) -> dict[str, Any] | None:
    if _use_postgres():
        return _try_postgres("find_session_by_identity", tenant_id, channel, channel_user_id)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        idx = conn.execute(
            "SELECT conversation_session_id FROM channel_identity_index WHERE tenant_id = ? AND channel = ? AND channel_user_id = ?",
            (tenant_id, channel, channel_user_id),
        ).fetchone()
        if not idx:
            return None
        row = conn.execute("SELECT * FROM conversation_sessions WHERE id = ?", (idx["conversation_session_id"],)).fetchone()
    return _decode_row(row)


def upsert_session(session: dict[str, Any]) -> None:
    if _use_postgres():
        return _try_postgres("upsert_session", session)
    ensure_schema()
    identities = session.get("channel_identities") or {}
    with _DB_LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT INTO conversation_sessions (id, tenant_id, customer_id, primary_channel, channel_identities_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              customer_id=excluded.customer_id,
              channel_identities_json=excluded.channel_identities_json,
              updated_at=excluded.updated_at
            """,
            (
                session["id"],
                session["tenant_id"],
                session["customer_id"],
                session["primary_channel"],
                json.dumps(identities, sort_keys=True),
                session["created_at"],
                session["updated_at"],
            ),
        )
        for channel, channel_user_id in identities.items():
            conn.execute(
                """
                INSERT INTO channel_identity_index (tenant_id, channel, channel_user_id, conversation_session_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id, channel, channel_user_id) DO UPDATE SET
                  conversation_session_id=excluded.conversation_session_id
                """,
                (session["tenant_id"], channel, str(channel_user_id), session["id"]),
            )


def get_active_journey_for_session(session_id: str) -> dict[str, Any] | None:
    if _use_postgres():
        return _try_postgres("get_active_journey_for_session", session_id)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM journeys WHERE conversation_session_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    return _decode_row(row)


def get_journey(journey_id: str) -> dict[str, Any] | None:
    if _use_postgres():
        return _try_postgres("get_journey", journey_id)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        row = conn.execute("SELECT * FROM journeys WHERE id = ?", (journey_id,)).fetchone()
    return _decode_row(row)


def upsert_journey(journey: dict[str, Any]) -> None:
    if _use_postgres():
        return _try_postgres("upsert_journey", journey)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT INTO journeys (id, tenant_id, customer_id, conversation_session_id, stage, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              stage=excluded.stage,
              status=excluded.status,
              updated_at=excluded.updated_at
            """,
            (
                journey["id"], journey["tenant_id"], journey["customer_id"], journey["conversation_session_id"],
                journey.get("stage", "intake"), journey.get("status", "active"), journey["created_at"], journey["updated_at"],
            ),
        )


def save_message(message: dict[str, Any]) -> None:
    if _use_postgres():
        return _try_postgres("save_message", message)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO messages
              (id, tenant_id, conversation_session_id, journey_id, channel, channel_user_id, customer_id, correlation_id, text, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message["message_id"], message["tenant_id"], message.get("conversation_session_id"), message.get("journey_id"),
                message["channel"], message["channel_user_id"], message.get("customer_id"), message["correlation_id"],
                message["text"], json.dumps(message, sort_keys=True), message["timestamp"],
            ),
        )


def list_messages(conversation_session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if _use_postgres():
        return _try_postgres("list_messages", conversation_session_id=conversation_session_id, limit=limit)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        if conversation_session_id:
            rows = conn.execute(
                "SELECT payload_json FROM messages WHERE conversation_session_id = ? ORDER BY created_at DESC LIMIT ?",
                (conversation_session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT payload_json FROM messages ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    messages = [json.loads(row["payload_json"]) for row in rows]
    return list(reversed(messages))


def save_evidence_event(event: dict[str, Any]) -> None:
    if _use_postgres():
        return _try_postgres("save_evidence_event", event)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO evidence_events
              (id, event_type, tenant_id, correlation_id, conversation_session_id, journey_id, agent_id, workflow_id, tool_name, policy_verdict, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"], event["event_type"], event["tenant_id"], event["correlation_id"],
                event.get("conversation_session_id"), event.get("journey_id"), event.get("agent_id"), event.get("workflow_id"),
                event.get("tool_name"), event.get("policy_verdict"), json.dumps(event.get("payload") or {}, sort_keys=True), event["created_at"],
            ),
        )


def list_evidence_events(
    correlation_id: str | None = None,
    journey_id: str | None = None,
    tenant_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if _use_postgres():
        return _try_postgres(
            "list_evidence_events",
            correlation_id=correlation_id,
            journey_id=journey_id,
            tenant_id=tenant_id,
            limit=limit,
        )
    ensure_schema()
    params: list[Any] = []
    where: list[str] = []
    if correlation_id:
        where.append("correlation_id = ?")
        params.append(correlation_id)
    if journey_id:
        where.append("journey_id = ?")
        params.append(journey_id)
    if tenant_id:
        where.append("tenant_id = ?")
        params.append(tenant_id)
    sql = "SELECT * FROM evidence_events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with _DB_LOCK, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    events: list[dict[str, Any]] = []
    for row in reversed(rows):
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json") or "{}")
        events.append(data)
    return events


def list_sessions(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent conversation sessions for Studio/Ops proof screens."""
    if _use_postgres():
        return _try_postgres("list_sessions", tenant_id=tenant_id, limit=limit)
    ensure_schema()
    params: list[Any] = []
    sql = "SELECT * FROM conversation_sessions"
    if tenant_id:
        sql += " WHERE tenant_id = ?"
        params.append(tenant_id)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with _DB_LOCK, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_decode_row(row) for row in rows if row is not None]


def list_journeys(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent journeys for Studio/Ops proof screens."""
    if _use_postgres():
        return _try_postgres("list_journeys", tenant_id=tenant_id, limit=limit)
    ensure_schema()
    params: list[Any] = []
    sql = "SELECT * FROM journeys"
    if tenant_id:
        sql += " WHERE tenant_id = ?"
        params.append(tenant_id)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with _DB_LOCK, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_decode_row(row) for row in rows if row is not None]



def save_replay_run(replay: dict[str, Any]) -> None:
    """Persist a replayable north-star orchestration snapshot."""
    if _use_postgres():
        return _try_postgres("save_replay_run", replay)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO replay_runs
              (id, tenant_id, conversation_session_id, journey_id, correlation_id, request_json, result_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                replay["id"], replay["tenant_id"], replay.get("conversation_session_id"), replay.get("journey_id"),
                replay["correlation_id"], json.dumps(replay.get("request") or {}, sort_keys=True),
                json.dumps(replay.get("result") or {}, sort_keys=True), replay.get("status", "captured"), replay["created_at"],
            ),
        )


def list_replay_runs(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if _use_postgres():
        return _try_postgres("list_replay_runs", tenant_id=tenant_id, limit=limit)
    ensure_schema()
    params: list[Any] = []
    sql = "SELECT * FROM replay_runs"
    if tenant_id:
        sql += " WHERE tenant_id = ?"
        params.append(tenant_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with _DB_LOCK, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_decode_replay(row) for row in rows]


def get_replay_run(replay_id: str) -> dict[str, Any] | None:
    if _use_postgres():
        return _try_postgres("get_replay_run", replay_id)
    ensure_schema()
    with _DB_LOCK, _connect() as conn:
        row = conn.execute("SELECT * FROM replay_runs WHERE id = ?", (replay_id,)).fetchone()
    return _decode_replay(row) if row else None


def _decode_replay(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["request"] = json.loads(data.pop("request_json") or "{}")
    data["result"] = json.loads(data.pop("result_json") or "{}")
    return data
