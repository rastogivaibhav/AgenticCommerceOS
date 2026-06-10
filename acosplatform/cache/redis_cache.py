"""Optional Redis hot-cache for north-star sessions and Studio proof payloads."""
from __future__ import annotations

import json
import os
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional fast path
    redis = None  # type: ignore


def enabled() -> bool:
    return os.environ.get("ACOS_REDIS_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}


def _client() -> Any | None:
    if not enabled() or redis is None:
        return None
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def get_json(key: str) -> dict[str, Any] | list[Any] | None:
    client = _client()
    if client is None:
        return None
    raw = client.get(key)
    return json.loads(raw) if raw else None


def set_json(key: str, value: dict[str, Any] | list[Any], *, ttl_seconds: int = 300) -> None:
    client = _client()
    if client is None:
        return
    client.setex(key, ttl_seconds, json.dumps(value, sort_keys=True, default=str))


def delete(key: str) -> None:
    client = _client()
    if client is not None:
        client.delete(key)
