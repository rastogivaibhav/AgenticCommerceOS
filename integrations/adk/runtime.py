"""Standardized ADK runtime with tool-contract enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class ToolContractError(ValueError):
    """Raised when a tool invocation violates its declared contract."""


@dataclass(frozen=True)
class ToolContract:
    name: str
    input_required: tuple[str, ...] = ()
    output_required: tuple[str, ...] = ()
    output_types: dict[str, type | tuple[type, ...]] = field(default_factory=dict)


@dataclass
class RuntimeTool:
    name: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    contract: ToolContract


class ADKRuntime:
    """Small runtime abstraction for deterministic tool execution."""

    def __init__(
        self,
        *,
        journey_type: str,
        provider: str,
        contract_version: str = "v1",
        model_name: str | None = None,
    ):
        self.journey_type = journey_type
        self.provider = provider
        self.contract_version = contract_version
        self.model_name = model_name
        self._tools: dict[str, RuntimeTool] = {}
        self.trace: list[dict[str, Any]] = []

    def register_tool(self, tool: RuntimeTool) -> None:
        self._tools[tool.name] = tool

    def _validate_input(self, contract: ToolContract, payload: dict[str, Any]) -> None:
        missing = [key for key in contract.input_required if key not in payload]
        if missing:
            raise ToolContractError(
                f"{contract.name}: missing required input fields: {', '.join(missing)}"
            )

    def _validate_output(self, contract: ToolContract, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ToolContractError(f"{contract.name}: tool output must be an object")

        missing = [key for key in contract.output_required if key not in payload]
        if missing:
            raise ToolContractError(
                f"{contract.name}: missing required output fields: {', '.join(missing)}"
            )

        for field_name, expected_type in contract.output_types.items():
            if field_name not in payload:
                continue
            if not isinstance(payload[field_name], expected_type):
                raise ToolContractError(
                    f"{contract.name}: output field '{field_name}' has invalid type"
                )

    def call_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise ToolContractError(f"Unknown tool '{name}'")
        tool = self._tools[name]

        self._validate_input(tool.contract, payload)
        output = tool.handler(payload)
        self._validate_output(tool.contract, output)
        self.trace.append({"tool": name, "status": "ok"})
        return output

    def run_pipeline(self, tool_names: list[str], payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        results: dict[str, Any] = {}
        used: list[str] = []
        for name in tool_names:
            results[name] = self.call_tool(name, payload)
            used.append(name)
        return results, used

    def metadata(self) -> dict[str, Any]:
        return {
            "engine": "standardized-adk-runtime",
            "journey_type": self.journey_type,
            "provider": self.provider,
            "model_name": self.model_name,
            "contract_version": self.contract_version,
            "trace": list(self.trace),
        }
