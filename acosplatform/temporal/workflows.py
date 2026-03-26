"""GraphWorkflow — durable Temporal workflow that walks a canvas graph."""
from __future__ import annotations
import logging
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from acosplatform.temporal.graph_walker import (
        find_start_node, next_nodes, topological_order,
    )
    from acosplatform.temporal.activities import (
        NodeInput,
        execute_start_node, execute_end_node, execute_orchestrator_node,
        execute_agent_node, execute_sub_agent_node,
        execute_integration_node, execute_logic_node,
    )
    from temporalio.common import RetryPolicy

_RETRY   = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2))
_TIMEOUT = timedelta(seconds=60)

_ACTIVITY_FN = {
    "startNode":        execute_start_node,
    "endNode":          execute_end_node,
    "orchestratorNode": execute_orchestrator_node,
    "agentNode":        execute_agent_node,
    "subAgentNode":     execute_sub_agent_node,
    "integrationNode":  execute_integration_node,
    "logicNode":        execute_logic_node,
    "triggerNode":      execute_start_node,
}


@workflow.defn(name="GraphWorkflow")
class GraphWorkflow:
    @workflow.run
    async def run(self, graph: dict, ctx: dict) -> dict:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            return {"error": "empty graph", "nodes_executed": 0}

        ordered  = topological_order({"nodes": nodes, "edges": edges})
        start    = find_start_node(nodes)
        cleared: set[str]  = {start["id"]}
        results: dict[str, dict] = {}
        exec_ctx = dict(ctx)

        for node in ordered:
            nid = node["id"]
            if nid not in cleared:
                continue

            activity_fn = _ACTIVITY_FN.get(node["type"])
            if not activity_fn:
                workflow.logger.warning("Unknown node type %s — skipping", node["type"])
                continue

            node_result: dict = await workflow.execute_activity(
                activity_fn,
                NodeInput(node=node, ctx=exec_ctx, upstream=results),
                start_to_close_timeout=_TIMEOUT,
                retry_policy=_RETRY,
            )
            results[nid]  = node_result
            exec_ctx      = {**exec_ctx, **node_result}

            for downstream in next_nodes(nid, edges, nodes, exec_ctx):
                cleared.add(downstream["id"])

        return {
            "nodes_executed": len(results),
            "results": results,
            "final_context": exec_ctx,
        }
