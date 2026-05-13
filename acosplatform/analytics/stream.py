"""Analytics stream – event tracking and persistence."""

import logging
from datetime import datetime, UTC

from acosplatform.db.repository import save_event as db_save_event

logger = logging.getLogger(__name__)

_events = []


def push(event):
    """Push an analytics event to the stream and persist it.

    event should have: run_id, journey, customer_id, tenant_id
    """
    event["timestamp"] = datetime.now(UTC).isoformat()
    event["event_type"] = event.get("event_type", "journey_analytics")
    _events.append(event)

    # Persist to DB if run_id is present
    run_id = event.get("run_id")
    if run_id:
        try:
            db_save_event(run_id, event["event_type"], event)
        except Exception as e:
            logger.debug(f"Analytics event persist failed: {e}")

    return event


def get_events(limit=100):
    """Get recent analytics events."""
    return list(reversed(_events[-limit:]))


def get_events_by_type(event_type, limit=50):
    """Get events filtered by type."""
    filtered = [e for e in _events if e.get("event_type") == event_type]
    return list(reversed(filtered[-limit:]))


def get_event_counts():
    """Get counts of events by type."""
    counts = {}
    for e in _events:
        t = e.get("event_type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts
