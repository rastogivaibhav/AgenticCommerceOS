"""Structured audit logging — GDPR-compliant event records for all data access. (FIX-10)"""

import json
import logging
import uuid
from datetime import datetime, UTC

_audit = logging.getLogger("acos.audit")

# Ensure audit logs always go to stdout even if root logger is misconfigured
if not _audit.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _audit.addHandler(_handler)
    _audit.setLevel(logging.INFO)
    _audit.propagate = False


def audit(
    event_type: str,
    actor: str,
    resource: str,
    outcome: str = "success",
    **kwargs,
) -> None:
    """
    Emit a structured audit log entry.

    Args:
        event_type: e.g. 'journey_executed', 'run_accessed', 'replay_triggered'
        actor:      customer_id or ops user identifier
        resource:   what was accessed (e.g. '/runs', 'run-abc123')
        outcome:    'success', 'denied', 'error'
        **kwargs:   additional context (journey_type, tenant_id, etc.)
    """
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "actor": actor,
        "resource": resource,
        "outcome": outcome,
        **kwargs,
    }
    _audit.info(json.dumps(entry))
