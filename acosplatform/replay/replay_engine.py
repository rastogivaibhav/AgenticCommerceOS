"""Replay engine – replays a stored run through the journey engine."""

import logging

from acosplatform.db.repository import get_run
from acosplatform.journey.engine import run_journey

logger = logging.getLogger(__name__)


def replay(run_id):
    """Replay a previously stored run by re-executing its input.

    Fetches the original run's input from the DB, then passes it back
    through the journey engine to produce a new run.
    """
    original = get_run(run_id)
    if not original:
        return {"success": False, "error": f"Run {run_id} not found"}

    # Extract the original input
    original_input = original.get("input", {})
    if isinstance(original_input, str):
        import json
        try:
            original_input = json.loads(original_input)
        except Exception:
            original_input = {"message": original_input}

    # Build the replay payload
    payload = {
        "message": original_input.get("message", ""),
        "customer_id": original_input.get("customer_id", original.get("customer_id", "anon")),
        "tenant_id": original_input.get("tenant_id", original.get("tenant_id", "default")),
    }

    # Re-execute
    new_result = run_journey(payload)

    return {
        "success": True,
        "original_run_id": run_id,
        "new_run_id": new_result.get("run_id"),
        "original_journey": original.get("journey"),
        "new_journey": new_result.get("journey"),
        "result": new_result.get("result"),
    }
