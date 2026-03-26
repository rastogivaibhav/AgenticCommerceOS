"""
Temporal activities — one per canvas node type.
Each activity receives a NodeInput (node + context + upstream results)
and returns a dict merged into the running execution context.
"""
from __future__ import annotations
import asyncio
import logging
from temporalio import activity
from pydantic import BaseModel
from acosplatform.plugins import catalog, checkout, loyalty, orders
from integrations.adk.provider import run_adk

logger = logging.getLogger(__name__)


class NodeInput(BaseModel):
    """Pydantic model — Temporal's data converter serialises this reliably."""
    node: dict      # ReactFlow node {id, type, data}
    ctx: dict       # Journey context (customer_id, tenant_id, message, ...)
    upstream: dict  # Merged results from all upstream nodes


# ── Start / End — sentinels ───────────────────────────────────────────────────

@activity.defn(name="execute_start_node")
async def execute_start_node(inp: NodeInput) -> dict:
    return {"started": True, "trigger_type": inp.node["data"].get("triggerType", "manual")}


@activity.defn(name="execute_end_node")
async def execute_end_node(inp: NodeInput) -> dict:
    return {"completed": True, "outcome": inp.node["data"].get("outcomeType", "success")}


# ── Orchestrator ──────────────────────────────────────────────────────────────

@activity.defn(name="execute_orchestrator_node")
async def execute_orchestrator_node(inp: NodeInput) -> dict:
    """Signals fan-out. GraphWorkflow uses edge conditions to route sub-agents."""
    return {
        "orchestrated": True,
        "agent_id": inp.node["data"].get("agentId", ""),
        "routing_context": {**inp.ctx, **inp.upstream},
    }


# ── Agent / Sub-Agent ─────────────────────────────────────────────────────────

@activity.defn(name="execute_agent_node")
async def execute_agent_node(inp: NodeInput) -> dict:
    agent_id      = inp.node["data"].get("agentId", "")
    system_prompt = inp.node["data"].get("systemPrompt", "")
    merged_ctx    = {**inp.ctx, **inp.upstream}
    if system_prompt:
        merged_ctx["system_prompt_override"] = system_prompt
    try:
        result = await asyncio.to_thread(run_adk, merged_ctx, agent_id or "default")
        return result if isinstance(result, dict) else {"response": str(result)}
    except Exception as exc:
        logger.warning("execute_agent_node agent=%s failed: %s", agent_id, exc)
        return {"error": str(exc), "agent_id": agent_id}


@activity.defn(name="execute_sub_agent_node")
async def execute_sub_agent_node(inp: NodeInput) -> dict:
    return await execute_agent_node(inp)


# ── Integration ───────────────────────────────────────────────────────────────

_SKILL_MAP = {
    # catalog.search() takes a query STRING, not a context dict — extract it first
    "catalog":  lambda ctx: catalog.search(ctx.get("query") or ctx.get("message", "")),
    "checkout": lambda ctx: checkout.run(ctx),
    "loyalty":  lambda ctx: loyalty.run(ctx),
    "orders":   lambda ctx: orders.run(ctx),
}


@activity.defn(name="execute_integration_node")
async def execute_integration_node(inp: NodeInput) -> dict:
    skill_id   = inp.node["data"].get("skillId", "")
    merged_ctx = {**inp.ctx, **inp.upstream}
    fn         = _SKILL_MAP.get(skill_id)
    if fn:
        try:
            return await asyncio.to_thread(fn, merged_ctx) or {}
        except Exception as exc:
            logger.warning("execute_integration_node skill=%s failed: %s", skill_id, exc)
            return {"error": str(exc), "skill_id": skill_id}
    logger.warning("Unknown skillId '%s' — skipping node", skill_id)
    return {"skill_id": skill_id, "skipped": True}


# ── Logic ─────────────────────────────────────────────────────────────────────

@activity.defn(name="execute_logic_node")
async def execute_logic_node(inp: NodeInput) -> dict:
    """
    Switch: passes merged context through so downstream edge conditions can route.
    Code type: deferred to a future sandboxed evaluator — passes through for now.
    """
    logic_type = inp.node["data"].get("logicType", "switch")
    if logic_type == "code":
        logger.warning(
            "logicNode 'code' type is not yet executed — sandboxed evaluator pending. "
            "Node %s passes context through unchanged.", inp.node.get("id")
        )
    return {**inp.ctx, **inp.upstream}


# ── Registry ──────────────────────────────────────────────────────────────────

ACTIVITY_REGISTRY = {
    "startNode":        execute_start_node,
    "endNode":          execute_end_node,
    "orchestratorNode": execute_orchestrator_node,
    "agentNode":        execute_agent_node,
    "subAgentNode":     execute_sub_agent_node,
    "integrationNode":  execute_integration_node,
    "logicNode":        execute_logic_node,
    "triggerNode":      execute_start_node,
}
