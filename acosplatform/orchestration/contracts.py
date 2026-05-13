"""Contracts for ACOS multi-agent orchestration."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class IntentResult:
    intent: str
    confidence: float
    journey_stage: str
    recommended_agent: str
    required_tools: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    needs_human: bool = False
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentDefinition:
    id: str
    name: str
    role: str
    intent_families: list[str]
    tools: list[str]
    system_prompt: str
