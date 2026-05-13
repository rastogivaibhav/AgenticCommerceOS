from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class A2AInvocationRequest:
    message: str
    tenant_id: str = 'default'
    customer_id: str = 'demo-customer'
    channel: str = 'web'
    actor_type: str = 'customer'
    channel_mode: str = 'customer_direct'
    vendor_agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class A2ATask:
    task_id: str
    trace_id: str
    agent_id: str
    capability_id: str
    status: str
    request: dict[str, Any]
    response: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self): return asdict(self)
