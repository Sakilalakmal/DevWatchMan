from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.storage.db import get_connection

logger = logging.getLogger(__name__)

RAW_RETENTION_HOURS: int = 24
ROLLUP_1M_DAYS: int = 7
ROLLUP_15M_DAYS: int = 30

RAW_TO_1M_LAG_MINUTES: int = 2
ONE_M_TO_15M_LAG_MINUTES: int = 20

RAW_TO_1M_MAX_SPAN_MINUTES: int = 6 * 60
ONE_M_TO_15M_MAX_SPAN_MINUTES: int = 2 * 24 * 60

APP_STATE_RAW_TO_1M_NEXT_START: str = "rollup_raw_to_1m_next_start_utc"
APP_STATE_1M_TO_15M_NEXT_START: str = "rollup_1m_to_15m_next_start_utc"


def _floor_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def _floor_15m(dt: datetime) -> datetime:
    minute = dt.minute - (dt.minute % 15)
    return dt.replace(minute=minute, second=0, microsecond=0)


def _get_app_state(conn, key: str) -> str | None:
    row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    value = str(row["value"] or "").strip()
    return value or None


def _set_app_state(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO app_state(key, value) VALUES(?, ?)",
        (key, value),
    )


def _parse_ts(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _rollup_raw_to_1m(conn, *, now_utc: datetime) -> int:
    cutoff_dt = _floor_minute(now_utc - timedelta(minutes=RAW_TO_1M_LAG_MINUTES))
    next_start_raw = _get_app_state(conn, APP_STATE_RAW_TO_1M_NEXT_START)
    if next_start_raw is None:
        start_dt = _floor_minute(now_utc - timedelta(days=ROLLUP_15M_DAYS))
    else:
        start_dt = _parse_ts(next_start_raw) or _floor_minute(now_utc - timedelta(days=ROLLUP_15M_DAYS))
        start_dt = _floor_minute(start_dt)

    if start_dt >= cutoff_dt:
        return 0

    end_dt = min(cutoff_dt, start_dt + timedelta(minutes=RAW_TO_1M_MAX_SPAN_MINUTES))
    end_dt = _floor_minute(end_dt)
    if end_dt <= start_dt:
        return 0

    start_ts = start_dt.isoformat()
    end_ts = end_dt.isoformat()

    conn.execute(
        """
        INSERT INTO snapshots_1m (
            bucket_start_utc,
            avg_cpu_percent,
            avg_mem_percent,
            avg_disk_percent,
            avg_net_sent_bps,
            avg_net_recv_bps
        )
        SELECT
            substr(ts_utc, 1, 16) || ':00+00:00' AS bucket_start_utc,
            avg(cpu_percent) AS avg_cpu_percent,
            avg(mem_percent) AS avg_mem_percent,
            avg(disk_percent) AS avg_disk_percent,
            avg(net_sent_bps) AS avg_net_sent_bps,
            avg(net_recv_bps) AS avg_net_recv_bps
        FROM snapshots
        WHERE ts_utc >= ? AND ts_utc < ?
        GROUP BY bucket_start_utc
        ON CONFLICT(bucket_start_utc) DO UPDATE SET
            avg_cpu_percent = excluded.avg_cpu_percent,
            avg_mem_percent = excluded.avg_mem_percent,
            avg_disk_percent = excluded.avg_disk_percent,
            avg_net_sent_bps = excluded.avg_net_sent_bps,
            avg_net_recv_bps = excluded.avg_net_recv_bps
        """,
        (start_ts, end_ts),
    )

    _set_app_state(conn, APP_STATE_RAW_TO_1M_NEXT_START, end_ts)
    return 1


def _rollup_1m_to_15m(conn, *, now_utc: datetime) -> int:
    cutoff_dt = _floor_15m(now_utc - timedelta(minutes=ONE_M_TO_15M_LAG_MINUTES))
    next_start_raw = _get_app_state(conn, APP_STATE_1M_TO_15M_NEXT_START)
    if next_start_raw is None:
        start_dt = _floor_15m(now_utc - timedelta(days=ROLLUP_15M_DAYS))
    else:
        start_dt = _parse_ts(next_start_raw) or _floor_15m(now_utc - timedelta(days=ROLLUP_15M_DAYS))
        start_dt = _floor_15m(start_dt)

    if start_dt >= cutoff_dt:
        return 0

    end_dt = min(cutoff_dt, start_dt + timedelta(minutes=ONE_M_TO_15M_MAX_SPAN_MINUTES))
    end_dt = _floor_15m(end_dt)
    if end_dt <= start_dt:
        return 0

    start_ts = start_dt.isoformat()
    end_ts = end_dt.isoformat()

    conn.execute(
        """
        INSERT INTO snapshots_15m (
            bucket_start_utc,
            avg_cpu_percent,
            avg_mem_percent,
            avg_disk_percent,
            avg_net_sent_bps,
            avg_net_recv_bps
        )
        SELECT
            substr(bucket_start_utc, 1, 14)
                || printf(
                    '%02d',
                    CAST(CAST(substr(bucket_start_utc, 15, 2) AS INTEGER) / 15 AS INTEGER) * 15
                )
                || ':00+00:00' AS bucket_start_utc,
            avg(avg_cpu_percent) AS avg_cpu_percent,
            avg(avg_mem_percent) AS avg_mem_percent,
            avg(avg_disk_percent) AS avg_disk_percent,
            avg(avg_net_sent_bps) AS avg_net_sent_bps,
            avg(avg_net_recv_bps) AS avg_net_recv_bps
        FROM snapshots_1m
        WHERE bucket_start_utc >= ? AND bucket_start_utc < ?
        GROUP BY bucket_start_utc
        ON CONFLICT(bucket_start_utc) DO UPDATE SET
            avg_cpu_percent = excluded.avg_cpu_percent,
            avg_mem_percent = excluded.avg_mem_percent,
            avg_disk_percent = excluded.avg_disk_percent,
            avg_net_sent_bps = excluded.avg_net_sent_bps,
            avg_net_recv_bps = excluded.avg_net_recv_bps
        """,
        (start_ts, end_ts),
    )

    _set_app_state(conn, APP_STATE_1M_TO_15M_NEXT_START, end_ts)
    return 1


def _apply_retention(conn, *, now_utc: datetime) -> None:
    raw_cutoff = (now_utc - timedelta(hours=RAW_RETENTION_HOURS)).isoformat()
    one_m_cutoff = (now_utc - timedelta(days=ROLLUP_1M_DAYS)).isoformat()
    fifteen_m_cutoff = (now_utc - timedelta(days=ROLLUP_15M_DAYS)).isoformat()

    raw_cursor = _parse_ts(_get_app_state(conn, APP_STATE_RAW_TO_1M_NEXT_START) or "")
    safe_raw_cutoff = raw_cutoff
    if raw_cursor is not None:
        safe_raw_cutoff = min(raw_cutoff, raw_cursor.isoformat())

    one_m_cursor = _parse_ts(_get_app_state(conn, APP_STATE_1M_TO_15M_NEXT_START) or "")
    safe_one_m_cutoff = one_m_cutoff
    if one_m_cursor is not None:
        safe_one_m_cutoff = min(one_m_cutoff, one_m_cursor.isoformat())

    conn.execute("DELETE FROM snapshots WHERE ts_utc < ?", (safe_raw_cutoff,))
    conn.execute(
        "DELETE FROM snapshots_1m WHERE bucket_start_utc < ?",
        (safe_one_m_cutoff,),
    )
    conn.execute("DELETE FROM snapshots_15m WHERE bucket_start_utc < ?", (fifteen_m_cutoff,))


@dataclass
class RetentionService:
    interval_seconds: int = 60
    _task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="retention-service")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        while True:
            now_utc = datetime.now(timezone.utc)
            try:
                with get_connection() as conn:
                    try:
                        conn.execute("BEGIN")
                        progressed = 0
                        progressed += _rollup_raw_to_1m(conn, now_utc=now_utc)
                        progressed += _rollup_1m_to_15m(conn, now_utc=now_utc)
                        _apply_retention(conn, now_utc=now_utc)
                        conn.commit()
                        if progressed:
                            logger.debug("Retention progressed steps=%s", progressed)
                    except Exception:
                        with suppress(Exception):
                            conn.rollback()
                        raise
            except Exception:
                logger.exception("Retention cycle failed")

            await asyncio.sleep(float(self.interval_seconds))
