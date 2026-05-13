from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=lambda: {"type": "object"})
