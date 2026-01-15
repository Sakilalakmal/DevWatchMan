from __future__ import annotations

import asyncio
import logging
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any, Callable

from app.collectors.cpu import collect_cpu
from app.collectors.disk import collect_disk
from app.collectors.memory import collect_memory
from app.collectors.network import collect_network
from app.collectors.network_quality import classify_network, ping_latency_ms
from app.collectors.ports import get_port_status
from app.core.config import ALERT_COOLDOWN_SECONDS
from app.core.config import ALERT_CPU_PERCENT
from app.core.config import ALERT_PORTS_REQUIRED
from app.core.config import ALERT_RAM_PERCENT
from app.core.config import NETWORK_PING_HOST
from app.core.config import NETWORK_PING_TIMEOUT_MS
from app.core.config import SNAPSHOT_INTERVAL_SECONDS
from app.storage.db import get_connection
from app.storage.alerts import insert_alert
from app.storage.snapshots import insert_snapshot

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    def __init__(self, interval_seconds: int = SNAPSHOT_INTERVAL_SECONDS) -> None:
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._last_alert_sent: dict[str, float] = {}

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

    def _safe_collect(self, name: str, func: Callable[[], Any]) -> Any:
        try:
            return func()
        except Exception:
            logger.exception("Collector failed: %s", name)
            return None

    def _should_send_alert(self, alert_type: str, now_monotonic: float) -> bool:
        last = self._last_alert_sent.get(alert_type)
        if last is not None and (now_monotonic - last) < ALERT_COOLDOWN_SECONDS:
            return False
        self._last_alert_sent[alert_type] = now_monotonic
        return True

    def _emit_alert(
        self, ts_utc: str, now_monotonic: float, *, type: str, message: str, severity: str
    ) -> bool:
        if not self._should_send_alert(type, now_monotonic):
            return False
        try:
            with get_connection() as conn:
                insert_alert(
                    conn,
                    {"ts_utc": ts_utc, "type": type, "message": message, "severity": severity},
                )
            return True
        except Exception:
            logger.exception("Failed to insert alert type=%s", type)
            return False

    async def _run(self) -> None:
        while True:
            ts_utc = datetime.now(timezone.utc).isoformat()
            now_mono = time.monotonic()

            cpu = self._safe_collect("cpu", collect_cpu) or {}
            mem = self._safe_collect("memory", collect_memory) or {}
            disk = self._safe_collect("disk", collect_disk) or {}
            net = self._safe_collect("network", collect_network) or {}

            ports_required = self._safe_collect(
                "ports_required", lambda: get_port_status(ALERT_PORTS_REQUIRED)
            ) or []
            latency_ms = await asyncio.to_thread(
                ping_latency_ms, NETWORK_PING_HOST, NETWORK_PING_TIMEOUT_MS
            )
            net_quality = classify_network(latency_ms)

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

            alerts_inserted = 0

            cpu_percent = float(snapshot.get("cpu_percent") or 0.0)
            if cpu_percent >= ALERT_CPU_PERCENT:
                alerts_inserted += int(
                    self._emit_alert(
                        ts_utc,
                        now_mono,
                        type="cpu_high",
                        message=f"CPU usage high: {cpu_percent:.1f}%",
                        severity="warning",
                    )
                )

            mem_percent = float(snapshot.get("mem_percent") or 0.0)
            if mem_percent >= ALERT_RAM_PERCENT:
                alerts_inserted += int(
                    self._emit_alert(
                        ts_utc,
                        now_mono,
                        type="ram_high",
                        message=f"RAM usage high: {mem_percent:.1f}%",
                        severity="warning",
                    )
                )

            down_ports = [
                int(p["port"])
                for p in ports_required
                if isinstance(p, dict) and (not bool(p.get("listening")))
            ]
            if down_ports:
                alerts_inserted += int(
                    self._emit_alert(
                        ts_utc,
                        now_mono,
                        type="port_down",
                        message=f"Required port(s) down: {', '.join(map(str, down_ports))}",
                        severity="critical",
                    )
                )

            if net_quality in {"offline", "poor"}:
                severity = "critical" if net_quality == "offline" else "warning"
                latency_str = "N/A" if latency_ms is None else f"{latency_ms:.0f}ms"
                alerts_inserted += int(
                    self._emit_alert(
                        ts_utc,
                        now_mono,
                        type="network_poor",
                        message=f"Network {net_quality} (ping {NETWORK_PING_HOST} latency {latency_str})",
                        severity=severity,
                    )
                )

            logger.info(
                "snapshot ts=%s inserted=%s alerts=%d cpu=%.1f mem=%.1f disk=%.1f net_tx=%.0f net_rx=%.0f net_q=%s",
                ts_utc,
                inserted,
                alerts_inserted,
                float(snapshot.get("cpu_percent") or 0.0),
                float(snapshot.get("mem_percent") or 0.0),
                float(snapshot.get("disk_percent") or 0.0),
                float(snapshot.get("net_sent_bps") or 0.0),
                float(snapshot.get("net_recv_bps") or 0.0),
                net_quality,
            )

            await asyncio.sleep(self._interval_seconds)
