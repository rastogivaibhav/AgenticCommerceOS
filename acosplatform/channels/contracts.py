"""Canonical omnichannel message contracts for ACOS."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class MessageEnvelope:
    tenant_id: str
    channel: str
    channel_user_id: str
    text: str
    customer_id: str | None = None
    conversation_session_id: str | None = None
    journey_id: str | None = None
    message_id: str = field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    correlation_id: str = field(default_factory=lambda: f"corr_{uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
