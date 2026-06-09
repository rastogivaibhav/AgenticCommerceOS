from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from acosplatform.agents.registry import REGISTRY
from acosplatform.v2_store import get_v2_repository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_evaluations() -> list[dict]:
    return [
        {
            "agent_id": agent["agent_id"],
            "agent_name": agent["name"],
            "score": agent.get("evaluation_score", 0),
            "threshold": 0.85 if agent.get("risk_level") != "high" else 0.90,
            "status": (
                "pass"
                if agent.get("evaluation_score", 0)
                >= (0.90 if agent.get("risk_level") == "high" else 0.85)
                else "needs_work"
            ),
            "dimensions": {
                "brand_tone": 0.9,
                "tool_use": 0.88,
                "policy_compliance": 0.92,
            },
        }
        for agent in REGISTRY.list_agents()
    ]


def split_recommendations() -> list[dict]:
    return [
        {
            "source_agent": "shopping_agent",
            "recommended_specialist": "beauty_advisor",
            "reason": "category performance lag in beauty/cosmetics test set",
            "confidence": 0.72,
        }
    ]


def run_evaluation(agent_id: str = "shopping_agent", tenant_id: str = "default") -> dict:
    agent = REGISTRY.get_agent(agent_id) or {}
    score = float(agent.get("evaluation_score") or 0.80)
    threshold = 0.90 if agent.get("risk_level") == "high" else 0.85
    run = {
        "run_id": f"eval_{uuid4().hex[:10]}",
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "score": score,
        "threshold": threshold,
        "status": "pass" if score >= threshold else "fail",
        "created_at": _now(),
        "cases_run": 12,
        "failures": [] if score >= threshold else ["score_below_threshold"],
    }
    return get_v2_repository().insert_eval_run(run)


def list_evaluation_runs(tenant_id: str = "default") -> list[dict]:
    rows = get_v2_repository().list_eval_runs(tenant_id)
    return rows or [run_evaluation("mattress_recommender", tenant_id)]


def get_evaluation_run(run_id: str, tenant_id: str = "default") -> dict | None:
    return get_v2_repository().get_eval_run(run_id, tenant_id)
