import json
import logging
from datetime import UTC, datetime

from acosplatform.db.connection import is_pool_available, transaction

logger = logging.getLogger(__name__)

_fallback_runs = []
_fallback_events = []
_fallback_experiments = []
_fallback_workflows = []
_fallback_workflow_versions = []
_fallback_workflow_versions = []
_fallback_workflow_promotions = []
_fallback_audit_events = []
_fallback_orders = []
_fallback_agents = [
    {
        "id": "ag_marketing",
        "name": "Campaign Manager",
        "purpose": "Coordinates outbound campaign generation and segmentation decisions.",
        "subsystem": "Marketing",
        "status": "healthy",
        "calls": "12.4k",
        "uptime": "99.9%",
        "skills": ["sk_email_gen", "sk_search_products", "sk_audience_insight"],
        "bound_skills": ["sk_email_gen", "sk_search_products", "sk_audience_insight"],
        "connector_bindings": ["shopify-primary"],
        "used_by_workflow_ids": ["wf-engagement"],
        "grade": "A+",
        "latency": "110ms",
        "last_test_at": "2026-04-10T12:15:00Z",
        "last_test_status": "pass",
        "code": {
            "system_prompt": "Drive high-conversion outbound messaging while respecting campaign policies.",
            "tool_bindings": ["sk_email_gen", "sk_search_products"],
            "runtime": {"provider": "google_genai", "model": "gemini-2.0-flash"},
        },
        "scorecard": {
            "connector_health_status": "healthy",
            "contract_validation_status": "pass",
            "recent_run_failure_rate": 0.01,
            "last_successful_run_at": "2026-04-10T11:58:00Z",
        },
        "history": [
            {"id": "run_12931", "time": "2m ago", "outcome": "Success"},
            {"id": "run_12929", "time": "1h ago", "outcome": "Degraded"},
        ],
    },
    {
        "id": "ag_support_l1",
        "name": "Frontline Support",
        "purpose": "Handles order status, policy-guided answers, and escalation decisions for inbound service requests.",
        "subsystem": "Customer Service",
        "status": "healthy",
        "calls": "45.1k",
        "uptime": "99.9%",
        "skills": ["sk_order_lookup", "sk_process_refund", "sk_check_loyalty"],
        "bound_skills": ["sk_order_lookup", "sk_process_refund", "sk_check_loyalty"],
        "connector_bindings": ["shopify-primary", "salesforce-support", "whatsapp-support"],
        "used_by_workflow_ids": ["wf-order-support-demo", "wf-service"],
        "grade": "A",
        "latency": "240ms",
        "last_test_at": "2026-04-10T12:30:00Z",
        "last_test_status": "pass",
        "code": {
            "system_prompt": "Resolve order support requests, use commerce systems for evidence, and escalate if confidence is low.",
            "tool_bindings": ["shopify:get_order", "salesforce:get_contact", "whatsapp:send_message"],
            "runtime": {"provider": "google_genai", "model": "gemini-2.0-flash"},
        },
        "scorecard": {
            "connector_health_status": "healthy",
            "contract_validation_status": "pass",
            "recent_run_failure_rate": 0.02,
            "last_successful_run_at": "2026-04-10T12:25:00Z",
        },
        "history": [],
    },
    {
        "id": "ag_support_l2",
        "name": "Escalation Desk",
        "purpose": "Takes over high-risk or policy-sensitive cases that require human review.",
        "subsystem": "Customer Service",
        "status": "degraded",
        "calls": "2.1k",
        "uptime": "98.4%",
        "skills": ["sk_human_handoff", "sk_issue_credit"],
        "bound_skills": ["sk_human_handoff", "sk_issue_credit"],
        "connector_bindings": ["salesforce-support", "whatsapp-support"],
        "used_by_workflow_ids": ["wf-order-support-demo"],
        "grade": "C-",
        "latency": "1450ms",
        "last_test_at": "2026-04-10T11:30:00Z",
        "last_test_status": "fail",
        "code": {
            "system_prompt": "Collect the minimum service evidence required for escalation and open a downstream case.",
            "tool_bindings": ["salesforce:create_case", "whatsapp:handoff_tag"],
            "runtime": {"provider": "local_fallback", "model": "gemini-2.0-flash"},
        },
        "scorecard": {
            "connector_health_status": "degraded",
            "contract_validation_status": "pass",
            "recent_run_failure_rate": 0.18,
            "last_successful_run_at": "2026-04-09T19:12:00Z",
        },
        "history": [
            {"id": "run_841", "time": "1m ago", "outcome": "Failed"},
            {"id": "run_839", "time": "12m ago", "outcome": "Timeout"},
        ],
    },
    {
        "id": "ag_fulfillment",
        "name": "Logistics Router",
        "purpose": "Routes fulfillment and post-purchase tracking requests across order systems.",
        "subsystem": "Fulfillment",
        "status": "healthy",
        "calls": "8.3k",
        "uptime": "100%",
        "skills": [],
        "bound_skills": [],
        "connector_bindings": ["shopify-primary"],
        "used_by_workflow_ids": ["wf-post-purchase"],
        "grade": "A+",
        "latency": "45ms",
        "last_test_at": "2026-04-10T10:45:00Z",
        "last_test_status": "pass",
        "code": {
            "system_prompt": "Read shipment/order state and route fulfillment actions without customer-facing improvisation.",
            "tool_bindings": ["shopify:get_order"],
            "runtime": {"provider": "local_fallback", "model": "gemini-2.0-flash"},
        },
        "scorecard": {
            "connector_health_status": "healthy",
            "contract_validation_status": "pass",
            "recent_run_failure_rate": 0.0,
            "last_successful_run_at": "2026-04-10T10:44:00Z",
        },
        "history": [],
    },
    {
        "id": "ag_returns",
        "name": "Returns Processor",
        "purpose": "Prepares returns and refund intents before final downstream approval.",
        "subsystem": "Reverse Logistics",
        "status": "healthy",
        "calls": "1.2k",
        "uptime": "99.8%",
        "skills": [],
        "bound_skills": [],
        "connector_bindings": ["shopify-primary", "salesforce-support"],
        "used_by_workflow_ids": ["wf-service"],
        "grade": "A",
        "latency": "310ms",
        "last_test_at": "2026-04-10T09:30:00Z",
        "last_test_status": "pass",
        "code": {
            "system_prompt": "Prepare a governed return path and avoid issuing refunds without policy evidence.",
            "tool_bindings": ["shopify:create_return_intent", "salesforce:update_case"],
            "runtime": {"provider": "local_fallback", "model": "gemini-2.0-flash"},
        },
        "scorecard": {
            "connector_health_status": "healthy",
            "contract_validation_status": "pass",
            "recent_run_failure_rate": 0.03,
            "last_successful_run_at": "2026-04-10T09:28:00Z",
        },
        "history": [],
    },
]

_fallback_channel_bindings = [
    {
        "id": "whatsapp-support",
        "type": "whatsapp",
        "tenant_id": "default",
        "environment": "dev",
        "status": "sandbox",
        "mode": "sandbox",
        "identity": "WhatsApp Support",
        "default_route": "order_status",
        "allowed_routes": ["order_status", "return_refund", "loyalty_rewards", "vip_escalation"],
        "notification_targets": ["telegram-ops"],
        "metadata": {
            "phone_number_id": "",
            "verified_name": "",
        },
    },
    {
        "id": "telegram-ops",
        "type": "telegram",
        "tenant_id": "default",
        "environment": "dev",
        "status": "sandbox",
        "mode": "sandbox",
        "identity": "ACOS Ops Bot",
        "default_route": "order_status",
        "allowed_routes": ["order_status", "return_refund", "loyalty_rewards", "vip_escalation"],
        "notification_targets": [],
        "metadata": {
            "bot_username": "",
            "default_chat_id": "",
        },
    },
]

_fallback_channel_senders = [
    {
        "id": "sender-whatsapp-approved",
        "channel_binding_id": "whatsapp-support",
        "sender_external_id": "whatsapp:+447700900001",
        "display_name": "Ava Morgan",
        "customer_id": "cust_1001",
        "approval_status": "approved",
        "last_message": "Where is my order ORD-1001?",
        "last_seen_at": "2026-04-12T09:00:00Z",
        "metadata": {"channel": "whatsapp"},
    }
]

_fallback_channel_pairings = []

_fallback_demo_routes = [
    {
        "id": "order_status",
        "name": "Order Status",
        "description": "Track the latest order, explain shipment state, and notify ops.",
        "workflow_id": "wf-order-support-demo",
        "workflow_family": "service",
        "supported_channels": ["whatsapp", "telegram"],
        "sample_trigger": "Where is my order ORD-1001?",
        "systems": ["crm", "shopify", "salesforce", "whatsapp", "telegram"],
        "preferred_runtime": "lmstudio_local",
        "mode": "sandbox",
    },
    {
        "id": "return_refund",
        "name": "Return / Refund",
        "description": "Prepare a return intent, summarize policy, and escalate when needed.",
        "workflow_id": "wf-service",
        "workflow_family": "service",
        "supported_channels": ["whatsapp", "telegram"],
        "sample_trigger": "I want to return my last order.",
        "systems": ["crm", "shopify", "salesforce", "telegram"],
        "preferred_runtime": "local_fallback",
        "mode": "sandbox",
    },
    {
        "id": "loyalty_rewards",
        "name": "Loyalty Rewards",
        "description": "Retrieve loyalty tier and available benefits before replying.",
        "workflow_id": "wf-engagement",
        "workflow_family": "engagement",
        "supported_channels": ["whatsapp", "telegram"],
        "sample_trigger": "Do I have any loyalty rewards?",
        "systems": ["crm", "salesforce", "telegram"],
        "preferred_runtime": "local_fallback",
        "mode": "sandbox",
    },
    {
        "id": "vip_escalation",
        "name": "VIP Escalation",
        "description": "Escalate priority cases for high-value customers and notify ops.",
        "workflow_id": "wf-order-support-demo",
        "workflow_family": "service",
        "supported_channels": ["whatsapp", "telegram"],
        "sample_trigger": "This is my third failed delivery, escalate now.",
        "systems": ["crm", "salesforce", "whatsapp", "telegram"],
        "preferred_runtime": "lmstudio_local",
        "mode": "sandbox",
    },
]

_fallback_crm_customers = [
    {
        "id": "cust_1001",
        "tenant_id": "default",
        "name": "Ava Morgan",
        "email": "ava@example.com",
        "phone": "+447700900001",
        "loyalty_tier": "gold",
        "preferred_channel": "whatsapp",
        "salesforce_contact_id": "003-demo-contact",
        "shopify_customer_id": "1001",
        "last_order_id": "ORD-1001",
        "segment": "vip_repeat_buyer",
        "metadata": {
            "open_cases": ["case_1001"],
            "consent_flags": {"whatsapp": True, "telegram": True},
        },
    },
    {
        "id": "cust_1002",
        "tenant_id": "default",
        "name": "Leo Barnes",
        "email": "leo@example.com",
        "phone": "+447700900002",
        "loyalty_tier": "silver",
        "preferred_channel": "telegram",
        "salesforce_contact_id": "003-demo-contact-2",
        "shopify_customer_id": "1002",
        "last_order_id": "ORD-1002",
        "segment": "loyalty_growth",
        "metadata": {
            "open_cases": [],
            "consent_flags": {"whatsapp": False, "telegram": True},
        },
    },
]

_fallback_crm_cases = [
    {
        "id": "case_1001",
        "customer_id": "cust_1001",
        "tenant_id": "default",
        "subject": "Delayed shipment complaint",
        "status": "open",
        "priority": "high",
        "channel": "whatsapp",
        "summary": "Customer reported repeated delays for order ORD-1001.",
        "metadata": {"source": "support_history"},
    }
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
    "bound_skills",
    "history",
    "linterWarnings",
    "agent_metadata",
    "skill_metadata",
    "promo_rules",
    "features",
    "connector_routes",
    "connector_bindings",
    "used_by_workflow_ids",
    "code",
    "scorecard",
    "allowed_routes",
    "notification_targets",
    "metadata",
    "supported_channels",
    "systems",
}

_fallback_tenants = []


def _use_db():
    return is_pool_available()


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


_DEFAULT_AGENT_RUNTIME_PROVIDER = "local_fallback"
_DEFAULT_AGENT_MODEL = "gemini-2.0-flash"
_DEFAULT_AGENT_VERSION = "v1"
_DEFAULT_SKILL_EXECUTION_MODE = "local"


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_agent(agent_data):
    data = dict(agent_data)
    data["subsystem"] = data.get("subsystem") or "General"
    data["purpose"] = data.get("purpose") or f"{data.get('name', 'Agent')} operational responsibilities"
    data["status"] = data.get("status") or "healthy"
    data["calls"] = data.get("calls") or "0"
    data["uptime"] = data.get("uptime") or "100%"
    data["grade"] = data.get("grade") or "A+"
    data["latency"] = data.get("latency") or "0ms"
    data["history"] = list(data.get("history") or [])
    skills = list(data.get("skills") or data.get("bound_skills") or [])
    bound_skills = list(data.get("bound_skills") or skills)
    data["skills"] = skills
    data["bound_skills"] = bound_skills
    data["runtime_provider"] = data.get("runtime_provider") or _DEFAULT_AGENT_RUNTIME_PROVIDER
    data["model_name"] = data.get("model_name") or _DEFAULT_AGENT_MODEL
    data["agent_version"] = data.get("agent_version") or _DEFAULT_AGENT_VERSION
    data["connector_bindings"] = list(data.get("connector_bindings") or [])
    data["used_by_workflow_ids"] = list(data.get("used_by_workflow_ids") or [])
    data["last_test_at"] = data.get("last_test_at")
    data["last_test_status"] = data.get("last_test_status") or "unknown"
    data["code"] = data.get("code") or {
        "system_prompt": "",
        "tool_bindings": bound_skills,
        "runtime": {
            "provider": data["runtime_provider"],
            "model": data["model_name"],
        },
    }
    data["scorecard"] = data.get("scorecard") or {
        "connector_health_status": "unknown",
        "contract_validation_status": "unknown",
        "recent_run_failure_rate": None,
        "last_successful_run_at": None,
    }
    return data


def _normalize_skill(skill_data):
    data = dict(skill_data)
    data["category"] = data.get("category") or "Integration"
    data["type"] = data.get("type") or "read"
    data["calls"] = data.get("calls") or "0"
    data["code"] = data.get("code") or ""
    data["linterWarnings"] = list(data.get("linterWarnings") or [])
    data["input_schema"] = data.get("input_schema") or {}
    data["output_schema"] = data.get("output_schema") or {}
    data["execution_mode"] = data.get("execution_mode") or _DEFAULT_SKILL_EXECUTION_MODE
    data["timeout_seconds"] = _safe_int(data.get("timeout_seconds", 15), 15)
    data["retries"] = _safe_int(data.get("retries", 0), 0)
    return data


def _normalize_channel_binding(binding_data):
    data = dict(binding_data)
    data["type"] = (data.get("type") or "whatsapp").strip().lower()
    data["tenant_id"] = data.get("tenant_id") or "default"
    data["environment"] = data.get("environment") or "dev"
    data["status"] = data.get("status") or "sandbox"
    data["mode"] = data.get("mode") or "sandbox"
    data["identity"] = data.get("identity") or data.get("display_name") or data.get("id", "Channel")
    data["default_route"] = data.get("default_route") or "order_status"
    data["allowed_routes"] = list(data.get("allowed_routes") or [data["default_route"]])
    data["notification_targets"] = list(data.get("notification_targets") or [])
    data["metadata"] = dict(data.get("metadata") or {})
    return data


def _normalize_channel_sender(sender_data):
    data = dict(sender_data)
    data["display_name"] = data.get("display_name") or data.get("sender_external_id") or "Unknown sender"
    data["customer_id"] = data.get("customer_id")
    data["approval_status"] = (data.get("approval_status") or "pending").strip().lower()
    data["last_message"] = data.get("last_message") or ""
    data["metadata"] = dict(data.get("metadata") or {})
    return data


def _normalize_channel_pairing(pairing_data):
    data = dict(pairing_data)
    data["channel_binding_id"] = data.get("channel_binding_id") or ""
    data["route_id"] = data.get("route_id") or "order_status"
    data["pair_code"] = str(data.get("pair_code") or "").strip().upper()
    data["status"] = (data.get("status") or "active").strip().lower()
    data["metadata"] = dict(data.get("metadata") or {})
    return data


def _normalize_demo_route(route_data):
    data = dict(route_data)
    data["description"] = data.get("description") or ""
    data["workflow_id"] = data.get("workflow_id") or ""
    data["workflow_family"] = data.get("workflow_family") or "service"
    data["supported_channels"] = list(data.get("supported_channels") or [])
    data["systems"] = list(data.get("systems") or [])
    data["sample_trigger"] = data.get("sample_trigger") or ""
    data["preferred_runtime"] = data.get("preferred_runtime") or "local_fallback"
    data["mode"] = data.get("mode") or "sandbox"
    return data


def _normalize_crm_customer(customer_data):
    data = dict(customer_data)
    data["tenant_id"] = data.get("tenant_id") or "default"
    data["email"] = data.get("email") or ""
    data["phone"] = data.get("phone") or ""
    data["loyalty_tier"] = data.get("loyalty_tier") or "standard"
    data["preferred_channel"] = data.get("preferred_channel") or "whatsapp"
    data["salesforce_contact_id"] = data.get("salesforce_contact_id") or ""
    data["shopify_customer_id"] = data.get("shopify_customer_id") or ""
    data["last_order_id"] = data.get("last_order_id") or ""
    data["segment"] = data.get("segment") or "general"
    data["metadata"] = dict(data.get("metadata") or {})
    return data


def _normalize_phone_lookup(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    digits = "".join(char for char in raw if char.isdigit())
    return digits or raw.lstrip("+")


def _normalize_crm_case(case_data):
    data = dict(case_data)
    data["tenant_id"] = data.get("tenant_id") or "default"
    data["status"] = data.get("status") or "new"
    data["priority"] = data.get("priority") or "medium"
    data["channel"] = data.get("channel") or "whatsapp"
    data["summary"] = data.get("summary") or ""
    data["metadata"] = dict(data.get("metadata") or {})
    return data


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
    agent_metadata=None,
    skill_metadata=None,
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
        "agent_metadata": agent_metadata or {},
        "skill_metadata": skill_metadata or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO runs (
                               id, tenant_id, customer_id, journey, input, output, cost, score, variant,
                               workflow_id, workflow_version, environment_id, agent_metadata, skill_metadata
                           )
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                            json.dumps(agent_metadata or {}),
                            json.dumps(skill_metadata or {}),
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
    normalized = _normalize_agent(agent_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO agents (
                               id, name, subsystem, purpose, status, calls, uptime, skills, grade, latency, history,
                               runtime_provider, model_name, agent_version, bound_skills, connector_bindings,
                               used_by_workflow_ids, last_test_at, last_test_status, code, scorecard
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               subsystem=EXCLUDED.subsystem,
                               purpose=EXCLUDED.purpose,
                               status=EXCLUDED.status,
                               calls=EXCLUDED.calls,
                               uptime=EXCLUDED.uptime,
                               skills=EXCLUDED.skills,
                               grade=EXCLUDED.grade,
                               latency=EXCLUDED.latency,
                               history=EXCLUDED.history,
                               runtime_provider=EXCLUDED.runtime_provider,
                               model_name=EXCLUDED.model_name,
                               agent_version=EXCLUDED.agent_version,
                               bound_skills=EXCLUDED.bound_skills,
                               connector_bindings=EXCLUDED.connector_bindings,
                               used_by_workflow_ids=EXCLUDED.used_by_workflow_ids,
                               last_test_at=EXCLUDED.last_test_at,
                               last_test_status=EXCLUDED.last_test_status,
                               code=EXCLUDED.code,
                               scorecard=EXCLUDED.scorecard,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["name"],
                            normalized["subsystem"],
                            normalized.get("purpose", ""),
                            normalized.get("status", "healthy"),
                            normalized.get("calls", "0"),
                            normalized.get("uptime", "100%"),
                            json.dumps(normalized.get("skills", [])),
                            normalized.get("grade", "A+"),
                            normalized.get("latency", "0ms"),
                            json.dumps(normalized.get("history", [])),
                            normalized.get("runtime_provider", _DEFAULT_AGENT_RUNTIME_PROVIDER),
                            normalized.get("model_name", _DEFAULT_AGENT_MODEL),
                            normalized.get("agent_version", _DEFAULT_AGENT_VERSION),
                            json.dumps(normalized.get("bound_skills", [])),
                            json.dumps(normalized.get("connector_bindings", [])),
                            json.dumps(normalized.get("used_by_workflow_ids", [])),
                            normalized.get("last_test_at"),
                            normalized.get("last_test_status", "unknown"),
                            json.dumps(normalized.get("code", {})),
                            json.dumps(normalized.get("scorecard", {})),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_agent DB error: {e}")
    return _append_or_replace(_fallback_agents, normalized, "id")


def get_agents():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM agents ORDER BY name")
                    return [_normalize_agent(_serialize_record(r)) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_agents DB error: {e}")
    return sorted([_normalize_agent(a) for a in _fallback_agents], key=lambda x: x.get("name", ""))


def get_agent_by_id(agent_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM agents WHERE id=%s", (agent_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_agent(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_agent_by_id DB error: {e}")
    for agent in _fallback_agents:
        if agent.get("id") == agent_id:
            return _normalize_agent(agent)
    return None


def save_skill(skill_data):
    normalized = _normalize_skill(skill_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO skills (
                               id, name, category, type, calls, code, "linterWarnings",
                               input_schema, output_schema, execution_mode, timeout_seconds, retries
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               category=EXCLUDED.category,
                               type=EXCLUDED.type,
                               calls=EXCLUDED.calls,
                               code=EXCLUDED.code,
                               "linterWarnings"=EXCLUDED."linterWarnings",
                               input_schema=EXCLUDED.input_schema,
                               output_schema=EXCLUDED.output_schema,
                               execution_mode=EXCLUDED.execution_mode,
                               timeout_seconds=EXCLUDED.timeout_seconds,
                               retries=EXCLUDED.retries,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["name"],
                            normalized["category"],
                            normalized.get("type", "read"),
                            normalized.get("calls", "0"),
                            normalized.get("code", ""),
                            json.dumps(normalized.get("linterWarnings", [])),
                            json.dumps(normalized.get("input_schema", {})),
                            json.dumps(normalized.get("output_schema", {})),
                            normalized.get("execution_mode", _DEFAULT_SKILL_EXECUTION_MODE),
                            normalized.get("timeout_seconds", 15),
                            normalized.get("retries", 0),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_skill DB error: {e}")
    return _append_or_replace(_fallback_skills, normalized, "id")


def get_skills():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM skills ORDER BY name")
                    return [_normalize_skill(_serialize_record(r)) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_skills DB error: {e}")
    return sorted([_normalize_skill(s) for s in _fallback_skills], key=lambda x: x.get("name", ""))


def get_skill_by_id(skill_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM skills WHERE id=%s", (skill_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_skill(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_skill_by_id DB error: {e}")
    for skill in _fallback_skills:
        if skill.get("id") == skill_id:
            return _normalize_skill(skill)
    return None


def save_channel_binding(binding_data):
    normalized = _normalize_channel_binding(binding_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO channel_bindings (
                               id, type, tenant_id, environment, status, mode, identity,
                               default_route, allowed_routes, notification_targets, metadata
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET type=EXCLUDED.type,
                               tenant_id=EXCLUDED.tenant_id,
                               environment=EXCLUDED.environment,
                               status=EXCLUDED.status,
                               mode=EXCLUDED.mode,
                               identity=EXCLUDED.identity,
                               default_route=EXCLUDED.default_route,
                               allowed_routes=EXCLUDED.allowed_routes,
                               notification_targets=EXCLUDED.notification_targets,
                               metadata=EXCLUDED.metadata,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["type"],
                            normalized["tenant_id"],
                            normalized["environment"],
                            normalized["status"],
                            normalized["mode"],
                            normalized["identity"],
                            normalized["default_route"],
                            json.dumps(normalized["allowed_routes"]),
                            json.dumps(normalized["notification_targets"]),
                            json.dumps(normalized["metadata"]),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_channel_binding DB error: {e}")
    return _append_or_replace(_fallback_channel_bindings, normalized, "id")


def get_channel_bindings():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM channel_bindings ORDER BY type, id")
                    rows = [_normalize_channel_binding(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_channel_bindings DB error: {e}")
    return [_normalize_channel_binding(binding) for binding in _fallback_channel_bindings]


def get_channel_binding(binding_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM channel_bindings WHERE id=%s", (binding_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_channel_binding(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_channel_binding DB error: {e}")
    for binding in _fallback_channel_bindings:
        if binding.get("id") == binding_id:
            return _normalize_channel_binding(binding)
    return None


def save_channel_sender(sender_data):
    normalized = _normalize_channel_sender(sender_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO channel_senders (
                               id, channel_binding_id, sender_external_id, display_name, customer_id,
                               approval_status, last_message, last_seen_at, metadata
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET channel_binding_id=EXCLUDED.channel_binding_id,
                               sender_external_id=EXCLUDED.sender_external_id,
                               display_name=EXCLUDED.display_name,
                               customer_id=EXCLUDED.customer_id,
                               approval_status=EXCLUDED.approval_status,
                               last_message=EXCLUDED.last_message,
                               last_seen_at=EXCLUDED.last_seen_at,
                               metadata=EXCLUDED.metadata,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["channel_binding_id"],
                            normalized["sender_external_id"],
                            normalized["display_name"],
                            normalized.get("customer_id"),
                            normalized["approval_status"],
                            normalized["last_message"],
                            normalized.get("last_seen_at") or datetime.now(UTC),
                            json.dumps(normalized["metadata"]),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_channel_sender DB error: {e}")
    return _append_or_replace(_fallback_channel_senders, normalized, "id")


def get_channel_senders(channel_binding_id=None, approval_status=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM channel_senders WHERE 1=1"
                    params = []
                    if channel_binding_id:
                        query += " AND channel_binding_id=%s"
                        params.append(channel_binding_id)
                    if approval_status:
                        query += " AND approval_status=%s"
                        params.append(approval_status)
                    query += " ORDER BY last_seen_at DESC"
                    cur.execute(query, tuple(params))
                    rows = [_normalize_channel_sender(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_channel_senders DB error: {e}")
    records = [_normalize_channel_sender(sender) for sender in _fallback_channel_senders]
    if channel_binding_id:
        records = [sender for sender in records if sender.get("channel_binding_id") == channel_binding_id]
    if approval_status:
        records = [sender for sender in records if sender.get("approval_status") == approval_status]
    return records


def get_channel_sender_by_external_id(channel_binding_id, sender_external_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT * FROM channel_senders
                           WHERE channel_binding_id=%s AND sender_external_id=%s
                           LIMIT 1""",
                        (channel_binding_id, sender_external_id),
                    )
                    row = cur.fetchone()
                    if row:
                        return _normalize_channel_sender(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_channel_sender_by_external_id DB error: {e}")
    for sender in _fallback_channel_senders:
        if sender.get("channel_binding_id") == channel_binding_id and sender.get("sender_external_id") == sender_external_id:
            return _normalize_channel_sender(sender)
    return None


def save_channel_pairing(pairing_data):
    normalized = _normalize_channel_pairing(pairing_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO channel_pairings (
                               id, channel_binding_id, route_id, pair_code, status, metadata, expires_at, used_at
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET channel_binding_id=EXCLUDED.channel_binding_id,
                               route_id=EXCLUDED.route_id,
                               pair_code=EXCLUDED.pair_code,
                               status=EXCLUDED.status,
                               metadata=EXCLUDED.metadata,
                               expires_at=EXCLUDED.expires_at,
                               used_at=EXCLUDED.used_at""",
                        (
                            normalized["id"],
                            normalized["channel_binding_id"],
                            normalized["route_id"],
                            normalized["pair_code"],
                            normalized["status"],
                            json.dumps(normalized["metadata"]),
                            normalized.get("expires_at"),
                            normalized.get("used_at"),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_channel_pairing DB error: {e}")
    return _append_or_replace(_fallback_channel_pairings, normalized, "id")


def get_channel_pairings(channel_binding_id=None, status=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM channel_pairings WHERE 1=1"
                    params = []
                    if channel_binding_id:
                        query += " AND channel_binding_id=%s"
                        params.append(channel_binding_id)
                    if status:
                        query += " AND status=%s"
                        params.append(status)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, tuple(params))
                    rows = [_normalize_channel_pairing(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_channel_pairings DB error: {e}")
    records = [_normalize_channel_pairing(pairing) for pairing in _fallback_channel_pairings]
    if channel_binding_id:
        records = [pairing for pairing in records if pairing.get("channel_binding_id") == channel_binding_id]
    if status:
        records = [pairing for pairing in records if pairing.get("status") == status]
    return records


def get_channel_pairing(pairing_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM channel_pairings WHERE id=%s", (pairing_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_channel_pairing(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_channel_pairing DB error: {e}")
    for pairing in _fallback_channel_pairings:
        if pairing.get("id") == pairing_id:
            return _normalize_channel_pairing(pairing)
    return None


def get_channel_pairing_by_code(channel_binding_id, pair_code):
    normalized_code = str(pair_code or "").strip().upper()
    if not normalized_code:
        return None
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT * FROM channel_pairings
                           WHERE channel_binding_id=%s AND pair_code=%s
                           ORDER BY created_at DESC
                           LIMIT 1""",
                        (channel_binding_id, normalized_code),
                    )
                    row = cur.fetchone()
                    if row:
                        return _normalize_channel_pairing(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_channel_pairing_by_code DB error: {e}")
    for pairing in _fallback_channel_pairings:
        if pairing.get("channel_binding_id") == channel_binding_id and str(pairing.get("pair_code") or "").upper() == normalized_code:
            return _normalize_channel_pairing(pairing)
    return None


def get_channel_pairing_by_route(channel_binding_id, route_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT * FROM channel_pairings
                           WHERE channel_binding_id=%s AND route_id=%s AND status='active'
                           ORDER BY created_at DESC
                           LIMIT 1""",
                        (channel_binding_id, route_id),
                    )
                    row = cur.fetchone()
                    if row:
                        return _normalize_channel_pairing(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_channel_pairing_by_route DB error: {e}")
    for pairing in _fallback_channel_pairings:
        if (
            pairing.get("channel_binding_id") == channel_binding_id
            and pairing.get("route_id") == route_id
            and pairing.get("status") == "active"
        ):
            return _normalize_channel_pairing(pairing)
    return None


def save_demo_route(route_data):
    normalized = _normalize_demo_route(route_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO demo_routes (
                               id, name, description, workflow_id, workflow_family, supported_channels,
                               sample_trigger, systems, preferred_runtime, mode
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               description=EXCLUDED.description,
                               workflow_id=EXCLUDED.workflow_id,
                               workflow_family=EXCLUDED.workflow_family,
                               supported_channels=EXCLUDED.supported_channels,
                               sample_trigger=EXCLUDED.sample_trigger,
                               systems=EXCLUDED.systems,
                               preferred_runtime=EXCLUDED.preferred_runtime,
                               mode=EXCLUDED.mode,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["name"],
                            normalized["description"],
                            normalized["workflow_id"],
                            normalized["workflow_family"],
                            json.dumps(normalized["supported_channels"]),
                            normalized["sample_trigger"],
                            json.dumps(normalized["systems"]),
                            normalized["preferred_runtime"],
                            normalized["mode"],
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_demo_route DB error: {e}")
    return _append_or_replace(_fallback_demo_routes, normalized, "id")


def get_demo_routes():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM demo_routes ORDER BY id")
                    rows = [_normalize_demo_route(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_demo_routes DB error: {e}")
    return [_normalize_demo_route(route) for route in _fallback_demo_routes]


def get_demo_route(route_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM demo_routes WHERE id=%s", (route_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_demo_route(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_demo_route DB error: {e}")
    for route in _fallback_demo_routes:
        if route.get("id") == route_id:
            return _normalize_demo_route(route)
    return None


def save_crm_customer(customer_data):
    normalized = _normalize_crm_customer(customer_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO crm_customers (
                               id, tenant_id, name, email, phone, loyalty_tier, preferred_channel,
                               salesforce_contact_id, shopify_customer_id, last_order_id, segment, metadata
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET tenant_id=EXCLUDED.tenant_id,
                               name=EXCLUDED.name,
                               email=EXCLUDED.email,
                               phone=EXCLUDED.phone,
                               loyalty_tier=EXCLUDED.loyalty_tier,
                               preferred_channel=EXCLUDED.preferred_channel,
                               salesforce_contact_id=EXCLUDED.salesforce_contact_id,
                               shopify_customer_id=EXCLUDED.shopify_customer_id,
                               last_order_id=EXCLUDED.last_order_id,
                               segment=EXCLUDED.segment,
                               metadata=EXCLUDED.metadata,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["tenant_id"],
                            normalized["name"],
                            normalized["email"],
                            normalized["phone"],
                            normalized["loyalty_tier"],
                            normalized["preferred_channel"],
                            normalized["salesforce_contact_id"],
                            normalized["shopify_customer_id"],
                            normalized["last_order_id"],
                            normalized["segment"],
                            json.dumps(normalized["metadata"]),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_crm_customer DB error: {e}")
    return _append_or_replace(_fallback_crm_customers, normalized, "id")


def get_crm_customers():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM crm_customers ORDER BY name")
                    rows = [_normalize_crm_customer(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_crm_customers DB error: {e}")
    return [_normalize_crm_customer(customer) for customer in _fallback_crm_customers]


def get_crm_customer_by_id(customer_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM crm_customers WHERE id=%s", (customer_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_crm_customer(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_crm_customer_by_id DB error: {e}")
    for customer in _fallback_crm_customers:
        if customer.get("id") == customer_id:
            return _normalize_crm_customer(customer)
    return None


def find_crm_customer_by_phone(phone):
    phone_key = _normalize_phone_lookup(phone)
    if not phone_key:
        return None
    customers = get_crm_customers()
    for customer in customers:
        if _normalize_phone_lookup(customer.get("phone")) == phone_key:
            return customer
    return None


def save_crm_case(case_data):
    normalized = _normalize_crm_case(case_data)
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO crm_cases (
                               id, customer_id, tenant_id, subject, status, priority, channel, summary, metadata
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET customer_id=EXCLUDED.customer_id,
                               tenant_id=EXCLUDED.tenant_id,
                               subject=EXCLUDED.subject,
                               status=EXCLUDED.status,
                               priority=EXCLUDED.priority,
                               channel=EXCLUDED.channel,
                               summary=EXCLUDED.summary,
                               metadata=EXCLUDED.metadata,
                               updated_at=NOW()""",
                        (
                            normalized["id"],
                            normalized["customer_id"],
                            normalized["tenant_id"],
                            normalized["subject"],
                            normalized["status"],
                            normalized["priority"],
                            normalized["channel"],
                            normalized["summary"],
                            json.dumps(normalized["metadata"]),
                        ),
                    )
            return normalized
        except Exception as e:
            logger.warning(f"save_crm_case DB error: {e}")
    return _append_or_replace(_fallback_crm_cases, normalized, "id")


def get_crm_cases(customer_id=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    if customer_id:
                        cur.execute(
                            "SELECT * FROM crm_cases WHERE customer_id=%s ORDER BY created_at DESC",
                            (customer_id,),
                        )
                    else:
                        cur.execute("SELECT * FROM crm_cases ORDER BY created_at DESC")
                    rows = [_normalize_crm_case(_serialize_record(r)) for r in cur.fetchall()]
                    if rows:
                        return rows
        except Exception as e:
            logger.warning(f"get_crm_cases DB error: {e}")
    records = [_normalize_crm_case(case) for case in _fallback_crm_cases]
    if customer_id:
        records = [case for case in records if case.get("customer_id") == customer_id]
    return records


_fallback_products = []


def save_product(product_data):
    record = {
        "id": product_data["id"],
        "name": product_data["name"],
        "category": product_data["category"],
        "base_price": product_data["base_price"],
        "description": product_data.get("description", ""),
        "tags": product_data.get("tags", []),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO products (id, name, category, base_price, description, tags)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               category=EXCLUDED.category,
                               base_price=EXCLUDED.base_price,
                               description=EXCLUDED.description,
                               tags=EXCLUDED.tags,
                               updated_at=NOW()""",
                        (
                            record["id"],
                            record["name"],
                            record["category"],
                            record["base_price"],
                            record["description"],
                            json.dumps(record["tags"]),
                        ),
                    )
            return record
        except Exception as e:
            logger.warning(f"save_product DB error: {e}")
    return _append_or_replace(_fallback_products, record, "id")


def get_products(category=None, limit=100):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    if category:
                        cur.execute(
                            "SELECT * FROM products WHERE category=%s ORDER BY id LIMIT %s",
                            (category, limit),
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM products ORDER BY id LIMIT %s",
                            (limit,),
                        )
                    rows = cur.fetchall()
                    return [_serialize_record(r) for r in rows]
        except Exception as e:
            logger.warning(f"get_products DB error: {e}")
    if category:
        return [p for p in _fallback_products if p.get("category") == category]
    return list(_fallback_products)


def get_product_by_id(product_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_product_by_id DB error: {e}")
    for p in _fallback_products:
        if p.get("id") == product_id:
            return p
    return None


def search_products(query, category=None):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    like = f"%{query}%"
                    if category:
                        cur.execute(
                            """SELECT * FROM products
                               WHERE (name ILIKE %s OR description ILIKE %s)
                               AND category=%s
                               ORDER BY id""",
                            (like, like, category),
                        )
                    else:
                        cur.execute(
                            """SELECT * FROM products
                               WHERE name ILIKE %s OR description ILIKE %s
                               ORDER BY id""",
                            (like, like),
                        )
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"search_products DB error: {e}")
    q = query.lower()
    results = [
        p for p in _fallback_products
        if q in p.get("name", "").lower() or q in p.get("description", "").lower()
    ]
    if category:
        results = [p for p in results if p.get("category") == category]
    return results


def _normalize_order(row):
    """Ensure order dicts always have 'order_id' key (DB uses 'id' as PK)."""
    r = dict(row)
    if "order_id" not in r:
        r["order_id"] = r.get("id")
    return r


def save_order(order_data):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO orders (
                               id, customer_id, tenant_id, items, total, status,
                               placed_at, shipped_at, delivered_at
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET status=EXCLUDED.status,
                               items=EXCLUDED.items,
                               total=EXCLUDED.total,
                               shipped_at=EXCLUDED.shipped_at,
                               delivered_at=EXCLUDED.delivered_at""",
                        (
                            order_data["order_id"],
                            order_data["customer_id"],
                            order_data.get("tenant_id", "default"),
                            json.dumps(order_data.get("items", [])),
                            order_data.get("total", 0.0),
                            order_data.get("status", "placed"),
                            order_data.get("placed_at"),
                            order_data.get("shipped_at"),
                            order_data.get("delivered_at"),
                        ),
                    )
            return order_data
        except Exception as e:
            logger.warning(f"save_order DB error: {e}")
    return _append_or_replace(_fallback_orders, order_data, "order_id")


def get_orders_for_customer(customer_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM orders WHERE customer_id=%s ORDER BY placed_at DESC",
                        (customer_id,),
                    )
                    return [_normalize_order(_serialize_record(r)) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_orders_for_customer DB error: {e}")
    return [o for o in _fallback_orders if o.get("customer_id") == customer_id]


def get_order_by_id(order_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
                    row = cur.fetchone()
                    if row:
                        return _normalize_order(_serialize_record(row))
        except Exception as e:
            logger.warning(f"get_order_by_id DB error: {e}")
    for order in _fallback_orders:
        if order.get("order_id") == order_id:
            return order
    return None


def save_tenant(tenant_data):
    record = {
        "id": tenant_data["id"],
        "name": tenant_data["name"],
        "currency": tenant_data.get("currency", "USD"),
        "tax_rate": tenant_data.get("tax_rate", 0.08),
        "promo_rules": tenant_data.get("promo_rules", {}),
        "features": tenant_data.get("features", {}),
        "connectors": tenant_data.get("connectors", tenant_data.get("connector_routes", {})),
    }
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO tenants (id, name, currency, tax_rate, promo_rules, features, connector_routes)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE
                           SET name=EXCLUDED.name,
                               currency=EXCLUDED.currency,
                               tax_rate=EXCLUDED.tax_rate,
                               promo_rules=EXCLUDED.promo_rules,
                               features=EXCLUDED.features,
                               connector_routes=EXCLUDED.connector_routes,
                               updated_at=NOW()""",
                        (
                            record["id"],
                            record["name"],
                            record["currency"],
                            record["tax_rate"],
                            json.dumps(record["promo_rules"]),
                            json.dumps(record["features"]),
                            json.dumps(record["connectors"]),
                        ),
                    )
            return record
        except Exception as e:
            logger.warning(f"save_tenant DB error: {e}")
    return _append_or_replace(_fallback_tenants, record, "id")


def get_tenant(tenant_id):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM tenants WHERE id=%s", (tenant_id,))
                    row = cur.fetchone()
                    if row:
                        return _serialize_record(row)
        except Exception as e:
            logger.warning(f"get_tenant DB error: {e}")
    for t in _fallback_tenants:
        if t.get("id") == tenant_id:
            return t
    return None


def get_all_tenants():
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM tenants ORDER BY id")
                    return [_serialize_record(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"get_all_tenants DB error: {e}")
    return list(_fallback_tenants)


_fallback_loyalty = {}


def save_loyalty_points(customer_id: str, points: int):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO loyalty_points (customer_id, points) VALUES (%s, %s) "
                        "ON CONFLICT (customer_id) DO UPDATE SET points=EXCLUDED.points, updated_at=NOW()",
                        (customer_id, points),
                    )
            return
        except Exception as e:
            logger.warning(f"save_loyalty_points DB error: {e}")
    _fallback_loyalty[customer_id] = points


def get_loyalty_points(customer_id: str):
    if _use_db():
        try:
            with transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT points FROM loyalty_points WHERE customer_id=%s",
                        (customer_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        return row["points"]
                    return None
        except Exception as e:
            logger.warning(f"get_loyalty_points DB error: {e}")
    return _fallback_loyalty.get(customer_id)
