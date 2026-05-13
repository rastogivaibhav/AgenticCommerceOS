"""Billing engine – cost per run with token and API call tracking."""

import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

BASE_COST_PER_RUN = 0.005  # $0.005 per run
COST_PER_TOKEN = 0.00001   # $0.00001 per token
COST_PER_API_CALL = 0.001  # $0.001 per API call

# In-memory usage tracking
_usage = {}


def compute_cost(run_id, ctx, result):
    """Compute the cost of a journey run.

    Cost = base_cost + (token_count × cost_per_token) + (api_calls × cost_per_call)
    """
    tenant_id = ctx.get("tenant_id", "default")

    # Estimate token count from input/output size
    message_len = len(ctx.get("message", ""))
    result_str = str(result)
    token_count = (message_len + len(result_str)) // 4  # rough token estimate

    # Count API calls (ADK + plugins + AgentFabric)
    api_calls = 1  # base run
    agent = result.get("agent", {})
    api_calls += len(agent.get("skills_used", []))
    if agent.get("adk_active"):
        api_calls += 1  # GenAI call
    if result.get("policy", {}).get("source") == "agentfabric":
        api_calls += 1

    # Calculate costs
    base_cost = BASE_COST_PER_RUN
    token_cost = round(token_count * COST_PER_TOKEN, 6)
    api_cost = round(api_calls * COST_PER_API_CALL, 6)
    total_cost = round(base_cost + token_cost + api_cost, 6)

    cost_record = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "base_cost": base_cost,
        "token_count": token_count,
        "token_cost": token_cost,
        "api_calls": api_calls,
        "api_cost": api_cost,
        "total_cost": total_cost,
        "computed_at": datetime.now(UTC).isoformat(),
    }

    # Track usage per tenant
    if tenant_id not in _usage:
        _usage[tenant_id] = {
            "total_runs": 0,
            "total_tokens": 0,
            "total_api_calls": 0,
            "total_cost": 0.0,
        }

    _usage[tenant_id]["total_runs"] += 1
    _usage[tenant_id]["total_tokens"] += token_count
    _usage[tenant_id]["total_api_calls"] += api_calls
    _usage[tenant_id]["total_cost"] = round(_usage[tenant_id]["total_cost"] + total_cost, 6)

    return cost_record


def get_usage(tenant_id=None):
    """Get usage statistics, optionally by tenant."""
    if tenant_id:
        return _usage.get(tenant_id, {
            "total_runs": 0,
            "total_tokens": 0,
            "total_api_calls": 0,
            "total_cost": 0.0,
        })
    return dict(_usage)


def get_cost_summary():
    """Get overall cost summary across all tenants."""
    total_runs = sum(u["total_runs"] for u in _usage.values())
    total_cost = sum(u["total_cost"] for u in _usage.values())
    total_tokens = sum(u["total_tokens"] for u in _usage.values())
    total_api_calls = sum(u["total_api_calls"] for u in _usage.values())

    return {
        "total_runs": total_runs,
        "total_cost": round(total_cost, 6),
        "total_tokens": total_tokens,
        "total_api_calls": total_api_calls,
        "avg_cost_per_run": round(total_cost / total_runs, 6) if total_runs else 0,
        "tenants": len(_usage),
    }
