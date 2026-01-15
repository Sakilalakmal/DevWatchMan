from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any, Callable

from app.collectors.cpu import collect_cpu
from app.collectors.disk import collect_disk
from app.collectors.memory import collect_memory
from app.collectors.network import collect_network
from app.core.config import SNAPSHOT_INTERVAL_SECONDS
from app.storage.db import get_connection
from app.storage.snapshots import insert_snapshot

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    def __init__(self, interval_seconds: int = SNAPSHOT_INTERVAL_SECONDS) -> None:
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="snapshot-scheduler")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    def _safe_collect(
        self, name: str, func: Callable[[], dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            return func()
        except Exception:
            logger.exception("Collector failed: %s", name)
            return {}

    async def _run(self) -> None:
        while True:
            ts_utc = datetime.now(timezone.utc).isoformat()

            cpu = self._safe_collect("cpu", collect_cpu)
            mem = self._safe_collect("memory", collect_memory)
            disk = self._safe_collect("disk", collect_disk)
            net = self._safe_collect("network", collect_network)

            snapshot: dict[str, Any] = {
                "ts_utc": ts_utc,
                "cpu_percent": cpu.get("percent"),
                "mem_percent": mem.get("percent"),
                "mem_used_bytes": mem.get("used_bytes"),
                "mem_avail_bytes": mem.get("available_bytes"),
                "mem_total_bytes": mem.get("total_bytes"),
                "disk_percent": disk.get("percent"),
                "disk_used_bytes": disk.get("used_bytes"),
                "disk_free_bytes": disk.get("free_bytes"),
                "disk_total_bytes": disk.get("total_bytes"),
                "net_sent_bps": net.get("bytes_sent_per_sec"),
                "net_recv_bps": net.get("bytes_recv_per_sec"),
            }

            inserted = False
            try:
                with get_connection() as conn:
                    insert_snapshot(conn, snapshot)
                inserted = True
            except Exception:
                logger.exception("Failed to insert snapshot")

            logger.info(
                "snapshot ts=%s inserted=%s cpu=%.1f mem=%.1f disk=%.1f net_tx=%.0f net_rx=%.0f",
                ts_utc,
                inserted,
                float(snapshot.get("cpu_percent") or 0.0),
                float(snapshot.get("mem_percent") or 0.0),
                float(snapshot.get("disk_percent") or 0.0),
                float(snapshot.get("net_sent_bps") or 0.0),
                float(snapshot.get("net_recv_bps") or 0.0),
            )

            await asyncio.sleep(self._interval_seconds)

