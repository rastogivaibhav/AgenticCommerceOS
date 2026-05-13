"""Conversation and journey spine for omnichannel retail interactions."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import EvidenceEvent, record_evidence
from acosplatform.northstar import repository as northstar_repository
from acosplatform.events.outbox import publish_event
from acosplatform.cache.redis_cache import get_json as cache_get_json, set_json as cache_set_json


@dataclass(slots=True)
class ConversationSession:
    id: str
    tenant_id: str
    customer_id: str
    primary_channel: str
    channel_identities: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(slots=True)
class Journey:
    id: str
    tenant_id: str
    customer_id: str
    conversation_session_id: str
    stage: str = "intake"
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


_LOCK = RLock()
_SESSIONS: dict[str, ConversationSession] = {}
_JOURNEYS: dict[str, Journey] = {}
_MESSAGES: list[dict[str, Any]] = []
_IDENTITY_INDEX: dict[str, str] = {}


def _identity_key(tenant_id: str, channel: str, channel_user_id: str) -> str:
    return f"{tenant_id}:{channel}:{channel_user_id}"


def resolve_or_create_session(envelope: MessageEnvelope) -> MessageEnvelope:
    customer_id = envelope.customer_id or f"anon_{envelope.channel}_{envelope.channel_user_id}".replace("+", "")
    key = _identity_key(envelope.tenant_id, envelope.channel, envelope.channel_user_id)
    now = datetime.now(UTC).isoformat()
    with _LOCK:
        session_id = envelope.conversation_session_id or _IDENTITY_INDEX.get(key)
        persisted_session = None
        if not session_id:
            persisted_session = northstar_repository.find_session_by_identity(envelope.tenant_id, envelope.channel, envelope.channel_user_id)
            session_id = persisted_session["id"] if persisted_session else None
        if not session_id:
            session_id = f"sess_{uuid4().hex[:12]}"
            _IDENTITY_INDEX[key] = session_id
            session = ConversationSession(
                id=session_id,
                tenant_id=envelope.tenant_id,
                customer_id=customer_id,
                primary_channel=envelope.channel,
                channel_identities={envelope.channel: envelope.channel_user_id},
                created_at=now,
                updated_at=now,
            )
            _SESSIONS[session_id] = session
        else:
            session = _SESSIONS.get(session_id)
            if not session and persisted_session:
                session = ConversationSession(
                    id=persisted_session["id"],
                    tenant_id=persisted_session["tenant_id"],
                    customer_id=persisted_session["customer_id"],
                    primary_channel=persisted_session["primary_channel"],
                    channel_identities=dict(persisted_session.get("channel_identities") or {}),
                    created_at=persisted_session["created_at"],
                    updated_at=persisted_session["updated_at"],
                )
                _SESSIONS[session_id] = session
            elif not session:
                existing = northstar_repository.get_session(session_id)
                if existing:
                    session = ConversationSession(
                        id=existing["id"], tenant_id=existing["tenant_id"], customer_id=existing["customer_id"],
                        primary_channel=existing["primary_channel"], channel_identities=dict(existing.get("channel_identities") or {}),
                        created_at=existing["created_at"], updated_at=existing["updated_at"],
                    )
                    _SESSIONS[session_id] = session
            if not session:
                session = ConversationSession(
                    id=session_id, tenant_id=envelope.tenant_id, customer_id=customer_id, primary_channel=envelope.channel,
                    channel_identities={envelope.channel: envelope.channel_user_id}, created_at=now, updated_at=now,
                )
                _SESSIONS[session_id] = session
            session.channel_identities[envelope.channel] = envelope.channel_user_id
            session.updated_at = now
            _IDENTITY_INDEX[key] = session_id
        northstar_repository.upsert_session(asdict(session))
        try:
            cache_set_json(f"northstar:session:{session.id}", asdict(session), ttl_seconds=900)
        except Exception:
            pass
        active = northstar_repository.get_active_journey_for_session(session_id)
        journey_id = envelope.journey_id or (active["id"] if active else None) or next(
            (j.id for j in _JOURNEYS.values() if j.conversation_session_id == session_id and j.status == "active"),
            None,
        )
        if not journey_id:
            journey_id = f"journey_{uuid4().hex[:12]}"
            journey = Journey(
                id=journey_id,
                tenant_id=envelope.tenant_id,
                customer_id=customer_id,
                conversation_session_id=session_id,
                created_at=now,
                updated_at=now,
            )
            _JOURNEYS[journey_id] = journey
            northstar_repository.upsert_journey(asdict(journey))
            try:
                cache_set_json(f"northstar:journey:{journey.id}", asdict(journey), ttl_seconds=900)
            except Exception:
                pass
        envelope.customer_id = customer_id
        envelope.conversation_session_id = session_id
        envelope.journey_id = journey_id
        payload = envelope.to_dict()
        _MESSAGES.append(payload)
        northstar_repository.save_message(payload)
    try:
        publish_event("message.received", envelope.to_dict(), tenant_id=envelope.tenant_id, aggregate_id=envelope.conversation_session_id, idempotency_key=envelope.message_id)
    except Exception:
        pass
    record_evidence(EvidenceEvent(
        event_type="message.received",
        tenant_id=envelope.tenant_id,
        correlation_id=envelope.correlation_id,
        conversation_session_id=envelope.conversation_session_id,
        journey_id=envelope.journey_id,
        payload={"channel": envelope.channel, "message_id": envelope.message_id},
    ))
    return envelope

def get_session(session_id: str) -> dict[str, Any] | None:
    try:
        cached = cache_get_json(f"northstar:session:{session_id}")
        if isinstance(cached, dict):
            return cached
    except Exception:
        pass
    with _LOCK:
        session = _SESSIONS.get(session_id)
        if session:
            return asdict(session)
    return northstar_repository.get_session(session_id)


def get_journey(journey_id: str) -> dict[str, Any] | None:
    try:
        cached = cache_get_json(f"northstar:journey:{journey_id}")
        if isinstance(cached, dict):
            return cached
    except Exception:
        pass
    with _LOCK:
        journey = _JOURNEYS.get(journey_id)
        if journey:
            return asdict(journey)
    return northstar_repository.get_journey(journey_id)


def list_messages(*, conversation_session_id: str | None = None) -> list[dict[str, Any]]:
    persisted = northstar_repository.list_messages(conversation_session_id=conversation_session_id)
    if persisted:
        return persisted
    with _LOCK:
        messages = list(_MESSAGES)
    if conversation_session_id:
        messages = [m for m in messages if m.get("conversation_session_id") == conversation_session_id]
    return messages
