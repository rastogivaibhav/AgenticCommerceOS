"""Optional Postgres repository for the ACOS north-star spine.

This module mirrors acosplatform.northstar.repository but targets the
`northstar_*` tables in db/northstar_schema.sql. It is intentionally optional:
local pilots use SQLite, while production deployments can set
ACOS_NORTHSTAR_STORE=postgres and wire these functions from the service layer.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Iterator

try:  # psycopg v3 preferred
    import psycopg  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    psycopg = None  # type: ignore


class PostgresNorthstarUnavailable(RuntimeError):
    pass


def _dsn() -> str:
    dsn = os.environ.get("ACOS_NORTHSTAR_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise PostgresNorthstarUnavailable("DATABASE_URL or ACOS_NORTHSTAR_DATABASE_URL is required")
    if psycopg is None:
        raise PostgresNorthstarUnavailable("psycopg is not installed")
    return dsn


@contextmanager
def _connect() -> Iterator[Any]:
    conn = psycopg.connect(_dsn())  # type: ignore[union-attr]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_session(session: dict[str, Any]) -> None:
    identities = session.get("channel_identities") or {}
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO northstar_conversation_sessions
                  (id, tenant_id, customer_id, primary_channel, channel_identities_json, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT(id) DO UPDATE SET
                  customer_id=EXCLUDED.customer_id,
                  channel_identities_json=EXCLUDED.channel_identities_json,
                  updated_at=EXCLUDED.updated_at
                """,
                (session["id"], session["tenant_id"], session["customer_id"], session["primary_channel"], json.dumps(identities), session["created_at"], session["updated_at"]),
            )
            for channel, channel_user_id in identities.items():
                cur.execute(
                    """
                    INSERT INTO northstar_channel_identity_index
                      (tenant_id, channel, channel_user_id, conversation_session_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(tenant_id, channel, channel_user_id) DO UPDATE SET
                      conversation_session_id=EXCLUDED.conversation_session_id
                    """,
                    (session["tenant_id"], channel, str(channel_user_id), session["id"]),
                )


def upsert_journey(journey: dict[str, Any]) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO northstar_journeys
                  (id, tenant_id, customer_id, conversation_session_id, stage, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(id) DO UPDATE SET stage=EXCLUDED.stage, status=EXCLUDED.status, updated_at=EXCLUDED.updated_at
                """,
                (journey["id"], journey["tenant_id"], journey["customer_id"], journey["conversation_session_id"], journey.get("stage", "intake"), journey.get("status", "active"), journey["created_at"], journey["updated_at"]),
            )


def save_message(message: dict[str, Any]) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO northstar_messages
                  (id, tenant_id, conversation_session_id, journey_id, channel, channel_user_id, customer_id, correlation_id, text, payload_json, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT(id) DO UPDATE SET payload_json=EXCLUDED.payload_json
                """,
                (message["message_id"], message["tenant_id"], message.get("conversation_session_id"), message.get("journey_id"), message["channel"], message["channel_user_id"], message.get("customer_id"), message["correlation_id"], message["text"], json.dumps(message), message["timestamp"]),
            )


def save_evidence_event(event: dict[str, Any]) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO northstar_evidence_events
                  (id, event_type, tenant_id, correlation_id, conversation_session_id, journey_id, agent_id, workflow_id, tool_name, policy_verdict, payload_json, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT(id) DO UPDATE SET payload_json=EXCLUDED.payload_json
                """,
                (event["id"], event["event_type"], event["tenant_id"], event["correlation_id"], event.get("conversation_session_id"), event.get("journey_id"), event.get("agent_id"), event.get("workflow_id"), event.get("tool_name"), event.get("policy_verdict"), json.dumps(event.get("payload") or {}), event["created_at"]),
            )


def _row_to_dict(row: Any, columns: list[str]) -> dict[str, Any]:
    data = dict(zip(columns, row))
    for key in ("channel_identities_json", "payload_json", "request_json", "result_json"):
        if key in data:
            value = data.pop(key)
            target = key.replace("_json", "")
            if isinstance(value, str):
                data[target] = json.loads(value or "{}")
            else:
                data[target] = value or {}
    return data


def get_session(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tenant_id, customer_id, primary_channel, channel_identities_json, created_at, updated_at FROM northstar_conversation_sessions WHERE id = %s", (session_id,))
            row = cur.fetchone()
    return _row_to_dict(row, ["id", "tenant_id", "customer_id", "primary_channel", "channel_identities_json", "created_at", "updated_at"]) if row else None


def find_session_by_identity(tenant_id: str, channel: str, channel_user_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.tenant_id, s.customer_id, s.primary_channel, s.channel_identities_json, s.created_at, s.updated_at
                FROM northstar_channel_identity_index i
                JOIN northstar_conversation_sessions s ON s.id = i.conversation_session_id
                WHERE i.tenant_id = %s AND i.channel = %s AND i.channel_user_id = %s
                """,
                (tenant_id, channel, channel_user_id),
            )
            row = cur.fetchone()
    return _row_to_dict(row, ["id", "tenant_id", "customer_id", "primary_channel", "channel_identities_json", "created_at", "updated_at"]) if row else None


def get_active_journey_for_session(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, customer_id, conversation_session_id, stage, status, created_at, updated_at
                FROM northstar_journeys
                WHERE conversation_session_id = %s AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
                """,
                (session_id,),
            )
            row = cur.fetchone()
    return _row_to_dict(row, ["id", "tenant_id", "customer_id", "conversation_session_id", "stage", "status", "created_at", "updated_at"]) if row else None


def get_journey(journey_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tenant_id, customer_id, conversation_session_id, stage, status, created_at, updated_at FROM northstar_journeys WHERE id = %s", (journey_id,))
            row = cur.fetchone()
    return _row_to_dict(row, ["id", "tenant_id", "customer_id", "conversation_session_id", "stage", "status", "created_at", "updated_at"]) if row else None


def list_messages(conversation_session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            if conversation_session_id:
                cur.execute("SELECT payload_json FROM northstar_messages WHERE conversation_session_id = %s ORDER BY created_at DESC LIMIT %s", (conversation_session_id, limit))
            else:
                cur.execute("SELECT payload_json FROM northstar_messages ORDER BY created_at DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
    messages = []
    for row in rows:
        value = row[0]
        messages.append(value if isinstance(value, dict) else json.loads(value or "{}"))
    return list(reversed(messages))


def list_evidence_events(correlation_id: str | None = None, journey_id: str | None = None, tenant_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    where: list[str] = []
    params: list[Any] = []
    if correlation_id:
        where.append("correlation_id = %s")
        params.append(correlation_id)
    if journey_id:
        where.append("journey_id = %s")
        params.append(journey_id)
    if tenant_id:
        where.append("tenant_id = %s")
        params.append(tenant_id)
    sql = "SELECT id, event_type, tenant_id, correlation_id, conversation_session_id, journey_id, agent_id, workflow_id, tool_name, policy_verdict, payload_json, created_at FROM northstar_evidence_events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    cols = ["id", "event_type", "tenant_id", "correlation_id", "conversation_session_id", "journey_id", "agent_id", "workflow_id", "tool_name", "policy_verdict", "payload_json", "created_at"]
    return list(reversed([_row_to_dict(row, cols) for row in rows]))


def list_sessions(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    params: list[Any] = []
    sql = "SELECT id, tenant_id, customer_id, primary_channel, channel_identities_json, created_at, updated_at FROM northstar_conversation_sessions"
    if tenant_id:
        sql += " WHERE tenant_id = %s"
        params.append(tenant_id)
    sql += " ORDER BY updated_at DESC LIMIT %s"
    params.append(limit)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    cols = ["id", "tenant_id", "customer_id", "primary_channel", "channel_identities_json", "created_at", "updated_at"]
    return [_row_to_dict(row, cols) for row in rows]


def list_journeys(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    params: list[Any] = []
    sql = "SELECT id, tenant_id, customer_id, conversation_session_id, stage, status, created_at, updated_at FROM northstar_journeys"
    if tenant_id:
        sql += " WHERE tenant_id = %s"
        params.append(tenant_id)
    sql += " ORDER BY updated_at DESC LIMIT %s"
    params.append(limit)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    cols = ["id", "tenant_id", "customer_id", "conversation_session_id", "stage", "status", "created_at", "updated_at"]
    return [_row_to_dict(row, cols) for row in rows]


def save_replay_run(replay: dict[str, Any]) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO northstar_replay_runs
                  (id, tenant_id, conversation_session_id, journey_id, correlation_id, request_json, result_json, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                ON CONFLICT(id) DO UPDATE SET result_json=EXCLUDED.result_json, status=EXCLUDED.status
                """,
                (replay["id"], replay["tenant_id"], replay.get("conversation_session_id"), replay.get("journey_id"), replay["correlation_id"], json.dumps(replay.get("request") or {}), json.dumps(replay.get("result") or {}), replay.get("status", "captured"), replay["created_at"]),
            )


def list_replay_runs(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    params: list[Any] = []
    sql = "SELECT id, tenant_id, conversation_session_id, journey_id, correlation_id, request_json, result_json, status, created_at FROM northstar_replay_runs"
    if tenant_id:
        sql += " WHERE tenant_id = %s"
        params.append(tenant_id)
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    cols = ["id", "tenant_id", "conversation_session_id", "journey_id", "correlation_id", "request_json", "result_json", "status", "created_at"]
    return [_row_to_dict(row, cols) for row in rows]


def get_replay_run(replay_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tenant_id, conversation_session_id, journey_id, correlation_id, request_json, result_json, status, created_at FROM northstar_replay_runs WHERE id = %s", (replay_id,))
            row = cur.fetchone()
    cols = ["id", "tenant_id", "conversation_session_id", "journey_id", "correlation_id", "request_json", "result_json", "status", "created_at"]
    return _row_to_dict(row, cols) if row else None
