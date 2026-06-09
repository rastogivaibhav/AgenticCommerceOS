from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from acosplatform.v2_store import get_v2_repository

repo = get_v2_repository()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_access(
    tenant_id: str,
    actor: str,
    scope: str,
    subject_id: str,
    purpose: str,
    verdict: str = "allow",
) -> dict:
    event = {
        "id": f"ma_{uuid4().hex[:10]}",
        "tenant_id": tenant_id,
        "actor_id": actor,
        "scope": scope,
        "subject_id": subject_id,
        "purpose": purpose,
        "verdict": verdict,
        "created_at": _now(),
    }
    with repo._conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO v2_memory_access_events
            (id, tenant_id, actor_id, scope, subject_id, purpose, verdict, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                tenant_id,
                actor,
                scope,
                subject_id,
                purpose,
                verdict,
                event["created_at"],
            ),
        )
    return event


def seed_memory(tenant_id: str = "default") -> None:
    if not repo.list_json("v2_memory_records", tenant_id):
        repo.upsert_json(
            "v2_memory_records",
            "session_demo",
            {
                "id": "session_demo",
                "scope": "session_memory",
                "subject_id": "demo-session",
                "summary": "Customer is considering nursery mattress and previous order return.",
                "data_classification": "customer",
            },
            tenant_id,
        )
        repo.upsert_json(
            "v2_memory_records",
            "journey_demo",
            {
                "id": "journey_demo",
                "scope": "journey_memory",
                "subject_id": "demo-journey",
                "stage": "research_and_returns",
                "constraints": {"budget": 250, "category": "nursery"},
            },
            tenant_id,
        )


def get_session_memory(
    session_id: str,
    tenant_id: str = "default",
    actor: str = "orchestrator",
) -> list[dict]:
    seed_memory(tenant_id)
    _record_access(tenant_id, actor, "session_memory", session_id, "read session context")
    return [
        record
        for record in repo.list_json("v2_memory_records", tenant_id)
        if record.get("scope") == "session_memory"
        and record.get("subject_id") in {session_id, "demo-session"}
    ]


def get_journey_memory(
    journey_id: str,
    tenant_id: str = "default",
    actor: str = "orchestrator",
) -> list[dict]:
    seed_memory(tenant_id)
    _record_access(tenant_id, actor, "journey_memory", journey_id, "read journey context")
    return [
        record
        for record in repo.list_json("v2_memory_records", tenant_id)
        if record.get("scope") == "journey_memory"
        and record.get("subject_id") in {journey_id, "demo-journey"}
    ]


def list_access_events(tenant_id: str = "default") -> list[dict]:
    seed_memory(tenant_id)
    with repo._conn() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM v2_memory_access_events
                WHERE tenant_id in (?, 'default')
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            ).fetchall()
        ]
    return rows or [
        _record_access(
            tenant_id,
            "orchestrator",
            "journey_memory",
            "demo-journey",
            "resolve nursery mattress journey",
        )
    ]
