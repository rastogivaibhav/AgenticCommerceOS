import os
import sys

# Ensure acosplatform is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from acosplatform.db.connection import ensure_schema
from acosplatform.db.repository import save_agent, save_skill

MOCK_AGENTS = [
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
            {"id": "run_12930", "time": "14m ago", "outcome": "Success"},
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
            {"id": "run_840", "time": "5m ago", "outcome": "Failed"},
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

MOCK_SKILLS = [
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

def seed_db():
    print("Ensuring DB schema...")
    ensure_schema()
    
    print("Seeding Agents...")
    for agent in MOCK_AGENTS:
        save_agent(agent)
        print(f"  Saved ^ {agent['id']}")

    print("Seeding Skills...")
    for skill in MOCK_SKILLS:
        save_skill(skill)
        print(f"  Saved ^ {skill['id']}")
    
    print("Seed complete.")

if __name__ == "__main__":
    seed_db()
