"""Tenant-scoped traffic controls for Week-10 baseline protections."""

from __future__ import annotations

import os
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Callable

from acosplatform.tenancy.manager import get_tenant_config


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 1)


def _coerce_positive_int(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 1)


@dataclass(frozen=True)
class TenantTrafficLimits:
    requests_per_minute: int
    daily_quota: int
    max_in_flight: int


class TenantQuotaExceeded(RuntimeError):
    """Raised when a tenant exceeds configured traffic protections."""

    def __init__(
        self,
        *,
        tenant_id: str,
        limit_type: str,
        limit_value: int,
        retry_after_seconds: int,
    ) -> None:
        self.tenant_id = tenant_id
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.retry_after_seconds = max(int(retry_after_seconds), 1)
        super().__init__(f"{tenant_id} exceeded {limit_type} limit ({limit_value})")


class TenantTrafficController:
    """In-memory enforcement for per-tenant request rate, quota, and concurrency."""

    def __init__(self, now_fn: Callable[[], datetime] | None = None) -> None:
        self._now_fn = now_fn or (lambda: datetime.now(UTC))
        self._lock = Lock()
        self._window_events: dict[str, deque[datetime]] = defaultdict(deque)
        self._daily_counts: dict[str, dict[str, int | str]] = {}
        self._in_flight: dict[str, int] = defaultdict(int)

    def acquire(self, tenant_id: str, limits: TenantTrafficLimits) -> None:
        tenant = tenant_id or "default"
        now = self._now_fn()
        window_seconds = 60

        with self._lock:
            events = self._window_events[tenant]
            cutoff = now.timestamp() - window_seconds
            while events and events[0].timestamp() < cutoff:
                events.popleft()

            if len(events) >= limits.requests_per_minute:
                oldest = events[0] if events else now
                retry_after = int(max(window_seconds - (now.timestamp() - oldest.timestamp()), 1))
                raise TenantQuotaExceeded(
                    tenant_id=tenant,
                    limit_type="rate_limit",
                    limit_value=limits.requests_per_minute,
                    retry_after_seconds=retry_after,
                )

            day = now.date().isoformat()
            daily = self._daily_counts.get(tenant)
            if not daily or daily.get("day") != day:
                daily = {"day": day, "count": 0}
                self._daily_counts[tenant] = daily

            if int(daily["count"]) >= limits.daily_quota:
                next_day = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
                midnight_retry = max(int((next_day - now).total_seconds()), 1)
                raise TenantQuotaExceeded(
                    tenant_id=tenant,
                    limit_type="daily_quota",
                    limit_value=limits.daily_quota,
                    retry_after_seconds=midnight_retry,
                )

            if self._in_flight[tenant] >= limits.max_in_flight:
                raise TenantQuotaExceeded(
                    tenant_id=tenant,
                    limit_type="in_flight_limit",
                    limit_value=limits.max_in_flight,
                    retry_after_seconds=1,
                )

            events.append(now)
            daily["count"] = int(daily["count"]) + 1
            self._in_flight[tenant] += 1

    def release(self, tenant_id: str) -> None:
        tenant = tenant_id or "default"
        with self._lock:
            current = self._in_flight.get(tenant, 0)
            if current <= 1:
                self._in_flight.pop(tenant, None)
            else:
                self._in_flight[tenant] = current - 1

    def reset(self) -> None:
        with self._lock:
            self._window_events.clear()
            self._daily_counts.clear()
            self._in_flight.clear()

    def snapshot(self, tenant_id: str) -> dict[str, int | str]:
        tenant = tenant_id or "default"
        now = self._now_fn()
        with self._lock:
            events = self._window_events.get(tenant, deque())
            cutoff = now.timestamp() - 60
            recent = [e for e in events if e.timestamp() >= cutoff]
            daily = self._daily_counts.get(tenant, {"day": now.date().isoformat(), "count": 0})
            return {
                "tenant_id": tenant,
                "requests_last_minute": len(recent),
                "daily_count": int(daily.get("count", 0)),
                "in_flight": int(self._in_flight.get(tenant, 0)),
            }


tenant_traffic_controller = TenantTrafficController()


def resolve_tenant_limits(tenant_id: str) -> TenantTrafficLimits:
    defaults = TenantTrafficLimits(
        requests_per_minute=_env_int("TENANT_RATE_LIMIT_PER_MINUTE", 120),
        daily_quota=_env_int("TENANT_DAILY_QUOTA", 5000),
        max_in_flight=_env_int("TENANT_MAX_IN_FLIGHT", 8),
    )
    try:
        config = get_tenant_config(tenant_id or "default")
    except Exception:
        return defaults

    controls = (config or {}).get("traffic_controls") or {}
    return TenantTrafficLimits(
        requests_per_minute=_coerce_positive_int(
            controls.get("requests_per_minute"),
            defaults.requests_per_minute,
        ),
        daily_quota=_coerce_positive_int(
            controls.get("daily_quota"),
            defaults.daily_quota,
        ),
        max_in_flight=_coerce_positive_int(
            controls.get("max_in_flight"),
            defaults.max_in_flight,
        ),
    )


@contextmanager
def tenant_traffic_guard(tenant_id: str):
    tenant = tenant_id or "default"
    limits = resolve_tenant_limits(tenant)
    tenant_traffic_controller.acquire(tenant, limits)
    try:
        yield limits
    finally:
        tenant_traffic_controller.release(tenant)


def reset_tenant_traffic_state() -> None:
    tenant_traffic_controller.reset()
