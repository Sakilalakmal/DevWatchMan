from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from fastapi import Query

from app.api.schemas import HealthResponse, HistoryResponse, SnapshotResponse
from app.core.config import HISTORY_DEFAULT_HOURS
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
