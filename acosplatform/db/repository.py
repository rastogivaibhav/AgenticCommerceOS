import json
import logging
from datetime import datetime, UTC

from acosplatform.db.connection import get_connection, transaction

logger = logging.getLogger(__name__)

_fallback_runs = []
_fallback_events = []
_fallback_experiments = []


def _use_db():
    return get_connection() is not None


# ── Runs ──────────────────────────────────────────────────────────────────────

def save_run(run_id, tenant_id, customer_id, journey, input_data, output_data, cost=0.0, score=0.0, variant=None):
    record = {
        "id": run_id,
        "tenant_id": tenant_id,
        "customer_id": customer_id,
        "journey": journey,
        "input": input_data,
        "output": output_data,
        "cost": cost,
        "score": score,
        "variant": variant,
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                    """INSERT INTO runs (id, tenant_id, customer_id, journey, input, output, cost, score, variant)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING""",
                    (
                        run_id, tenant_id, customer_id, journey,
                        json.dumps(input_data), json.dumps(output_data),
                        cost, score, variant,
                    ),
                )
            return record
        except Exception as e:
            logger.warning(f"save_run DB error: {e}")
    _fallback_runs.append(record)
    return record


def get_runs(tenant_id=None, limit=100):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    if tenant_id:
                        cur.execute(
                            "SELECT * FROM runs WHERE tenant_id=%s ORDER BY created_at DESC LIMIT %s",
                            (tenant_id, limit),
                        )
                    else:
                        cur.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT %s", (limit,))
                    rows = cur.fetchall()
                    return [_serialize_run(r) for r in rows]
        except Exception as e:
            logger.warning(f"get_runs DB error: {e}")
    return list(reversed(_fallback_runs[-limit:]))


def get_run(run_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM runs WHERE id=%s", (run_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_run(row)
        except Exception as e:
            logger.warning(f"get_run DB error: {e}")
    for r in _fallback_runs:
        if r["id"] == run_id:
            return r
    return None


def _serialize_run(row):
    d = dict(row)
    for key in ("input", "output"):
        if isinstance(d.get(key), str):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    if d.get("created_at") and not isinstance(d["created_at"], str):
        d["created_at"] = d["created_at"].isoformat()
    return d


# ── Events ────────────────────────────────────────────────────────────────────

def save_event(run_id, event_type, payload=None):
    record = {
        "run_id": run_id,
        "event_type": event_type,
        "payload": payload or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO events (run_id, event_type, payload) VALUES (%s, %s, %s)""",
                        (run_id, event_type, json.dumps(payload or {})),
                    )
            return record
        except Exception as e:
            logger.warning(f"save_event DB error: {e}")
    _fallback_events.append(record)
    return record


def get_events(run_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM events WHERE run_id=%s ORDER BY created_at", (run_id,)
                    )
                    rows = cur.fetchall()
                    result = []
                    for r in rows:
                        d = dict(r)
                        if isinstance(d.get("payload"), str):
                            try:
                                d["payload"] = json.loads(d["payload"])
                            except Exception:
                                pass
                        if d.get("created_at") and not isinstance(d["created_at"], str):
                            d["created_at"] = d["created_at"].isoformat()
                        result.append(d)
                    return result
        except Exception as e:
            logger.warning(f"get_events DB error: {e}")
    return [e for e in _fallback_events if e["run_id"] == run_id]


# ── Experiments ───────────────────────────────────────────────────────────────

def save_experiment(name, variant_a, variant_b, winner=None):
    record = {
        "name": name,
        "variant_a": variant_a,
        "variant_b": variant_b,
        "winner": winner,
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO experiments (name, variant_a, variant_b, winner)
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (name, json.dumps(variant_a), json.dumps(variant_b), winner),
                    )
                row = cur.fetchone()
                record["id"] = row["id"] if row else None
            return record
        except Exception as e:
            logger.warning(f"save_experiment DB error: {e}")
    record["id"] = len(_fallback_experiments) + 1
    _fallback_experiments.append(record)
    return record


def get_experiments():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM experiments ORDER BY created_at DESC")
                    rows = cur.fetchall()
                    result = []
                    for r in rows:
                        d = dict(r)
                        for key in ("variant_a", "variant_b"):
                            if isinstance(d.get(key), str):
                                try:
                                    d[key] = json.loads(d[key])
                                except Exception:
                                    pass
                        if d.get("created_at") and not isinstance(d["created_at"], str):
                            d["created_at"] = d["created_at"].isoformat()
                        result.append(d)
                    return result
        except Exception as e:
            logger.warning(f"get_experiments DB error: {e}")
    return list(_fallback_experiments)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def get_dashboard():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as total_runs FROM runs")
                    total = cur.fetchone()["total_runs"]
                    cur.execute("SELECT COUNT(DISTINCT customer_id) as unique_customers FROM runs")
                    customers = cur.fetchone()["unique_customers"]
                    cur.execute("SELECT COALESCE(SUM(cost),0) as total_cost FROM runs")
                    cost = float(cur.fetchone()["total_cost"])
                    cur.execute("SELECT COALESCE(AVG(score),0) as avg_score FROM runs")
                    avg_score = float(cur.fetchone()["avg_score"])
                    cur.execute("SELECT journey, COUNT(*) as count FROM runs GROUP BY journey ORDER BY count DESC")
                    by_journey = {r["journey"]: r["count"] for r in cur.fetchall()}
                    cur.execute("SELECT tenant_id, COUNT(*) as count FROM runs GROUP BY tenant_id ORDER BY count DESC")
                    by_tenant = {r["tenant_id"]: r["count"] for r in cur.fetchall()}
                    return {
                        "total_runs": total,
                        "unique_customers": customers,
                        "total_cost": round(cost, 4),
                        "avg_score": round(avg_score, 2),
                        "runs_by_journey": by_journey,
                        "runs_by_tenant": by_tenant,
                    }
        except Exception as e:
            logger.warning(f"get_dashboard DB error: {e}")
    total = len(_fallback_runs)
    customers = len(set(r.get("customer_id", "anon") for r in _fallback_runs)) if _fallback_runs else 0
    cost = sum(r.get("cost", 0) for r in _fallback_runs)
    avg_score = (sum(r.get("score", 0) for r in _fallback_runs) / total) if total else 0
    by_journey = {}
    for r in _fallback_runs:
        j = r.get("journey", "unknown")
        by_journey[j] = by_journey.get(j, 0) + 1
    by_tenant = {}
    for r in _fallback_runs:
        t = r.get("tenant_id", "default")
        by_tenant[t] = by_tenant.get(t, 0) + 1
    return {
        "total_runs": total,
        "unique_customers": customers,
        "total_cost": round(cost, 4),
        "avg_score": round(avg_score, 2),
        "runs_by_journey": by_journey,
        "runs_by_tenant": by_tenant,
    }
