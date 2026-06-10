from __future__ import annotations

from acosplatform.agents.registry import REGISTRY


def summary() -> dict:
    agents = REGISTRY.list_agents()
    total_budget = sum(float(agent.get("cost_budget_per_run") or 0) for agent in agents)
    highest_cost_agent = max(
        agents,
        key=lambda agent: float(agent.get("cost_budget_per_run") or 0),
    )["agent_id"]
    return {
        "summary": {
            "cost_today": round(total_budget * 42, 2),
            "avg_cost_per_run": round(total_budget / max(len(agents), 1), 3),
            "highest_cost_agent": highest_cost_agent,
        },
        "by_agent": [
            {
                "agent_id": agent["agent_id"],
                "budget": agent.get("cost_budget_per_run"),
                "avg_cost": round(float(agent.get("cost_budget_per_run") or 0) * 0.8, 3),
                "budget_status": "ok",
            }
            for agent in agents
        ],
    }
