import json
import logging
from datetime import UTC, datetime

from acosplatform.db.connection import get_connection, transaction

logger = logging.getLogger(__name__)

_fallback_runs = []
_fallback_events = []
_fallback_experiments = []
_fallback_workflows = []
_fallback_workflow_versions = []
_fallback_workflow_versions = []
_fallback_workflow_promotions = []
_fallback_audit_events = []
_fallback_agents = [
    {
        "id": "ag_marketing",
        "name": "Campaign Manager",
        "subsystem": "Marketing",
        "status": "healthy",
        "calls": "12.4k",
        "uptime": "99.9%",
        "skills": ["sk_email_gen", "sk_search_products", "sk_audience_insight"],
        "grade": "A+",
        "latency": "110ms",
        "history": [
            {"id": "run_12931", "time": "2m ago", "outcome": "Success"},
            {"id": "run_12929", "time": "1h ago", "outcome": "Degraded"},
        ],
    },
    {
        "id": "ag_support_l1",
        "name": "Frontline Support",
        "subsystem": "Customer Service",
        "status": "healthy",
        "calls": "45.1k",
        "uptime": "99.9%",
        "skills": ["sk_order_lookup", "sk_process_refund", "sk_check_loyalty"],
        "grade": "A",
        "latency": "240ms",
        "history": [],
    },
    {
        "id": "ag_support_l2",
        "name": "Escalation Desk",
        "subsystem": "Customer Service",
        "status": "degraded",
        "calls": "2.1k",
        "uptime": "98.4%",
        "skills": ["sk_human_handoff", "sk_issue_credit"],
        "grade": "C-",
        "latency": "1450ms",
        "history": [
            {"id": "run_841", "time": "1m ago", "outcome": "Failed"},
            {"id": "run_839", "time": "12m ago", "outcome": "Timeout"},
        ],
    },
    {
        "id": "ag_fulfillment",
        "name": "Logistics Router",
        "subsystem": "Fulfillment",
        "status": "healthy",
        "calls": "8.3k",
        "uptime": "100%",
        "skills": [],
        "grade": "A+",
        "latency": "45ms",
        "history": [],
    },
    {
        "id": "ag_returns",
        "name": "Returns Processor",
        "subsystem": "Reverse Logistics",
        "status": "healthy",
        "calls": "1.2k",
        "uptime": "99.8%",
        "skills": [],
        "grade": "A",
        "latency": "310ms",
        "history": [],
    },
]

_fallback_skills = [
    {
        "id": "sk_catalog_search",
        "name": "Catalog Search",
        "category": "Integration",
        "type": "read",
        "calls": "105k",
        "code": "def search_catalog(query: str, filters: dict = None):\n    \"\"\"Retrieves products matching the query.\"\"\"\n    es_client = get_elastic_client()\n    results = es_client.search(\n        index=\"products\",\n        body={\"query\": {\"match\": {\"name\": query}}}\n    )\n    return results[\"hits\"]\n",
        "linterWarnings": [],
    },
    {
        "id": "sk_process_refund",
        "name": "Process Refund",
        "category": "Finance",
        "type": "write",
        "calls": "340",
        "code": "def process_refund(order_id: str, amount: float):\n    \"\"\"Issues a refund to the customer's payment method.\"\"\"\n    import stripe\n    # WARNING: Stripe version mismatch\n    if amount > 1000:\n         require_ops_approval()\n    \n    charge = get_charge_for_order(order_id)\n    return stripe.Refund.create(charge=charge.id, amount=int(amount*100))\n",
        "linterWarnings": [
            "Line 4: \"stripe\" imported but unused at module level",
            "Line 7: Unhandled exception edge-case for large refunds",
        ],
    },
    {
        "id": "sk_check_loyalty",
        "name": "Check Loyalty Tier",
        "category": "CRM",
        "type": "read",
        "calls": "45k",
        "code": "def loyalty(): pass",
        "linterWarnings": [],
    },
    {
        "id": "sk_create_label",
        "name": "Create Return Label",
        "category": "Logistics",
        "type": "write",
        "calls": "1.2k",
        "code": "def label(): pass",
        "linterWarnings": [],
    },
]

_JSON_KEYS = {
    "input",
    "output",
    "payload",
    "variant_a",
    "variant_b",
    "input_schema",
    "output_schema",
    "step_definitions",
    "step_definitions",
    "agent_bindings",
    "policy_bindings",
    "skills",
    "history",
    "linterWarnings",
}


def _use_db():
    return get_connection() is not None


def _serialize_record(row):
    data = dict(row)
    for key in _JSON_KEYS:
        if isinstance(data.get(key), str):
            try:
                data[key] = json.loads(data[key])
            except Exception:
                pass
    for key, value in list(data.items()):
        if value and hasattr(value, "isoformat") and not isinstance(value, str):
            data[key] = value.isoformat()
    return data


def _append_or_replace(store, record, identity_key):
    for idx, existing in enumerate(store):
        if existing.get(identity_key) == record.get(identity_key):
            store[idx] = record
            return record
    store.append(record)
    return record


def save_run(
    run_id,
    tenant_id,
    customer_id,
    journey,
    input_data,
    output_data,
    cost=0.0,
    score=0.0,
    variant=None,
    workflow_id=None,
    workflow_version=None,
    environment_id="dev",
):
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
        "workflow_id": workflow_id,
        "workflow_version": workflow_version,
        "environment_id": environment_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO runs (
                               id, tenant_id, customer_id, journey, input, output, cost, score, variant,
                               workflow_id, workflow_version, environment_id
                           )
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO NOTHING""",
                        (
                            run_id,
                            tenant_id,
                            customer_id,
                            journey,
                            json.dumps(input_data),
                            json.dumps(output_data),
                            cost,
                            score,
                            variant,
                            workflow_id,
                            workflow_version,
                            environment_id,
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
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_runs DB error: {e}")
    result = list(reversed(_fallback_runs[-limit:]))
    if tenant_id:
        result = [r for r in result if r.get("tenant_id") == tenant_id]
    return result


def get_runs_by_workflow(workflow_id, limit=100):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM runs WHERE workflow_id=%s ORDER BY created_at DESC LIMIT %s",
                        (workflow_id, limit),
                    )
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_runs_by_workflow DB error: {e}")
    filtered = [r for r in _fallback_runs if r.get("workflow_id") == workflow_id]
    return list(reversed(filtered[-limit:]))


def get_run(run_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM runs WHERE id=%s", (run_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_run DB error: {e}")
    for record in _fallback_runs:
        if record["id"] == run_id:
            return record
    return None


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
                        "INSERT INTO events (run_id, event_type, payload) VALUES (%s, %s, %s)",
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
                    cur.execute("SELECT * FROM events WHERE run_id=%s ORDER BY created_at", (run_id,))
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_events DB error: {e}")
    return [event for event in _fallback_events if event["run_id"] == run_id]


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
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_experiments DB error: {e}")
    return list(_fallback_experiments)


def save_workflow(
    workflow_id,
    tenant_id,
    name,
    workflow_family,
    description="",
    business_owner="acos-team",
    status="draft",
):
    now = datetime.now(UTC).isoformat()
    record = {
        "id": workflow_id,
        "tenant_id": tenant_id,
        "name": name,
        "workflow_family": workflow_family,
        "description": description,
        "business_owner": business_owner,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO workflows (
                               id, tenant_id, name, workflow_family, description, business_owner, status
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET tenant_id=EXCLUDED.tenant_id,
                               name=EXCLUDED.name,
                               workflow_family=EXCLUDED.workflow_family,
                               description=EXCLUDED.description,
                               business_owner=EXCLUDED.business_owner,
                               status=EXCLUDED.status,
                               updated_at=NOW()""",
                        (
                            workflow_id,
                            tenant_id,
                            name,
                            workflow_family,
                            description,
                            business_owner,
                            status,
                        ),
                    )
                    cur.execute("SELECT * FROM workflows WHERE id=%s", (workflow_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
            return record
        except Exception as e:
            logger.warning(f"save_workflow DB error: {e}")
    return _append_or_replace(_fallback_workflows, record, "id")


def get_workflows(tenant_id=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    if tenant_id:
                        cur.execute(
                            "SELECT * FROM workflows WHERE tenant_id=%s ORDER BY workflow_family, name",
                            (tenant_id,),
                        )
                    else:
                        cur.execute("SELECT * FROM workflows ORDER BY workflow_family, name")
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_workflows DB error: {e}")
    result = list(_fallback_workflows)
    if tenant_id:
        result = [w for w in result if w.get("tenant_id") == tenant_id]
    return sorted(result, key=lambda item: (item.get("workflow_family", ""), item.get("name", "")))


def get_workflow(workflow_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM workflows WHERE id=%s", (workflow_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_workflow DB error: {e}")
    for workflow in _fallback_workflows:
        if workflow["id"] == workflow_id:
            return workflow
    return None


def save_workflow_version(
    workflow_id,
    version,
    change_summary,
    validation_status="draft",
    lifecycle_state=None,
    created_by="system",
    input_schema=None,
    output_schema=None,
    step_definitions=None,
    agent_bindings=None,
    policy_bindings=None,
    approved_by=None,
):
    version_id = f"{workflow_id}:{version}"
    lifecycle = lifecycle_state or validation_status
    approved_at = datetime.now(UTC).isoformat() if approved_by else None
    record = {
        "id": version_id,
        "workflow_id": workflow_id,
        "version": version,
        "lifecycle_state": lifecycle,
        "change_summary": change_summary,
        "validation_status": validation_status,
        "input_schema": input_schema or {},
        "output_schema": output_schema or {},
        "step_definitions": step_definitions or [],
        "agent_bindings": agent_bindings or [],
        "policy_bindings": policy_bindings or [],
        "created_by": created_by,
        "created_at": datetime.now(UTC).isoformat(),
        "approved_by": approved_by,
        "approved_at": approved_at,
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO workflow_versions (
                               id, workflow_id, version, lifecycle_state, change_summary, validation_status,
                               input_schema, output_schema, step_definitions, agent_bindings, policy_bindings,
                               created_by, approved_by, approved_at
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET lifecycle_state=EXCLUDED.lifecycle_state,
                               change_summary=EXCLUDED.change_summary,
                               validation_status=EXCLUDED.validation_status,
                               input_schema=EXCLUDED.input_schema,
                               output_schema=EXCLUDED.output_schema,
                               step_definitions=EXCLUDED.step_definitions,
                               agent_bindings=EXCLUDED.agent_bindings,
                               policy_bindings=EXCLUDED.policy_bindings,
                               approved_by=EXCLUDED.approved_by,
                               approved_at=EXCLUDED.approved_at""",
                        (
                            version_id,
                            workflow_id,
                            version,
                            lifecycle,
                            change_summary,
                            validation_status,
                            json.dumps(input_schema or {}),
                            json.dumps(output_schema or {}),
                            json.dumps(step_definitions or []),
                            json.dumps(agent_bindings or []),
                            json.dumps(policy_bindings or []),
                            created_by,
                            approved_by,
                            approved_at,
                        ),
                    )
                    cur.execute("SELECT * FROM workflow_versions WHERE id=%s", (version_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
            return record
        except Exception as e:
            logger.warning(f"save_workflow_version DB error: {e}")
    return _append_or_replace(_fallback_workflow_versions, record, "id")


def get_workflow_versions(workflow_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM workflow_versions WHERE workflow_id=%s ORDER BY created_at DESC",
                        (workflow_id,),
                    )
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_workflow_versions DB error: {e}")
    result = [v for v in _fallback_workflow_versions if v.get("workflow_id") == workflow_id]
    return sorted(result, key=lambda item: item.get("created_at", ""), reverse=True)


def get_workflow_version(workflow_id, version):
    version_id = f"{workflow_id}:{version}"
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM workflow_versions WHERE id=%s", (version_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_workflow_version DB error: {e}")
    for workflow_version in _fallback_workflow_versions:
        if workflow_version["id"] == version_id:
            return workflow_version
    return None


def save_workflow_promotion(
    workflow_id,
    version,
    source_environment,
    target_environment,
    requested_by,
    approved_by,
    note="",
    status="promoted",
):
    record = {
        "id": len(_fallback_workflow_promotions) + 1,
        "workflow_id": workflow_id,
        "version": version,
        "source_environment": source_environment,
        "target_environment": target_environment,
        "status": status,
        "is_active": True,
        "requested_by": requested_by,
        "approved_by": approved_by,
        "note": note,
        "promoted_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE workflow_promotions
                           SET is_active=FALSE
                           WHERE workflow_id=%s AND target_environment=%s AND is_active=TRUE""",
                        (workflow_id, target_environment),
                    )
                    cur.execute(
                        """INSERT INTO workflow_promotions (
                               workflow_id, version, source_environment, target_environment, status, is_active,
                               requested_by, approved_by, note
                           ) VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s, %s)
                           RETURNING id, promoted_at""",
                        (
                            workflow_id,
                            version,
                            source_environment,
                            target_environment,
                            status,
                            requested_by,
                            approved_by,
                            note,
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        record["id"] = row["id"]
                        record["promoted_at"] = row["promoted_at"].isoformat()
            return record
        except Exception as e:
            logger.warning(f"save_workflow_promotion DB error: {e}")
    for promotion in _fallback_workflow_promotions:
        if promotion.get("workflow_id") == workflow_id and promotion.get("target_environment") == target_environment:
            promotion["is_active"] = False
    _fallback_workflow_promotions.append(record)
    return record


def get_workflow_promotions(workflow_id=None, environment=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM workflow_promotions WHERE 1=1"
                    params = []
                    if workflow_id:
                        query += " AND workflow_id=%s"
                        params.append(workflow_id)
                    if environment:
                        query += " AND target_environment=%s"
                        params.append(environment)
                    query += " ORDER BY promoted_at DESC"
                    cur.execute(query, tuple(params))
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_workflow_promotions DB error: {e}")
    result = list(_fallback_workflow_promotions)
    if workflow_id:
        result = [p for p in result if p.get("workflow_id") == workflow_id]
    if environment:
        result = [p for p in result if p.get("target_environment") == environment]
    return sorted(result, key=lambda item: item.get("promoted_at", ""), reverse=True)


def get_active_workflow_version(workflow_family, tenant_id="default", environment="dev"):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT w.id as workflow_id, w.name, w.workflow_family, v.version, v.lifecycle_state
                           FROM workflows w
                           JOIN workflow_promotions p
                             ON p.workflow_id = w.id
                           JOIN workflow_versions v
                             ON v.workflow_id = w.id AND v.version = p.version
                           WHERE w.workflow_family=%s
                             AND w.tenant_id=%s
                             AND p.target_environment=%s
                             AND p.is_active=TRUE
                           ORDER BY p.promoted_at DESC
                           LIMIT 1""",
                        (workflow_family, tenant_id, environment),
                    )
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_active_workflow_version DB error: {e}")
    workflow_lookup = {
        workflow["id"]: workflow
        for workflow in _fallback_workflows
        if workflow.get("tenant_id") == tenant_id and workflow.get("workflow_family") == workflow_family
    }
    for promotion in sorted(_fallback_workflow_promotions, key=lambda item: item.get("promoted_at", ""), reverse=True):
        if promotion.get("target_environment") != environment or not promotion.get("is_active"):
            continue
        workflow = workflow_lookup.get(promotion.get("workflow_id"))
        if workflow:
            return {
                "workflow_id": workflow["id"],
                "name": workflow["name"],
                "workflow_family": workflow["workflow_family"],
                "version": promotion["version"],
                "lifecycle_state": "active",
            }
    return None


def save_audit_event(
    actor,
    action,
    resource_type,
    resource_id,
    tenant_id="default",
    environment_id="dev",
    payload=None,
):
    record = {
        "id": len(_fallback_audit_events) + 1,
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "tenant_id": tenant_id,
        "environment_id": environment_id,
        "payload": payload or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO audit_events (
                               actor, action, resource_type, resource_id, tenant_id, environment_id, payload
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                           RETURNING id, created_at""",
                        (
                            actor,
                            action,
                            resource_type,
                            resource_id,
                            tenant_id,
                            environment_id,
                            json.dumps(payload or {}),
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        record["id"] = row["id"]
                        record["created_at"] = row["created_at"].isoformat()
            return record
        except Exception as e:
            logger.warning(f"save_audit_event DB error: {e}")
    _fallback_audit_events.append(record)
    return record


def get_audit_events(resource_type=None, resource_id=None, limit=200):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM audit_events WHERE 1=1"
                    params = []
                    if resource_type:
                        query += " AND resource_type=%s"
                        params.append(resource_type)
                    if resource_id:
                        query += " AND resource_id=%s"
                        params.append(resource_id)
                    query += " ORDER BY created_at DESC LIMIT %s"
                    params.append(limit)
                    cur.execute(query, tuple(params))
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_audit_events DB error: {e}")
    result = list(_fallback_audit_events)
    if resource_type:
        result = [event for event in result if event.get("resource_type") == resource_type]
    if resource_id:
        result = [event for event in result if event.get("resource_id") == resource_id]
    return sorted(result, key=lambda item: item.get("created_at", ""), reverse=True)[:limit]


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
    by_tenant = {}
    for record in _fallback_runs:
        journey = record.get("journey", "unknown")
        tenant = record.get("tenant_id", "default")
        by_journey[journey] = by_journey.get(journey, 0) + 1
        by_tenant[tenant] = by_tenant.get(tenant, 0) + 1
    return {
        "total_runs": total,
        "unique_customers": customers,
        "total_cost": round(cost, 4),
        "avg_score": round(avg_score, 2),
        "runs_by_journey": by_journey,
        "runs_by_tenant": by_tenant,
    }


def save_agent(agent_data):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO agents (
                               id, name, subsystem, status, calls, uptime, skills, grade, latency, history
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               subsystem=EXCLUDED.subsystem,
                               status=EXCLUDED.status,
                               calls=EXCLUDED.calls,
                               uptime=EXCLUDED.uptime,
                               skills=EXCLUDED.skills,
                               grade=EXCLUDED.grade,
                               latency=EXCLUDED.latency,
                               history=EXCLUDED.history,
                               updated_at=NOW()""",
                        (
                            agent_data["id"],
                            agent_data["name"],
                            agent_data["subsystem"],
                            agent_data.get("status", "healthy"),
                            agent_data.get("calls", "0"),
                            agent_data.get("uptime", "100%"),
                            json.dumps(agent_data.get("skills", [])),
                            agent_data.get("grade", "A+"),
                            agent_data.get("latency", "0ms"),
                            json.dumps(agent_data.get("history", [])),
                        ),
                    )
            return agent_data
        except Exception as e:
            logger.warning(f"save_agent DB error: {e}")
    return _append_or_replace(_fallback_agents, agent_data, "id")


def get_agents():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM agents ORDER BY name")
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_agents DB error: {e}")
    return sorted(list(_fallback_agents), key=lambda x: x.get("name", ""))


def save_skill(skill_data):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO skills (
                               id, name, category, type, calls, code, "linterWarnings"
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               category=EXCLUDED.category,
                               type=EXCLUDED.type,
                               calls=EXCLUDED.calls,
                               code=EXCLUDED.code,
                               "linterWarnings"=EXCLUDED."linterWarnings",
                               updated_at=NOW()""",
                        (
                            skill_data["id"],
                            skill_data["name"],
                            skill_data["category"],
                            skill_data.get("type", "read"),
                            skill_data.get("calls", "0"),
                            skill_data.get("code", ""),
                            json.dumps(skill_data.get("linterWarnings", [])),
                        ),
                    )
            return skill_data
        except Exception as e:
            logger.warning(f"save_skill DB error: {e}")
    return _append_or_replace(_fallback_skills, skill_data, "id")


def get_skills():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM skills ORDER BY name")
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_skills DB error: {e}")
    return sorted(list(_fallback_skills), key=lambda x: x.get("name", ""))
