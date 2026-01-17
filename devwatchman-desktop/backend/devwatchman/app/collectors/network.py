from __future__ import annotations

import time
from dataclasses import dataclass

import psutil


@dataclass
class _NetSample:
    ts_monotonic: float
    bytes_sent: int
    bytes_recv: int


_last_sample: _NetSample | None = None


def collect_network() -> dict[str, float]:
    global _last_sample

    now = time.monotonic()
    counters = psutil.net_io_counters()
    current = _NetSample(
        ts_monotonic=now,
        bytes_sent=int(counters.bytes_sent),
        bytes_recv=int(counters.bytes_recv),
    )

    if _last_sample is None:
        _last_sample = current
        return {"bytes_sent_per_sec": 0.0, "bytes_recv_per_sec": 0.0}

    dt = now - _last_sample.ts_monotonic
    if dt <= 0:
        _last_sample = current
        return {"bytes_sent_per_sec": 0.0, "bytes_recv_per_sec": 0.0}

    sent_per_sec = (current.bytes_sent - _last_sample.bytes_sent) / dt
    recv_per_sec = (current.bytes_recv - _last_sample.bytes_recv) / dt
    _last_sample = current

    return {
        "bytes_sent_per_sec": float(max(sent_per_sec, 0.0)),
        "bytes_recv_per_sec": float(max(recv_per_sec, 0.0)),
    }

