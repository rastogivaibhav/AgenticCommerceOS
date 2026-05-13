"""Tenant-routed connector runtime with contract validation and retries."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class ConnectorExecutionError(RuntimeError):
    """Raised when connector request/response contract is violated."""


@dataclass(frozen=True)
class ConnectorContract:
    """Connector request/response contract."""

    name: str
    required_request_fields: tuple[str, ...] = ()
    required_response_fields: tuple[str, ...] = ()
    required_response_any_fields: tuple[str, ...] = ()
    timeout_seconds: float = 1.5
    retries: int = 2
    backoff_seconds: float = 0.15
    allow_fallback: bool = True


@dataclass
class ConnectorResult:
    """Normalized connector runtime result."""

    data: dict[str, Any]
    source: str
    attempts: int
    degraded: bool = False
    error: str | None = None
    route: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = dict(self.data)
        payload["_connector"] = {
            "source": self.source,
            "attempts": self.attempts,
            "degraded": self.degraded,
            "error": self.error,
            "name": self.route.get("name"),
        }
        return payload


def execute_connector(
    *,
    contract: ConnectorContract,
    payload: dict[str, Any],
    tenant_config: dict[str, Any] | None,
    local_handler: Callable[[dict[str, Any]], dict[str, Any]],
) -> ConnectorResult:
    """Execute connector with tenant routing and safe local fallback."""
    _validate_request(contract, payload)
    route = _resolve_route(contract, tenant_config)
    route["name"] = contract.name

    if route["mode"] != "remote" or not route["url"]:
        local = _run_local(contract, payload, local_handler)
        return ConnectorResult(data=local, source="local", attempts=1, route=route)

    attempts = 0
    last_error: str | None = None
    max_attempts = max(int(route["retries"]) + 1, 1)
    timeout_seconds = float(route["timeout_seconds"])
    backoff_seconds = float(route["backoff_seconds"])

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        try:
            response = requests.post(
                route["url"],
                json=payload,
                headers=route.get("headers") or {},
                timeout=timeout_seconds,
            )
            if response.status_code in _RETRYABLE_STATUS_CODES and attempt < max_attempts:
                last_error = f"http_{response.status_code}"
                time.sleep(backoff_seconds * attempt)
                continue
            if response.status_code >= 400:
                raise ConnectorExecutionError(
                    f"{contract.name} returned HTTP {response.status_code}"
                )
            response_payload = response.json() if response.content else {}
            if not isinstance(response_payload, dict):
                raise ConnectorExecutionError(f"{contract.name} response must be a JSON object")
            _validate_response(contract, response_payload)
            return ConnectorResult(
                data=response_payload,
                source="remote",
                attempts=attempts,
                route=route,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            if attempt < max_attempts:
                time.sleep(backoff_seconds * attempt)
                continue
            break
        except ValueError as exc:
            # JSON decode / local validation failure on a non-retryable response.
            last_error = str(exc)
            break
        except ConnectorExecutionError as exc:
            last_error = str(exc)
            break

    if route["allow_fallback"]:
        logger.warning(
            "connector %s degraded to local fallback after %s attempts (%s)",
            contract.name,
            attempts,
            last_error,
        )
        local = _run_local(contract, payload, local_handler)
        return ConnectorResult(
            data=local,
            source="local",
            attempts=attempts,
            degraded=True,
            error=last_error,
            route=route,
        )
    raise ConnectorExecutionError(
        f"connector {contract.name} failed after {attempts} attempts: {last_error}"
    )


def _run_local(
    contract: ConnectorContract,
    payload: dict[str, Any],
    local_handler: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    response = local_handler(payload)
    if not isinstance(response, dict):
        raise ConnectorExecutionError(f"local handler for {contract.name} must return dict")
    _validate_response(contract, response)
    return response


def _validate_request(contract: ConnectorContract, payload: dict[str, Any]) -> None:
    missing = [field for field in contract.required_request_fields if field not in payload]
    if missing:
        raise ConnectorExecutionError(
            f"connector {contract.name} request missing required fields: {missing}"
        )


def _validate_response(contract: ConnectorContract, payload: dict[str, Any]) -> None:
    missing = [field for field in contract.required_response_fields if field not in payload]
    if missing:
        raise ConnectorExecutionError(
            f"connector {contract.name} response missing required fields: {missing}"
        )
    if contract.required_response_any_fields and not any(
        field in payload for field in contract.required_response_any_fields
    ):
        raise ConnectorExecutionError(
            "connector "
            f"{contract.name} response must contain at least one of "
            f"{list(contract.required_response_any_fields)}"
        )


def _resolve_route(
    contract: ConnectorContract,
    tenant_config: dict[str, Any] | None,
) -> dict[str, Any]:
    connectors = (tenant_config or {}).get("connectors") or {}
    route = connectors.get(contract.name) or {}

    mode = str(route.get("mode", "local")).lower()
    url = route.get("url") or route.get("endpoint")
    return {
        "mode": mode,
        "url": url,
        "headers": route.get("headers") or {},
        "timeout_seconds": route.get("timeout_seconds", contract.timeout_seconds),
        "retries": route.get("retries", contract.retries),
        "backoff_seconds": route.get("backoff_seconds", contract.backoff_seconds),
        "allow_fallback": route.get("allow_fallback", contract.allow_fallback),
    }
