"""AgentFabric integration – tracing, event logging, and policy checks.

Fails safely if AgentFabric is unavailable (returns allow-all defaults).
"""

import os
import uuid
import logging
from datetime import datetime, UTC

import requests

logger = logging.getLogger(__name__)

_base_url = os.environ.get("AGENTFABRIC_URL", "")
_api_key = os.environ.get("AGENTFABRIC_API_KEY", "")
_enabled = bool(_base_url and _api_key)

# In-memory trace store for local mode
_traces = {}


def _is_available():
    if not _enabled:
        return False
    try:
        resp = requests.get(f"{_base_url}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def start_trace(run_id, ctx):
    """Start a trace for a journey run.

    Returns a trace_id string.
    """
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"
    trace = {
        "trace_id": trace_id,
        "run_id": run_id,
        "customer_id": ctx.get("customer_id", "anon"),
        "tenant_id": ctx.get("tenant_id", "default"),
        "started_at": datetime.now(UTC).isoformat(),
        "events": [],
    }

    if _enabled:
        try:
            resp = requests.post(
                f"{_base_url}/traces",
                json=trace,
                headers={"Authorization": f"Bearer {_api_key}"},
                timeout=3,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                trace_id = data.get("trace_id", trace_id)
                logger.info(f"AgentFabric trace started: {trace_id}")
            else:
                logger.warning(f"AgentFabric start_trace returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"AgentFabric start_trace failed: {e}")

    _traces[trace_id] = trace
    return trace_id


def log_event(trace_id, event_type, payload=None):
    """Log an event to the trace.

    Fails silently if AgentFabric is not available.
    """
    event = {
        "trace_id": trace_id,
        "event_type": event_type,
        "payload": payload or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Store locally
    if trace_id in _traces:
        _traces[trace_id]["events"].append(event)

    if _enabled:
        try:
            requests.post(
                f"{_base_url}/traces/{trace_id}/events",
                json=event,
                headers={"Authorization": f"Bearer {_api_key}"},
                timeout=2,
            )
        except Exception as e:
            logger.debug(f"AgentFabric log_event failed: {e}")


def policy_check(trace_id, ctx, result):
    """Check policy before finalizing a journey.

    Returns a policy decision dict. Defaults to allow-all if unavailable.
    """
    default_allow = {
        "allowed": True,
        "source": "default",
        "reason": "No policy restrictions",
        "checked_at": datetime.now(UTC).isoformat(),
    }

    if _enabled:
        try:
            resp = requests.post(
                f"{_base_url}/policy/check",
                json={
                    "trace_id": trace_id,
                    "tenant_id": ctx.get("tenant_id", "default"),
                    "customer_id": ctx.get("customer_id", "anon"),
                    "journey": result.get("journey_type", "unknown"),
                    "cart_total": _extract_cart_total(result),
                },
                headers={"Authorization": f"Bearer {_api_key}"},
                timeout=3,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["source"] = "agentfabric"
                return data
        except Exception as e:
            logger.warning(f"AgentFabric policy_check failed: {e}")

    return default_allow


def get_trace(trace_id):
    """Get a trace by ID (local store)."""
    return _traces.get(trace_id)


def _extract_cart_total(result):
    """Extract cart total from result data."""
    cart = result.get("cart", {})
    if isinstance(cart, dict):
        return cart.get("total", 0)
    return 0
