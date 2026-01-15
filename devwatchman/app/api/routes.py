from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from fastapi import Query

from app.collectors.processes import get_top_processes
from app.collectors.network_quality import classify_network, ping_latency_ms
from app.collectors.ports import get_port_status
from app.api.schemas import AlertsResponse, HealthResponse, HistoryResponse, NetworkResponse, PortsResponse
from app.api.schemas import ProcessesResponse
from app.api.schemas import SnapshotResponse
from app.core.config import HISTORY_DEFAULT_HOURS, NETWORK_PING_HOST, NETWORK_PING_TIMEOUT_MS, WATCH_PORTS
from app.storage.alerts import get_recent_alerts
from app.storage.db import get_connection
from app.storage.snapshots import get_latest_snapshot, get_snapshot_history

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(ok=True, data={"status": "ok"}, meta={})


@router.get("/summary")
def summary() -> SnapshotResponse:
    with get_connection() as conn:
        latest = get_latest_snapshot(conn)

    if latest is None:
        return SnapshotResponse(ok=False, data=None, meta={"message": "no snapshots yet"})

    return SnapshotResponse(ok=True, data=latest, meta={})


@router.get("/history")
def history(
    hours: int = Query(default=HISTORY_DEFAULT_HOURS, ge=1, le=168),
) -> HistoryResponse:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_ts_utc = since.isoformat()

    with get_connection() as conn:
        rows = get_snapshot_history(conn, since_ts_utc=since_ts_utc)

    return HistoryResponse(
        ok=True,
        data=rows,
        meta={"hours": hours, "since_ts_utc": since_ts_utc, "count": len(rows)},
    )


@router.get("/ports")
def ports() -> PortsResponse:
    statuses = get_port_status(WATCH_PORTS)
    return PortsResponse(ok=True, data=statuses, meta={"watch_ports": WATCH_PORTS})


@router.get("/network")
async def network() -> NetworkResponse:
    latency_ms = await asyncio.to_thread(
        ping_latency_ms, NETWORK_PING_HOST, NETWORK_PING_TIMEOUT_MS
    )
    status = classify_network(latency_ms)
    return NetworkResponse(
        ok=True,
        data={
            "host": NETWORK_PING_HOST,
            "timeout_ms": NETWORK_PING_TIMEOUT_MS,
            "latency_ms": latency_ms,
            "status": status,
        },
        meta={},
    )


@router.get("/alerts")
def alerts(limit: int = Query(default=50, ge=1, le=200)) -> AlertsResponse:
    with get_connection() as conn:
        rows = get_recent_alerts(conn, limit=limit)
    return AlertsResponse(ok=True, data=rows, meta={"limit": limit, "count": len(rows)})


@router.get("/processes")
async def processes(limit: int = Query(default=10, ge=1, le=50)) -> ProcessesResponse:
    items = await asyncio.to_thread(get_top_processes, limit)
    return ProcessesResponse(
        ok=True,
        data={"items": items},
        meta={"limit": limit, "ts_utc": datetime.now(timezone.utc).isoformat()},
    )
