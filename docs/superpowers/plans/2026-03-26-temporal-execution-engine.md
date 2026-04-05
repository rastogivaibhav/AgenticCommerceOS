# Temporal Execution Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the ACOS workflow canvas to a Temporal-backed execution engine so that graphs designed in the UI can be durably executed, retried on failure, and observed in real time.

**Architecture:** The ReactFlow canvas serialises a workflow graph (nodes + edges) as JSON into `step_definitions` in the DB. A new `acosplatform/temporal/` module defines a `GraphWorkflow` Temporal workflow that deserialises this JSON and walks it node-by-node, dispatching a typed Temporal Activity per node type. A `temporal-worker` Docker service runs the worker process; the Ops API exposes `POST /workflows/{id}/run` which uses the Temporal Python client to start an execution. The UI editor gains a **Run** button and a live run-status panel.

**Tech Stack:** `temporalio` Python SDK >= 1.7, Temporal server `temporalio/auto-setup:1.25`, Temporal UI `temporalio/ui:2.31`, FastAPI async endpoint, React useEffect polling for run status.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `acosplatform/temporal/__init__.py` | Package marker |
| Create | `acosplatform/temporal/activities.py` | One `@activity` per canvas node type |
| Create | `acosplatform/temporal/graph_walker.py` | Pure graph traversal logic (topological sort + condition eval) |
| Create | `acosplatform/temporal/workflows.py` | `GraphWorkflow` — calls activities in graph order |
| Create | `acosplatform/temporal/worker.py` | Worker process entry point (`python -m acosplatform.temporal.worker`) |
| Create | `acosplatform/temporal/client.py` | `start_graph_run()` helper used by the API |
| Create | `tests/temporal/test_graph_walker.py` | Unit tests for graph traversal and condition eval — no Temporal SDK required |
| Create | `tests/temporal/test_activities.py` | Unit tests for each activity function (mock plugins) |
| Modify | `requirements.txt` | Add `temporalio>=1.7.0` |
| Modify | `docker-compose.yml` | Add `temporal`, `temporal-ui`, `temporal-worker` services |
| Modify | `db/schema.sql` | Add `workflow_graph_runs` table |
| Modify | `apps/ops_api/main.py` | Add `POST /workflows/{id}/run` and `GET /workflows/{id}/runs` |
| Modify | `apps/ops_ui_v2/src/pages/WorkflowEditor.jsx` | Add Run button + run status panel |
| Modify | `apps/ops_ui_v2/src/api/workflowAPI.js` | Add `runWorkflow()` and `getWorkflowRuns()` |

---

## Task 1 — Pure graph walker (no Temporal, no I/O)

**Files:**
- Create: `acosplatform/temporal/graph_walker.py`
- Create: `tests/temporal/test_graph_walker.py`

This is the only pure logic layer. Everything else depends on it. Test it exhaustively here so the rest of the tasks are easy.

- [ ] **1.1 Create the test file with failing tests**

```python
# tests/temporal/test_graph_walker.py
import pytest
from acosplatform.temporal.graph_walker import (
    build_adjacency,
    find_start_node,
    evaluate_edge_condition,
    topological_order,
    next_nodes,
)

SIMPLE_GRAPH = {
    "nodes": [
        {"id": "s1", "type": "startNode", "data": {"triggerType": "manual"}},
        {"id": "a1", "type": "agentNode",  "data": {"agentId": "ag_triage", "label": "Triage"}},
        {"id": "e1", "type": "endNode",    "data": {"outcomeType": "success"}},
    ],
    "edges": [
        {"id": "es", "source": "s1", "target": "a1", "data": {}},
        {"id": "ea", "source": "a1", "target": "e1", "data": {}},
    ],
}

BRANCH_GRAPH = {
    "nodes": [
        {"id": "s1", "type": "startNode",       "data": {}},
        {"id": "o1", "type": "orchestratorNode", "data": {}},
        {"id": "a1", "type": "agentNode",        "data": {}},
        {"id": "a2", "type": "agentNode",        "data": {}},
        {"id": "e1", "type": "endNode",          "data": {}},
    ],
    "edges": [
        {"id": "e1", "source": "s1", "target": "o1", "data": {}},
        {"id": "e2", "source": "o1", "target": "a1",
         "data": {"condition": {"field": "score", "operator": ">", "value": "0.8"}}},
        {"id": "e3", "source": "o1", "target": "a2",
         "data": {"condition": {"field": "score", "operator": "<=", "value": "0.8"}}},
        {"id": "e4", "source": "a1", "target": "e1", "data": {}},
        {"id": "e5", "source": "a2", "target": "e1", "data": {}},
    ],
}

def test_build_adjacency_simple():
    adj = build_adjacency(SIMPLE_GRAPH["edges"])
    assert adj["s1"] == ["a1"]
    assert adj["a1"] == ["e1"]

def test_find_start_node():
    node = find_start_node(SIMPLE_GRAPH["nodes"])
    assert node["id"] == "s1"

def test_find_start_node_missing_raises():
    with pytest.raises(ValueError, match="No startNode"):
        find_start_node([{"id": "x", "type": "agentNode", "data": {}}])

def test_evaluate_edge_condition_no_condition():
    assert evaluate_edge_condition({}, {}) is True
    assert evaluate_edge_condition({"condition": None}, {}) is True

def test_evaluate_edge_condition_eq():
    cond = {"condition": {"field": "status", "operator": "==", "value": "placed"}}
    assert evaluate_edge_condition(cond, {"status": "placed"}) is True
    assert evaluate_edge_condition(cond, {"status": "pending"}) is False

def test_evaluate_edge_condition_gt():
    cond = {"condition": {"field": "score", "operator": ">", "value": "0.8"}}
    assert evaluate_edge_condition(cond, {"score": 0.9}) is True
    assert evaluate_edge_condition(cond, {"score": 0.5}) is False

def test_evaluate_edge_condition_contains():
    cond = {"condition": {"field": "message", "operator": "contains", "value": "refund"}}
    assert evaluate_edge_condition(cond, {"message": "I want a refund"}) is True
    assert evaluate_edge_condition(cond, {"message": "show me laptops"}) is False

def test_topological_order_simple():
    order = topological_order(SIMPLE_GRAPH)
    ids = [n["id"] for n in order]
    assert ids.index("s1") < ids.index("a1") < ids.index("e1")

def test_next_nodes_with_condition():
    ctx = {"score": 0.9}
    nxt = next_nodes("o1", BRANCH_GRAPH["edges"], BRANCH_GRAPH["nodes"], ctx)
    assert len(nxt) == 1
    assert nxt[0]["id"] == "a1"

def test_next_nodes_no_condition_returns_all():
    ctx = {}
    nxt = next_nodes("s1", SIMPLE_GRAPH["edges"], SIMPLE_GRAPH["nodes"], ctx)
    assert nxt[0]["id"] == "a1"
```

- [ ] **1.2 Run tests — expect all to FAIL**

```bash
cd C:\Users\vrast\OneDrive\Apps\Documents\acos
python -m pytest tests/temporal/test_graph_walker.py -v
```
Expected: `ModuleNotFoundError: No module named 'acosplatform.temporal'`

- [ ] **1.3 Create the module**

```python
# acosplatform/temporal/__init__.py
# (empty — package marker only)
```

```python
# acosplatform/temporal/graph_walker.py
"""Pure graph traversal and condition evaluation — no I/O, no Temporal SDK."""
from __future__ import annotations


def build_adjacency(edges: list[dict]) -> dict[str, list[str]]:
    """Return {source_id: [target_id, ...]} from an edge list."""
    adj: dict[str, list[str]] = {}
    for edge in edges:
        adj.setdefault(edge["source"], []).append(edge["target"])
    return adj


def find_start_node(nodes: list[dict]) -> dict:
    """Return the single startNode; raise ValueError if absent."""
    for node in nodes:
        if node.get("type") in ("startNode", "triggerNode"):
            return node
    raise ValueError("No startNode found in graph — canvas must have a Start node")


def evaluate_edge_condition(edge_data: dict, ctx: dict) -> bool:
    """
    Return True if the edge should be followed given the current execution context.
    An edge with no condition (or condition=None) is always followed.
    """
    condition = edge_data.get("condition")
    if not condition:
        return True
    field    = condition.get("field", "")
    operator = condition.get("operator", "==")
    value    = condition.get("value", "")
    actual   = ctx.get(field)
    if actual is None:
        return False
    try:
        if operator == "==":           return str(actual) == str(value)
        if operator == "!=":           return str(actual) != str(value)
        if operator == ">":            return float(actual) > float(value)
        if operator == ">=":           return float(actual) >= float(value)
        if operator == "<":            return float(actual) < float(value)
        if operator == "<=":           return float(actual) <= float(value)
        if operator == "contains":     return str(value).lower() in str(actual).lower()
        if operator == "not_contains": return str(value).lower() not in str(actual).lower()
    except (TypeError, ValueError):
        return False
    return True


def next_nodes(
    node_id: str,
    edges: list[dict],
    nodes: list[dict],
    ctx: dict,
) -> list[dict]:
    """Return nodes reachable from node_id whose edge conditions pass."""
    node_map = {n["id"]: n for n in nodes}
    outgoing = [e for e in edges if e["source"] == node_id]
    result = []
    for edge in outgoing:
        if evaluate_edge_condition(edge.get("data", {}), ctx):
            target = node_map.get(edge["target"])
            if target:
                result.append(target)
    return result


def topological_order(graph: dict) -> list[dict]:
    """
    Return nodes in a valid execution order (Kahn's algorithm).
    Raises ValueError if a cycle is detected.
    """
    nodes    = graph["nodes"]
    edges    = graph["edges"]
    node_map = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    for edge in edges:
        in_degree[edge["target"]] = in_degree.get(edge["target"], 0) + 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order: list[dict] = []
    while queue:
        nid = queue.pop(0)
        order.append(node_map[nid])
        for edge in edges:
            if edge["source"] == nid:
                in_degree[edge["target"]] -= 1
                if in_degree[edge["target"]] == 0:
                    queue.append(edge["target"])
    if len(order) != len(nodes):
        raise ValueError("Cycle detected in workflow graph")
    return order
```

- [ ] **1.4 Run tests — all should pass**

```bash
python -m pytest tests/temporal/test_graph_walker.py -v
```
Expected: `8 passed`

- [ ] **1.5 Commit**

```bash
git add acosplatform/temporal/ tests/temporal/test_graph_walker.py
git commit -m "feat(temporal): add pure graph walker with topological sort and edge condition eval"
```

---

## Task 2 — Temporal activities (one per node type)

**Files:**
- Create: `acosplatform/temporal/activities.py`
- Create: `tests/temporal/test_activities.py`

Activities are plain async Python functions decorated with `@activity.defn`. They call the existing ACOS plugins. Keep them thin — they are the glue layer, not where logic lives.

> **Security note on logicNode (code type):** The plan defers dynamic code evaluation to a future sandboxed implementation (e.g. RestrictedPython or a subprocess jail). For beta the `code` logicNode simply passes context through unchanged and logs a warning.

- [ ] **2.1 Install temporalio**

Add to `requirements.txt`:
```
temporalio>=1.7.0
```

```bash
pip install "temporalio>=1.7.0"
```

- [ ] **2.2 Write failing tests**

```python
# tests/temporal/test_activities.py
import pytest
from unittest.mock import patch, MagicMock
from acosplatform.temporal.activities import (
    execute_agent_node,
    execute_integration_node,
    execute_logic_node,
    execute_orchestrator_node,
    NodeInput,
)


@pytest.mark.asyncio
async def test_agent_node_calls_run_adk():
    node = {"id": "a1", "type": "agentNode", "data": {"agentId": "ag_triage", "label": "Triage"}}
    ctx  = {"customer_id": "cust-1", "message": "buy headphones", "tenant_id": "default"}
    with patch("acosplatform.temporal.activities.run_adk") as mock_adk:
        mock_adk.return_value = {"response": "Here are some headphones"}
        result = await execute_agent_node(NodeInput(node=node, ctx=ctx, upstream={}))
    mock_adk.assert_called_once()
    assert "response" in result


@pytest.mark.asyncio
async def test_integration_node_catalog_skill():
    node = {"id": "i1", "type": "integrationNode", "data": {"skillId": "catalog", "label": "Search"}}
    ctx  = {"message": "laptops", "tenant_id": "default"}
    with patch("acosplatform.temporal.activities.catalog") as mock_catalog:
        mock_catalog.search.return_value = {"products": [{"id": "p1"}]}
        result = await execute_integration_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert "products" in result


@pytest.mark.asyncio
async def test_integration_node_unknown_skill_skips():
    node = {"id": "i2", "type": "integrationNode", "data": {"skillId": "unknown_skill"}}
    ctx  = {}
    result = await execute_integration_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert result.get("skipped") is True


@pytest.mark.asyncio
async def test_logic_node_passes_context_through():
    node = {"id": "l1", "type": "logicNode", "data": {"logicType": "switch"}}
    ctx  = {"score": 0.9}
    result = await execute_logic_node(NodeInput(node=node, ctx=ctx, upstream={"score": 0.9}))
    assert result.get("score") == 0.9


@pytest.mark.asyncio
async def test_orchestrator_node_returns_dispatch_signal():
    node = {"id": "o1", "type": "orchestratorNode", "data": {"agentId": "", "label": "Orch"}}
    ctx  = {"tenant_id": "default"}
    result = await execute_orchestrator_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert result.get("orchestrated") is True
```

- [ ] **2.3 Run — expect ImportError**

```bash
python -m pytest tests/temporal/test_activities.py -v
```

- [ ] **2.4 Implement activities**

```python
# acosplatform/temporal/activities.py
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
```

- [ ] **2.5 Run activity tests — all pass**

```bash
python -m pytest tests/temporal/test_activities.py -v
```
Expected: `5 passed`

- [ ] **2.6 Commit**

```bash
git add acosplatform/temporal/activities.py tests/temporal/test_activities.py requirements.txt
git commit -m "feat(temporal): add typed activities for all canvas node types"
```

---

## Task 3 — GraphWorkflow

**Files:**
- Create: `acosplatform/temporal/workflows.py`

- [ ] **3.1 Implement GraphWorkflow**

```python
# acosplatform/temporal/workflows.py
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
```

- [ ] **3.2 Verify import**

```bash
python -c "from acosplatform.temporal.workflows import GraphWorkflow; print('OK')"
```

- [ ] **3.3 Commit**

```bash
git add acosplatform/temporal/workflows.py
git commit -m "feat(temporal): add GraphWorkflow that walks canvas graph via typed activities"
```

---

## Task 4 — Worker process and Docker

**Files:**
- Create: `acosplatform/temporal/worker.py`
- Create: `acosplatform/temporal/client.py`
- Modify: `docker-compose.yml`

- [ ] **4.1 Implement worker**

```python
# acosplatform/temporal/worker.py
"""Entry point: python -m acosplatform.temporal.worker"""
import asyncio, logging, os
from temporalio.client import Client
from temporalio.worker import Worker
from acosplatform.temporal.activities import (
    execute_start_node, execute_end_node, execute_orchestrator_node,
    execute_agent_node, execute_sub_agent_node,
    execute_integration_node, execute_logic_node,
)
from acosplatform.temporal.workflows import GraphWorkflow

logger    = logging.getLogger(__name__)
TASK_QUEUE = "acos-graph-workflows"


async def main() -> None:
    host   = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(host)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GraphWorkflow],
        activities=[
            execute_start_node, execute_end_node, execute_orchestrator_node,
            execute_agent_node, execute_sub_agent_node,
            execute_integration_node, execute_logic_node,
        ],
    )
    logger.info("Worker started on queue '%s'", TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

- [ ] **4.2 Implement client helper**

```python
# acosplatform/temporal/client.py
"""Helper used by the Ops API to start and query GraphWorkflow runs."""
from __future__ import annotations
import os, uuid
from temporalio.client import Client, WorkflowExecutionStatus
from acosplatform.temporal.workflows import GraphWorkflow

TASK_QUEUE = "acos-graph-workflows"
_client: Client | None = None


async def _get_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(os.getenv("TEMPORAL_HOST", "localhost:7233"))
    return _client


async def start_graph_run(workflow_id: str, graph: dict, ctx: dict) -> dict:
    client = await _get_client()
    run_id = f"grun-{uuid.uuid4().hex[:10]}"
    handle = await client.start_workflow(
        GraphWorkflow.run, args=[graph, ctx],
        id=run_id, task_queue=TASK_QUEUE,
    )
    return {"run_id": run_id, "workflow_id": workflow_id,
            "temporal_run_id": handle.first_execution_run_id, "status": "running"}


async def get_run_status(run_id: str) -> dict:
    client = await _get_client()
    try:
        desc   = await client.get_workflow_handle(run_id).describe()
        status_map = {
            WorkflowExecutionStatus.RUNNING:    "running",
            WorkflowExecutionStatus.COMPLETED:  "completed",
            WorkflowExecutionStatus.FAILED:     "failed",
            WorkflowExecutionStatus.TIMED_OUT:  "timed_out",
            WorkflowExecutionStatus.TERMINATED: "terminated",
            WorkflowExecutionStatus.CANCELED:   "cancelled",
        }
        return {
            "run_id":     run_id,
            "status":     status_map.get(desc.status, "unknown"),
            "start_time": desc.start_time.isoformat() if desc.start_time else None,
            "close_time": desc.close_time.isoformat() if desc.close_time else None,
        }
    except Exception as exc:
        return {"run_id": run_id, "status": "not_found", "error": str(exc)}
```

- [ ] **4.3 Add Temporal services to docker-compose.yml**

Append inside the `services:` block (after `ops-api`):

```yaml
  temporal:
    image: temporalio/auto-setup:1.25.1
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql12
      - DB_PORT=5432
      - POSTGRES_USER=acos
      - POSTGRES_PWD=${DB_PASSWORD}
      - POSTGRES_SEEDS=db
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  temporal-ui:
    image: temporalio/ui:2.31.2
    ports:
      - "8088:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:8088
    depends_on:
      - temporal
    restart: unless-stopped

  temporal-worker:
    build: .
    command: python -m acosplatform.temporal.worker
    depends_on:
      - temporal
      - db
    environment:
      - TEMPORAL_HOST=temporal:7233
      - DATABASE_URL=postgresql://acos:${DB_PASSWORD}@db:5432/acos
      - DB_POOL_MAX=${DB_POOL_MAX:-10}
      - PYTHONPATH=/app
      - GOOGLE_API_KEY=${GOOGLE_API_KEY:-}
    restart: unless-stopped
```

Also add `TEMPORAL_HOST=localhost:7233` to `.env.example`.

- [ ] **4.4 Smoke-test worker locally (requires Temporal running)**

```bash
docker compose up temporal -d
# Wait 15 seconds, then:
python -m acosplatform.temporal.worker
```
Expected: `Worker started on queue 'acos-graph-workflows'`
Press Ctrl+C to stop.

- [ ] **4.5 Commit**

```bash
git add acosplatform/temporal/worker.py acosplatform/temporal/client.py docker-compose.yml
git commit -m "feat(temporal): add worker process and docker-compose services"
```

---

## Task 5 — DB table for graph run history

**Files:**
- Modify: `db/schema.sql`
- Modify: `acosplatform/db/repository.py`

- [ ] **5.1 Append to db/schema.sql**

```sql
-- Temporal graph execution runs
CREATE TABLE IF NOT EXISTS workflow_graph_runs (
    id           TEXT PRIMARY KEY,
    workflow_id  TEXT NOT NULL,
    tenant_id    TEXT NOT NULL DEFAULT 'default',
    status       TEXT NOT NULL DEFAULT 'running',
    graph        JSONB NOT NULL DEFAULT '{}',
    ctx          JSONB NOT NULL DEFAULT '{}',
    result       JSONB,
    started_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at  TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_wgr_workflow ON workflow_graph_runs(workflow_id);
```

- [ ] **5.2 Add three repository functions to acosplatform/db/repository.py**

Use the same `transaction()` context manager pattern already used everywhere in the file.
Find where other `save_*` functions are defined and add after them:

```python
def save_graph_run(run_id: str, workflow_id: str, tenant_id: str,
                   graph: dict, ctx: dict, status: str = "running") -> dict:
    if not _use_db():
        return {"id": run_id, "workflow_id": workflow_id, "status": status}
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO workflow_graph_runs
                           (id, workflow_id, tenant_id, graph, ctx, status)
                       VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status
                       RETURNING *""",
                    (run_id, workflow_id, tenant_id,
                     json.dumps(graph), json.dumps(ctx), status),
                )
                return dict(cur.fetchone())
    except Exception as e:
        logger.warning("save_graph_run failed: %s", e)
        return {"id": run_id, "workflow_id": workflow_id, "status": status}


def update_graph_run(run_id: str, status: str, result: dict | None = None) -> None:
    if not _use_db():
        return
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE workflow_graph_runs
                       SET status=%s, result=%s, finished_at=NOW()
                       WHERE id=%s""",
                    (status, json.dumps(result) if result else None, run_id),
                )
    except Exception as e:
        logger.warning("update_graph_run failed: %s", e)


def get_graph_runs(workflow_id: str, limit: int = 25) -> list[dict]:
    if not _use_db():
        return []
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT * FROM workflow_graph_runs
                       WHERE workflow_id=%s ORDER BY started_at DESC LIMIT %s""",
                    (workflow_id, limit),
                )
                return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning("get_graph_runs failed: %s", e)
        return []
```

- [ ] **5.3 Apply migration (if DB is running)**

```bash
make migrate
```

- [ ] **5.4 Commit**

```bash
git add db/schema.sql acosplatform/db/repository.py
git commit -m "feat(temporal): add workflow_graph_runs table and repository helpers"
```

---

## Task 6 — Ops API run endpoints

**Files:**
- Modify: `apps/ops_api/main.py`

- [ ] **6.1 Add imports to main.py**

Patch the existing `from fastapi import` line and add the temporal/repository imports:
```python
# Existing line — add HTTPException:
from fastapi import Depends, FastAPI, HTTPException, Request

# New lines below the existing imports block:
from acosplatform.temporal.client import get_run_status, start_graph_run
from acosplatform.db.repository import get_graph_runs, get_workflow_versions, save_graph_run
from pydantic import BaseModel
```

- [ ] **6.2 Add three endpoints**

```python
class WorkflowRunRequest(BaseModel):
    ctx: dict = {}
    tenant_id: str = "default"


@app.post("/workflows/{workflow_id}/run", dependencies=[Depends(require_ops_token)])
async def trigger_workflow_run(workflow_id: str, body: WorkflowRunRequest):
    versions = get_workflow_versions(workflow_id)
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found")
    latest = sorted(versions, key=lambda v: v.get("created_at", ""))[-1]
    graph  = latest.get("step_definitions") or {}
    if not graph.get("nodes"):
        raise HTTPException(
            status_code=422,
            detail="No canvas graph saved — open the editor and click Save Workflow first."
        )
    run_meta = await start_graph_run(
        workflow_id=workflow_id,
        graph=graph,
        ctx={"tenant_id": body.tenant_id, **body.ctx},
    )
    save_graph_run(
        run_id=run_meta["run_id"], workflow_id=workflow_id,
        tenant_id=body.tenant_id, graph=graph, ctx=body.ctx,
    )
    return run_meta


@app.get("/workflows/{workflow_id}/runs", dependencies=[Depends(require_ops_token)])
async def list_workflow_runs(workflow_id: str, limit: int = 20):
    return {"runs": get_graph_runs(workflow_id, limit=limit)}


@app.get("/workflows/runs/{run_id}/status", dependencies=[Depends(require_ops_token)])
async def poll_run_status(run_id: str):
    return await get_run_status(run_id)
```

- [ ] **6.3 Verify the API boots**

```bash
python -m uvicorn apps.ops_api.main:app --port 8081
```
Expected: no import errors. Ctrl+C.

- [ ] **6.4 Commit**

```bash
git add apps/ops_api/main.py
git commit -m "feat(temporal): add POST /workflows/{id}/run and run history endpoints"
```

---

## Task 7 — UI: Run button + run history panel

**Files:**
- Modify: `apps/ops_ui_v2/src/api/workflowAPI.js`
- Modify: `apps/ops_ui_v2/src/pages/WorkflowEditor.jsx`

- [ ] **7.1 Add API helpers to workflowAPI.js**

```js
export async function runWorkflow(id, ctx = {}) {
  const res = await fetch(`${API_BASE}/workflows/${id}/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('ops_token') || 'dev-ops-token'}`,
    },
    body: JSON.stringify({ ctx }),
  });
  if (!res.ok) throw new Error(`Run failed: ${res.status}`);
  return res.json();
}

export async function getWorkflowRuns(id) {
  const res = await fetch(`${API_BASE}/workflows/${id}/runs`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('ops_token') || 'dev-ops-token'}` },
  });
  if (!res.ok) return { runs: [] };
  return res.json();
}
```

- [ ] **7.2 Update WorkflowEditor.jsx**

1. Import additions at top:
```js
// Patch the existing lucide-react line — add Play:
import { ArrowLeft, Save, GitBranch, Loader2, Play } from 'lucide-react';
// Add new API import:
import { runWorkflow, getWorkflowRuns } from '../api/workflowAPI';
```

2. New state:
```js
const [runs, setRuns] = useState([]);
const [running, setRunning] = useState(false);
const [showRuns, setShowRuns] = useState(false);
```

3. Load existing runs alongside the workflow fetch:
```js
getWorkflowRuns(id).then(d => setRuns(d.runs || [])).catch(() => {});
```

4. handleRun function:
```js
const handleRun = async () => {
  setRunning(true);
  try {
    await handleSave();
    const meta = await runWorkflow(id);
    setRuns(prev => [{ ...meta, started_at: new Date().toISOString() }, ...prev]);
    setShowRuns(true);
  } catch (e) {
    console.error(e);
    setSaveMsg('Run failed');
  } finally {
    setRunning(false);
  }
};
```

5. Run button in header (after Save Workflow button):
```jsx
<button onClick={handleRun} disabled={running} style={{
  display:'flex', alignItems:'center', gap:'7px',
  background: running ? '#374151' : '#22c55e',
  border:'none', color:'#fff', padding:'8px 18px',
  borderRadius:'8px', fontWeight:600,
  cursor: running ? 'not-allowed' : 'pointer', fontSize:'13px',
}}>
  {running ? <Loader2 size={14} style={{animation:'spin 1s linear infinite'}} /> : <Play size={14} />}
  Run
</button>
```

6. Run history drawer (inside the `flexGrow:1` canvas div, absolute positioned):
```jsx
{showRuns && (
  <div style={{
    position:'absolute', bottom:0, left:230, right:0,
    maxHeight:200, background:'#111318',
    borderTop:'1px solid #1f2937', overflowY:'auto', zIndex:15,
  }}>
    <div style={{padding:'8px 16px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
      <span style={{fontSize:'11px', color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.5px'}}>
        Run History
      </span>
      <button onClick={() => setShowRuns(false)}
        style={{background:'transparent', border:'none', color:'#6b7280', cursor:'pointer', fontSize:'16px'}}>
        ×
      </button>
    </div>
    {runs.length === 0 && (
      <div style={{padding:'12px 16px', color:'#4b5563', fontSize:'12px'}}>No runs yet</div>
    )}
    {runs.map(r => (
      <div key={r.run_id} style={{
        padding:'6px 16px', display:'flex', gap:'16px', fontSize:'12px',
        borderTop:'1px solid rgba(255,255,255,0.04)',
      }}>
        <span style={{fontFamily:'monospace', color:'#6b7280', minWidth:160}}>{r.run_id}</span>
        <span style={{color: r.status==='completed' ? '#4ade80' : r.status==='failed' ? '#f87171' : '#facc15'}}>
          {r.status}
        </span>
        <span style={{color:'#4b5563'}}>{r.started_at?.slice(0,19)?.replace('T',' ')}</span>
      </div>
    ))}
  </div>
)}
```

- [ ] **7.3 Build check**

```bash
cd apps/ops_ui_v2 && npm run build
```
Expected: no errors.

- [ ] **7.4 Commit**

```bash
git add apps/ops_ui_v2/src/api/workflowAPI.js apps/ops_ui_v2/src/pages/WorkflowEditor.jsx
git commit -m "feat(ui): add Run button and run history panel to workflow editor"
```

---

## Task 8 — End-to-end smoke test

- [ ] **8.1 Full stack up**

```bash
docker compose up --build -d
docker compose logs temporal-worker --follow
```
Expected: `Worker started on queue 'acos-graph-workflows'`

- [ ] **8.2 Create and run a workflow from the UI**

1. `http://localhost:5173/ui/workflows` → Create Workflow → name it `smoke-test`
2. Editor opens → canvas shows Start → End starter graph
3. Click **Save Workflow** → confirm "Saved" appears
4. Click **Run** → run history drawer opens with a `running` entry
5. Wait ~5 seconds → refresh page → entry should show `completed`

- [ ] **8.3 Verify Temporal UI**

`http://localhost:8088` — `smoke-test` workflow execution listed with status `Completed`

- [ ] **8.4 Verify DB**

```bash
docker compose exec db psql -U acos -d acos \
  -c "SELECT id, workflow_id, status FROM workflow_graph_runs ORDER BY started_at DESC LIMIT 5;"
```
Expected: row with `status = running` or `completed`.

- [ ] **8.5 Final commit**

```bash
git add .
git commit -m "feat(temporal): Temporal execution engine complete — end-to-end graph runs"
```

---

## Environment variables — add to .env.example

```
TEMPORAL_HOST=localhost:7233
```

## What this does NOT include (future work)

- Real-time WebSocket push for live node-by-node status in the canvas
- Per-node execution highlighting
- CRON-scheduled workflow triggers via Temporal Schedules API
- RBAC on who can trigger runs
- Temporal namespace isolation per tenant
- Sandboxed code evaluator for logicNode `code` type
