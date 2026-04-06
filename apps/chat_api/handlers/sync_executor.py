"""Synchronous workflow execution handler.

Executes workflows inline for fast responses (< 2 seconds).
Used for simple lookups and status queries that don't require
background processing.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SyncExecutor:
    """Synchronous workflow executor.

    Executes workflow steps inline and returns results directly.
    Useful for simple queries and lookups where response time < 2s.

    Returns results as dicts (not Job objects).
    """

    def __init__(self):
        """Initialize SyncExecutor."""
        pass

    def execute(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a workflow synchronously.

        Args:
            workflow: Workflow definition with workflow_id, workflow_name, timeout_seconds, steps
            input_data: Input data for the workflow

        Returns:
            Dict with status, result, and execution_time_ms
        """
        start_time = time.time()

        try:
            workflow_id = workflow.get("workflow_id", "unknown")
            workflow_name = workflow.get("workflow_name", "Unknown")
            timeout_seconds = workflow.get("timeout_seconds", 2)
            steps = workflow.get("steps", [])

            logger.info(
                f"Starting sync execution of workflow {workflow_name} ({workflow_id})",
                extra={"workflow_id": workflow_id, "timeout_seconds": timeout_seconds},
            )

            # Execute workflow steps
            execution_result = self._execute_steps(
                steps=steps,
                input_data=input_data,
                workflow_id=workflow_id,
                timeout_seconds=timeout_seconds,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Sync workflow {workflow_name} completed in {elapsed_ms}ms",
                extra={
                    "workflow_id": workflow_id,
                    "execution_time_ms": elapsed_ms,
                },
            )

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "result": execution_result,
                "execution_time_ms": elapsed_ms,
                "executed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Sync workflow execution failed: {str(e)}",
                extra={
                    "workflow_id": workflow.get("workflow_id"),
                    "error": str(e),
                },
                exc_info=True,
            )

            return {
                "status": "failed",
                "workflow_id": workflow.get("workflow_id"),
                "error": str(e),
                "execution_time_ms": elapsed_ms,
                "executed_at": datetime.now(UTC).isoformat(),
            }

    def _execute_steps(
        self,
        steps: list,
        input_data: Dict[str, Any],
        workflow_id: str,
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        """Execute workflow steps sequentially.

        Args:
            steps: List of step definitions
            input_data: Input data from user
            workflow_id: Workflow identifier
            timeout_seconds: Timeout in seconds

        Returns:
            Aggregated results from all steps
        """
        if not steps:
            # No steps to execute, return input as output
            return {"message": "Workflow completed with no steps", "input": input_data}

        results = {}

        for step in steps:
            step_id = step.get("step_id", "step_unknown")
            agent = step.get("agent", "unknown_agent")
            step_input = step.get("input", {})

            logger.debug(
                f"Executing step {step_id} with agent {agent}",
                extra={"workflow_id": workflow_id, "step_id": step_id},
            )

            # Merge input data with step input
            merged_input = {**input_data, **step_input}

            # Execute the step (mock executor - in real scenario would call actual agent)
            step_result = self._execute_step(
                agent=agent,
                step_input=merged_input,
            )

            results[step_id] = step_result

        return results

    def _execute_step(
        self,
        agent: str,
        step_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single step (basic implementation).

        In production, this would dispatch to actual agents via MCP.
        For now, returns a mock result structure.

        Args:
            agent: Agent name/ID
            step_input: Input for the agent

        Returns:
            Result from agent execution
        """
        # Mock executor - in real scenario would call actual agent
        # For testing purposes, return a structured result
        return {
            "agent": agent,
            "status": "completed",
            "output": {
                "message": f"Executed {agent} with input {step_input}",
                "input": step_input,
            },
        }
