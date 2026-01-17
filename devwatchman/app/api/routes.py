from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi import Query

from app.collectors.processes import get_top_processes
from app.collectors.network_quality import classify_network, ping_latency_ms
from app.collectors.ports import get_port_status
from app.collectors.listening_ports import get_listening_ports
from app.api.schemas import AlertAckResponse, AlertsResponse, HealthResponse, HistoryResponse, ListeningPortsResponse, MuteStatusResponse, NetworkResponse, PortsResponse
from app.api.schemas import ProcessesResponse
from app.api.schemas import SnapshotResponse
from app.api.schemas import TimelineResponse
from app.core.config import HISTORY_DEFAULT_HOURS, NETWORK_PING_HOST, NETWORK_PING_TIMEOUT_MS, WATCH_PORTS
from app.services.alert_state import AlertState
from app.storage.alerts import acknowledge_alert, get_recent_alerts, set_alert_setting
from app.storage.db import get_connection
from app.storage.events import get_events, get_latest_events, insert_event
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


@router.get("/timeline")
def timeline(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=500),
) -> TimelineResponse:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    since_ts_utc = since.isoformat()

    with get_connection() as conn:
        items = get_events(conn, since_ts_utc=since_ts_utc, limit=limit)

    return TimelineResponse(
        ok=True,
        data={"items": items},
        meta={"hours": hours, "limit": limit, "ts_utc": now.isoformat()},
    )


@router.get("/timeline/latest")
def timeline_latest(
    limit: int = Query(default=30, ge=1, le=500),
) -> TimelineResponse:
    now = datetime.now(timezone.utc)
    with get_connection() as conn:
        items = get_latest_events(conn, limit=limit)

    return TimelineResponse(
        ok=True,
        data={"items": items},
        meta={"hours": None, "limit": limit, "ts_utc": now.isoformat()},
    )


@router.get("/ports")
def ports() -> PortsResponse:
    statuses = get_port_status(WATCH_PORTS)
    return PortsResponse(ok=True, data=statuses, meta={"watch_ports": WATCH_PORTS})


@router.get("/ports/listening")
async def listening_ports(
    limit: int = Query(default=500, ge=1, le=2000),
) -> ListeningPortsResponse:
    now = datetime.now(timezone.utc)
    items = await asyncio.to_thread(get_listening_ports, limit)
    return ListeningPortsResponse(
        ok=True,
        data={"items": items},
        meta={"limit": limit, "count": len(items), "ts_utc": now.isoformat()},
    )


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
def alerts(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    include_ack: bool = Query(default=False),
) -> AlertsResponse:
    with get_connection() as conn:
        rows = get_recent_alerts(conn, limit=limit, include_ack=include_ack)

    mute_until: str | None = None
    state: AlertState | None = getattr(request.app.state, "alert_state", None)
    if state and state.mute_until_utc:
        mute_until = state.mute_until_utc.isoformat()

    return AlertsResponse(
        ok=True,
        data=rows,
        meta={
            "limit": limit,
            "count": len(rows),
            "include_ack": include_ack,
            "mute_until_utc": mute_until,
        },
    )


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int, request: Request) -> AlertAckResponse:
    ts_utc = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        ok = acknowledge_alert(conn, alert_id=alert_id, ts_utc=ts_utc)
        event_id: int | None = None
        if ok:
            try:
                event_id = insert_event(
                    conn,
                    {
                        "ts_utc": ts_utc,
                        "kind": "alert_ack",
                        "message": f"Alert {alert_id} acknowledged",
                        "severity": "info",
                        "meta": {"alert_id": alert_id},
                    },
                )
            except Exception:
                event_id = None

    if not ok:
        return AlertAckResponse(ok=False, data=None, meta={"message": "alert not found"})

    manager = getattr(request.app.state, "ws_manager", None)
    if manager is not None:
        try:
            await manager.broadcast_json(
                {"type": "alert_state", "v": 1, "ts_utc": ts_utc, "data": {"id": alert_id, "acknowledged": True}}
            )
            if event_id is not None:
                await manager.broadcast_json(
                    {
                        "type": "timeline_event",
                        "v": 1,
                        "ts_utc": ts_utc,
                        "data": {
                            "id": event_id,
                            "kind": "alert_ack",
                            "severity": "info",
                            "message": f"Alert {alert_id} acknowledged",
                        },
                    }
                )
        except Exception:
            pass

    return AlertAckResponse(ok=True, data={"id": alert_id, "acknowledged": True, "acknowledged_ts_utc": ts_utc}, meta={})


@router.post("/alerts/mute")
async def mute_alerts(
    request: Request,
    minutes: int = Query(default=30, ge=0, le=24 * 60),
) -> MuteStatusResponse:
    now = datetime.now(timezone.utc)
    mute_until = (now + timedelta(minutes=minutes)) if minutes > 0 else None

    state: AlertState = request.app.state.alert_state
    async with state.lock:
        state.mute_until_utc = mute_until

    with get_connection() as conn:
        set_alert_setting(conn, "mute_until_utc", mute_until.isoformat() if mute_until else None)
        kind = "mute_enabled" if mute_until else "mute_disabled"
        message = (
            f"Alerts muted for {minutes} minutes"
            if mute_until
            else "Alerts unmuted"
        )
        event_id: int | None = None
        try:
            event_id = insert_event(
                conn,
                {
                    "ts_utc": now.isoformat(),
                    "kind": kind,
                    "message": message,
                    "severity": "info",
                    "meta": {"minutes": minutes, "mute_until_utc": mute_until.isoformat() if mute_until else None},
                },
            )
        except Exception:
            event_id = None

    ts_utc = now.isoformat()
    manager = getattr(request.app.state, "ws_manager", None)
    if manager is not None:
        try:
            await manager.broadcast_json(
                {
                    "type": "alert_state",
                    "v": 1,
                    "ts_utc": ts_utc,
                    "data": {"mute_until_utc": mute_until.isoformat() if mute_until else None},
                }
            )
            if event_id is not None:
                await manager.broadcast_json(
                    {
                        "type": "timeline_event",
                        "v": 1,
                        "ts_utc": ts_utc,
                        "data": {"id": event_id, "kind": kind, "severity": "info", "message": message},
                    }
                )
        except Exception:
            pass

    return MuteStatusResponse(
        ok=True,
        data={"muted": bool(mute_until and mute_until > now), "mute_until_utc": mute_until.isoformat() if mute_until else None},
        meta={"minutes": minutes},
    )


@router.get("/processes")
async def processes(limit: int = Query(default=10, ge=1, le=50)) -> ProcessesResponse:
    items = await asyncio.to_thread(get_top_processes, limit)
    return ProcessesResponse(
        ok=True,
        data={"items": items},
        meta={"limit": limit, "ts_utc": datetime.now(timezone.utc).isoformat()},
    )
