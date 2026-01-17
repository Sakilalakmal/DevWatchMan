from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app.collectors.docker_containers import docker_available, get_container_stats, list_containers


@dataclass
class _Cache:
    lock: Lock = field(default_factory=Lock)
    status_ts: float = 0.0
    status_value: tuple[bool, str] = (False, "unknown")
    list_ts: float = 0.0
    list_value: list[dict[str, Any]] = field(default_factory=list)
    stats_ts: dict[str, float] = field(default_factory=dict)
    stats_value: dict[str, dict[str, Any]] = field(default_factory=dict)


_CACHE = _Cache()


def get_docker_status_cached(*, ttl_seconds: float = 2.0) -> tuple[bool, str]:
    now = time.monotonic()
    with _CACHE.lock:
        if (now - _CACHE.status_ts) <= ttl_seconds:
            return _CACHE.status_value

    value = docker_available()
    with _CACHE.lock:
        _CACHE.status_ts = now
        _CACHE.status_value = value
    return value


def list_containers_cached(*, include_stopped: bool, ttl_seconds: float = 2.0) -> list[dict[str, Any]]:
    now = time.monotonic()
    with _CACHE.lock:
        if (now - _CACHE.list_ts) <= ttl_seconds and _CACHE.list_value:
            return _CACHE.list_value

    items = list_containers(include_stopped=include_stopped)
    with _CACHE.lock:
        _CACHE.list_ts = now
        _CACHE.list_value = items
    return items


def get_container_stats_cached(container_id: str, *, ttl_seconds: float = 2.0) -> dict[str, Any]:
    now = time.monotonic()
    with _CACHE.lock:
        ts = _CACHE.stats_ts.get(container_id, 0.0)
        if (now - ts) <= ttl_seconds and container_id in _CACHE.stats_value:
            return _CACHE.stats_value[container_id]

    value = get_container_stats(container_id)
    with _CACHE.lock:
        _CACHE.stats_ts[container_id] = now
        _CACHE.stats_value[container_id] = value
    return value


def list_containers_with_stats(
    *, include_stopped: bool = True, limit: int = 50
) -> dict[str, Any]:
    ok, reason = get_docker_status_cached()
    if not ok:
        return {"available": False, "reason": reason, "items": []}

    items = list_containers_cached(include_stopped=include_stopped)
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    merged: list[dict[str, Any]] = []
    for c in items[:limit]:
        cid = str(c.get("id") or "")
        stats = get_container_stats_cached(cid) if cid else {}
        merged.append({**c, "stats": stats})

    return {"available": True, "reason": "ok", "items": merged}

