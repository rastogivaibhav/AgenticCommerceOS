"""Helper used by the Ops API to start and query GraphWorkflow runs."""
from __future__ import annotations
import os
import uuid

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
