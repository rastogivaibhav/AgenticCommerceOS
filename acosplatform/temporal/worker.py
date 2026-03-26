"""Entry point: python -m acosplatform.temporal.worker"""
import asyncio
import logging
import os

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
