from acosplatform.context.store import (
    append_context_event,
    get_context_memory,
    list_context_events,
    start_context_session,
    upsert_context_memory,
)


def test_session_and_event_fallback(monkeypatch):
    monkeypatch.setattr("acosplatform.context.store.is_pool_available", lambda: False)
    session = start_context_session(
        tenant_id="tenant-a",
        customer_id="cust-1",
        metadata={"journey": "discovery"},
    )
    append_context_event(
        session_id=session["id"],
        tenant_id="tenant-a",
        event_type="agent.step.completed",
        payload={"node": "catalog"},
    )
    events = list_context_events(session_id=session["id"])
    assert session["id"].startswith("ctx-")
    assert events
    assert events[0]["event_type"] == "agent.step.completed"


def test_memory_upsert_and_get_fallback(monkeypatch):
    monkeypatch.setattr("acosplatform.context.store.is_pool_available", lambda: False)
    upsert_context_memory(
        tenant_id="tenant-b",
        customer_id="cust-9",
        memory_key="preferred_category",
        memory_value={"value": "audio"},
        source="journey",
    )
    upsert_context_memory(
        tenant_id="tenant-b",
        customer_id="cust-9",
        memory_key="preferred_category",
        memory_value={"value": "gaming"},
        source="journey",
    )
    rows = get_context_memory(tenant_id="tenant-b", customer_id="cust-9")
    assert rows
    assert rows[0]["memory_key"] == "preferred_category"
    assert rows[0]["memory_value"]["value"] == "gaming"

