from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
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
from app.core.config import ALERT_CPU_DURATION_SECONDS
from app.core.config import ALERT_PORTS_REQUIRED
from app.core.config import ALERT_RAM_PERCENT
from app.core.config import ALERT_RAM_DURATION_SECONDS
from app.core.config import ALERT_NET_OFFLINE_SECONDS
from app.core.config import FLAP_THRESHOLD, FLAP_WINDOW_SECONDS
from app.core.config import NETWORK_PING_HOST
from app.core.config import NETWORK_PING_TIMEOUT_MS
from app.core.config import SNAPSHOT_INTERVAL_SECONDS
from app.storage.db import get_connection
from app.storage.alerts import insert_alert
from app.storage.snapshots import insert_snapshot
from app.services.alert_state import AlertState
from app.services.ws_manager import WebSocketManager

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    def __init__(
        self,
        interval_seconds: int = SNAPSHOT_INTERVAL_SECONDS,
        *,
        ws_manager: WebSocketManager | None = None,
        alert_state: AlertState | None = None,
    ) -> None:
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._last_alert_sent: dict[tuple[str, str], float] = {}
        self._ws_manager = ws_manager
        self._alert_state = alert_state
        self._last_processes_broadcast_mono: float = 0.0
        self._cpu_high_since_mono: float | None = None
        self._cpu_high_fired: bool = False
        self._ram_high_since_mono: float | None = None
        self._ram_high_fired: bool = False
        self._net_offline_since_mono: float | None = None
        self._net_offline_fired: bool = False
        self._net_poor_fired: bool = False
        self._port_last_state: dict[int, bool] = {}
        self._port_down_active: set[int] = set()
        self._port_flap_times: dict[int, deque[float]] = {}
        self._port_flapping_active: set[int] = set()

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

    def _can_send_alert(self, alert_type: str, key: str, now_monotonic: float) -> bool:
        last = self._last_alert_sent.get((alert_type, key))
        if last is None:
            return True
        return (now_monotonic - last) >= ALERT_COOLDOWN_SECONDS

    async def _broadcast(self, message: dict[str, Any]) -> None:
        if self._ws_manager is None:
            return
        try:
            await self._ws_manager.broadcast_json(message)
        except Exception:
            logger.exception("WebSocket broadcast failed")

    def _is_muted(self, now_utc: datetime) -> bool:
        if self._alert_state is None:
            return False
        mute_until = self._alert_state.mute_until_utc
        if mute_until is not None and mute_until.tzinfo is None:
            mute_until = mute_until.replace(tzinfo=timezone.utc)
        return bool(mute_until and now_utc < mute_until)

    def _emit_alert(
        self,
        ts_utc: str,
        now_utc: datetime,
        now_monotonic: float,
        *,
        type: str,
        key: str,
        message: str,
        severity: str,
    ) -> dict[str, Any] | None:
        if self._is_muted(now_utc):
            return None
        if not self._can_send_alert(type, key, now_monotonic):
            return None
        try:
            with get_connection() as conn:
                alert_id = insert_alert(
                    conn,
                    {"ts_utc": ts_utc, "type": type, "message": message, "severity": severity},
                )
            self._last_alert_sent[(type, key)] = now_monotonic
            return {
                "id": alert_id,
                "ts_utc": ts_utc,
                "type": type,
                "severity": severity,
                "message": message,
                "key": key,
            }
        except Exception:
            logger.exception("Failed to insert alert type=%s", type)
            return None

    async def _run(self) -> None:
        while True:
            now_utc_dt = datetime.now(timezone.utc)
            ts_utc = now_utc_dt.isoformat()
            now_mono = time.monotonic()

            cpu = self._safe_collect("cpu", collect_cpu) or {}
            mem = self._safe_collect("memory", collect_memory) or {}
            disk = self._safe_collect("disk", collect_disk) or {}
            net = self._safe_collect("network", collect_network) or {}

            ports_required_statuses = self._safe_collect(
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

            await self._broadcast(
                {
                    "type": "kpi",
                    "v": 1,
                    "ts_utc": ts_utc,
                    "data": {
                        "cpu_percent": snapshot.get("cpu_percent"),
                        "mem_percent": snapshot.get("mem_percent"),
                        "mem_used_bytes": snapshot.get("mem_used_bytes"),
                        "mem_avail_bytes": snapshot.get("mem_avail_bytes"),
                        "mem_total_bytes": snapshot.get("mem_total_bytes"),
                        "disk_percent": snapshot.get("disk_percent"),
                        "disk_used_bytes": snapshot.get("disk_used_bytes"),
                        "disk_free_bytes": snapshot.get("disk_free_bytes"),
                        "disk_total_bytes": snapshot.get("disk_total_bytes"),
                        "net_sent_bps": snapshot.get("net_sent_bps"),
                        "net_recv_bps": snapshot.get("net_recv_bps"),
                        "network_quality": net_quality,
                        "ping_latency_ms": latency_ms,
                    },
                }
            )
            await self._broadcast(
                {
                    "type": "chart_point",
                    "v": 1,
                    "ts_utc": ts_utc,
                    "data": {
                        "cpu_percent": snapshot.get("cpu_percent"),
                        "mem_percent": snapshot.get("mem_percent"),
                    },
                }
            )

            alerts_inserted = 0

            port_state: dict[int, bool] = {}
            for item in ports_required_statuses:
                if not isinstance(item, dict):
                    continue
                try:
                    port = int(item.get("port"))
                except Exception:
                    continue
                port_state[port] = bool(item.get("listening"))

            for port in ALERT_PORTS_REQUIRED:
                current = port_state.get(port, False)
                previous = self._port_last_state.get(port)
                if previous is None:
                    self._port_last_state[port] = current
                elif previous != current:
                    times = self._port_flap_times.setdefault(port, deque())
                    times.append(now_mono)
                    self._port_last_state[port] = current

                times = self._port_flap_times.get(port)
                if times is not None:
                    cutoff = now_mono - float(FLAP_WINDOW_SECONDS)
                    while times and times[0] < cutoff:
                        times.popleft()
                    if len(times) >= int(FLAP_THRESHOLD):
                        if port not in self._port_flapping_active:
                            if self._is_muted(now_utc_dt):
                                pass
                            elif not self._can_send_alert("port_flapping", str(port), now_mono):
                                self._port_flapping_active.add(port)
                            else:
                                alert = self._emit_alert(
                                    ts_utc,
                                    now_utc_dt,
                                    now_mono,
                                    type="port_flapping",
                                    key=str(port),
                                    message=f"Port {port} is flapping ({len(times)} state changes in {FLAP_WINDOW_SECONDS}s)",
                                    severity="warning",
                                )
                                if alert:
                                    self._port_flapping_active.add(port)
                                    alerts_inserted += 1
                                    await self._broadcast(
                                        {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                                    )
                    else:
                        self._port_flapping_active.discard(port)

                if current:
                    self._port_down_active.discard(port)
                else:
                    if port not in self._port_down_active:
                        if self._is_muted(now_utc_dt):
                            pass
                        elif not self._can_send_alert("port_down", str(port), now_mono):
                            self._port_down_active.add(port)
                        else:
                            alert = self._emit_alert(
                                ts_utc,
                                now_utc_dt,
                                now_mono,
                                type="port_down",
                                key=str(port),
                                message=f"Required port down: {port}",
                                severity="critical",
                            )
                            if alert:
                                alerts_inserted += 1
                                self._port_down_active.add(port)
                                await self._broadcast(
                                    {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                                )

            if (
                self._ws_manager is not None
                and await self._ws_manager.has_connections()
                and (now_mono - self._last_processes_broadcast_mono) >= 5.0
            ):
                self._last_processes_broadcast_mono = now_mono
                try:
                    from app.collectors.processes import get_top_processes

                    items = await asyncio.to_thread(get_top_processes, 10)
                    await self._broadcast(
                        {
                            "type": "processes",
                            "v": 1,
                            "ts_utc": ts_utc,
                            "data": {"items": items},
                        }
                    )
                except Exception:
                    logger.exception("Failed to broadcast processes")

            cpu_percent = float(snapshot.get("cpu_percent") or 0.0)
            if cpu_percent >= ALERT_CPU_PERCENT:
                if self._cpu_high_since_mono is None:
                    self._cpu_high_since_mono = now_mono
                if (
                    not self._cpu_high_fired
                    and self._cpu_high_since_mono is not None
                    and (now_mono - self._cpu_high_since_mono) >= float(ALERT_CPU_DURATION_SECONDS)
                ):
                    alert = self._emit_alert(
                        ts_utc,
                        now_utc_dt,
                        now_mono,
                        type="cpu_high",
                        key="global",
                        message=f"CPU usage high for {ALERT_CPU_DURATION_SECONDS}s: {cpu_percent:.1f}%",
                        severity="warning",
                    )
                    if alert:
                        self._cpu_high_fired = True
                        alerts_inserted += 1
                        await self._broadcast(
                            {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                        )
                    elif not self._is_muted(now_utc_dt) and not self._can_send_alert(
                        "cpu_high", "global", now_mono
                    ):
                        self._cpu_high_fired = True
            else:
                self._cpu_high_since_mono = None
                self._cpu_high_fired = False

            mem_percent = float(snapshot.get("mem_percent") or 0.0)
            if mem_percent >= ALERT_RAM_PERCENT:
                if self._ram_high_since_mono is None:
                    self._ram_high_since_mono = now_mono
                if (
                    not self._ram_high_fired
                    and self._ram_high_since_mono is not None
                    and (now_mono - self._ram_high_since_mono) >= float(ALERT_RAM_DURATION_SECONDS)
                ):
                    alert = self._emit_alert(
                        ts_utc,
                        now_utc_dt,
                        now_mono,
                        type="ram_high",
                        key="global",
                        message=f"RAM usage high for {ALERT_RAM_DURATION_SECONDS}s: {mem_percent:.1f}%",
                        severity="warning",
                    )
                    if alert:
                        self._ram_high_fired = True
                        alerts_inserted += 1
                        await self._broadcast(
                            {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                        )
                    elif not self._is_muted(now_utc_dt) and not self._can_send_alert(
                        "ram_high", "global", now_mono
                    ):
                        self._ram_high_fired = True
            else:
                self._ram_high_since_mono = None
                self._ram_high_fired = False

            if net_quality == "offline":
                if self._net_offline_since_mono is None:
                    self._net_offline_since_mono = now_mono
                if (
                    not self._net_offline_fired
                    and self._net_offline_since_mono is not None
                    and (now_mono - self._net_offline_since_mono)
                    >= float(ALERT_NET_OFFLINE_SECONDS)
                ):
                    alert = self._emit_alert(
                        ts_utc,
                        now_utc_dt,
                        now_mono,
                        type="network_offline",
                        key=NETWORK_PING_HOST,
                        message=f"Network offline for {ALERT_NET_OFFLINE_SECONDS}s (ping {NETWORK_PING_HOST})",
                        severity="critical",
                    )
                    if alert:
                        self._net_offline_fired = True
                        alerts_inserted += 1
                        await self._broadcast(
                            {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                        )
                    elif not self._is_muted(now_utc_dt) and not self._can_send_alert(
                        "network_offline", NETWORK_PING_HOST, now_mono
                    ):
                        self._net_offline_fired = True
            else:
                self._net_offline_since_mono = None
                self._net_offline_fired = False

            if net_quality == "poor":
                if not self._net_poor_fired:
                    latency_str = "N/A" if latency_ms is None else f"{latency_ms:.0f}ms"
                    alert = self._emit_alert(
                        ts_utc,
                        now_utc_dt,
                        now_mono,
                        type="network_poor",
                        key=NETWORK_PING_HOST,
                        message=f"Network poor (ping {NETWORK_PING_HOST} latency {latency_str})",
                        severity="warning",
                    )
                    if alert:
                        self._net_poor_fired = True
                        alerts_inserted += 1
                        await self._broadcast(
                            {"type": "alert", "v": 1, "ts_utc": ts_utc, "data": alert}
                        )
                    elif not self._is_muted(now_utc_dt) and not self._can_send_alert(
                        "network_poor", NETWORK_PING_HOST, now_mono
                    ):
                        self._net_poor_fired = True
            else:
                self._net_poor_fired = False

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
