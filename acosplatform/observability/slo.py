"""In-memory SLO snapshots for baseline dashboards."""

from __future__ import annotations

import math
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

_OBSERVATIONS: deque[dict[str, Any]] = deque(maxlen=10000)


def record_journey_observation(
    *,
    tenant_id: str,
    journey: str,
    run_id: str,
    duration_ms: float,
    success: bool,
    cost: float = 0.0,
) -> None:
    _OBSERVATIONS.append(
        {
            "timestamp": datetime.now(UTC),
            "tenant_id": tenant_id,
            "journey": journey,
            "run_id": run_id,
            "duration_ms": max(duration_ms, 0),
            "success": bool(success),
            "cost": max(cost, 0),
        }
    )


def get_slo_snapshot(window_minutes: int = 60, tenant_id: str | None = None) -> dict[str, Any]:
    window_start = datetime.now(UTC) - timedelta(minutes=max(window_minutes, 1))
    data = [item for item in _OBSERVATIONS if item["timestamp"] >= window_start]
    if tenant_id:
        data = [item for item in data if item["tenant_id"] == tenant_id]

    total = len(data)
    successes = sum(1 for item in data if item["success"])
    errors = total - successes
    latencies = sorted(item["duration_ms"] for item in data)
    costs = [item["cost"] for item in data]

    by_journey = {}
    for item in data:
        journey = item["journey"]
        entry = by_journey.setdefault(journey, {"total": 0, "success": 0, "errors": 0})
        entry["total"] += 1
        if item["success"]:
            entry["success"] += 1
        else:
            entry["errors"] += 1

    return {
        "window_minutes": window_minutes,
        "tenant_id": tenant_id,
        "total_runs": total,
        "successful_runs": successes,
        "failed_runs": errors,
        "availability_pct": _pct(successes, total),
        "error_rate_pct": _pct(errors, total),
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
        },
        "avg_cost_usd": round((sum(costs) / len(costs)), 6) if costs else 0.0,
        "journeys": by_journey,
        "captured_at": datetime.now(UTC).isoformat(),
    }


def _percentile(sorted_values: list[float], percentile: int) -> float:
    if not sorted_values:
        return 0.0
    if percentile <= 0:
        return float(sorted_values[0])
    if percentile >= 100:
        return float(sorted_values[-1])
    idx = math.ceil((percentile / 100) * len(sorted_values)) - 1
    idx = max(0, min(idx, len(sorted_values) - 1))
    return float(sorted_values[idx])


def _pct(part: int, total: int) -> float:
    return round((part / total) * 100, 4) if total else 100.0
