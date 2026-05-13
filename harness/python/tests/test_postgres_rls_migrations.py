"""Postgres-backed migration/RLS tests for context + governance tables."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")
extras = pytest.importorskip("psycopg2.extras")


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "postgresql://acos:acos_dev_password@localhost:5432/acos")


def _connect_or_skip():
    try:
        conn = psycopg2.connect(
            dsn=_database_url(),
            connect_timeout=2,
            cursor_factory=extras.RealDictCursor,
        )
    except Exception as exc:
        pytest.skip(f"Postgres unavailable for RLS migration tests: {exc}")
    return conn


def _ensure_schema(conn):
    schema_sql = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    with schema_sql.open("r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def _enable_rls_test_role(conn):
    """
    Switch to a non-superuser role so RLS policies are actually enforced.
    The default bootstrap role in local Docker Postgres is superuser and bypasses RLS.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'acos_rls_test') THEN
                    CREATE ROLE acos_rls_test;
                END IF;
            END
            $$;
            """
        )
        cur.execute("GRANT USAGE ON SCHEMA public TO acos_rls_test")
        cur.execute(
            """
            GRANT SELECT, INSERT, UPDATE, DELETE
            ON context_sessions, context_events, context_memory, governance_decisions
            TO acos_rls_test
            """
        )
        cur.execute("SET ROLE acos_rls_test")
        cur.execute("SET row_security = on")


def test_context_governance_schema_and_policies_exist():
    conn = _connect_or_skip()
    try:
        _ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname='public'
                  AND tablename IN (
                    'context_sessions',
                    'context_events',
                    'context_memory',
                    'governance_decisions'
                  )
                ORDER BY tablename
                """
            )
            tables = {row["tablename"] for row in cur.fetchall()}
            assert tables == {
                "context_events",
                "context_memory",
                "context_sessions",
                "governance_decisions",
            }

            cur.execute(
                """
                SELECT tablename, policyname
                FROM pg_policies
                WHERE schemaname='public'
                  AND policyname IN (
                    'tenant_isolation_context_sessions',
                    'tenant_isolation_context_events',
                    'tenant_isolation_context_memory',
                    'tenant_isolation_governance_decisions'
                  )
                ORDER BY tablename, policyname
                """
            )
            policies = {(row["tablename"], row["policyname"]) for row in cur.fetchall()}
            assert ("context_sessions", "tenant_isolation_context_sessions") in policies
            assert ("context_events", "tenant_isolation_context_events") in policies
            assert ("context_memory", "tenant_isolation_context_memory") in policies
            assert ("governance_decisions", "tenant_isolation_governance_decisions") in policies
    finally:
        conn.close()


def test_rls_isolation_uses_tenant_session_context():
    conn = _connect_or_skip()
    marker = f"rls-{uuid.uuid4().hex[:8]}"
    try:
        _ensure_schema(conn)
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET row_security = on")
            cur.execute("SELECT set_config('app.tenant_id', '', false)")
            cur.execute(
                "DELETE FROM context_memory WHERE memory_key LIKE %s",
                (f"{marker}%",),
            )
            cur.execute(
                """
                INSERT INTO context_memory (
                    tenant_id, customer_id, memory_key, memory_value, source, freshness_score
                ) VALUES
                    ('tenant-a', 'cust-1', %s, '{"value":"a"}'::jsonb, 'test', 1.0),
                    ('tenant-b', 'cust-1', %s, '{"value":"b"}'::jsonb, 'test', 1.0)
                """,
                (f"{marker}-shared", f"{marker}-shared"),
            )
            conn.commit()

        _enable_rls_test_role(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.tenant_id', %s, false)", ("tenant-a",))
            cur.execute(
                """
                SELECT DISTINCT tenant_id
                FROM context_memory
                WHERE memory_key = %s
                ORDER BY tenant_id
                """,
                (f"{marker}-shared",),
            )
            visible = [row["tenant_id"] for row in cur.fetchall()]
            assert visible == ["tenant-a"]

            cur.execute("SAVEPOINT blocked_insert")
            with pytest.raises(psycopg2.Error):
                cur.execute(
                    """
                    INSERT INTO context_memory (
                        tenant_id, customer_id, memory_key, memory_value, source, freshness_score
                    ) VALUES (%s, %s, %s, '{"value":"blocked"}'::jsonb, 'test', 1.0)
                    """,
                    ("tenant-b", "cust-9", f"{marker}-blocked"),
                )
            cur.execute("ROLLBACK TO SAVEPOINT blocked_insert")

            cur.execute("SELECT set_config('app.tenant_id', %s, false)", ("tenant-b",))
            cur.execute(
                """
                SELECT DISTINCT tenant_id
                FROM context_memory
                WHERE memory_key = %s
                ORDER BY tenant_id
                """,
                (f"{marker}-shared",),
            )
            visible_b = [row["tenant_id"] for row in cur.fetchall()]
            assert visible_b == ["tenant-b"]
    finally:
        with conn.cursor() as cur:
            cur.execute("RESET ROLE")
            cur.execute("SELECT set_config('app.tenant_id', '', false)")
            cur.execute("DELETE FROM context_memory WHERE memory_key LIKE %s", (f"{marker}%",))
        conn.commit()
        conn.close()
