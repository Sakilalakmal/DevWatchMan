from __future__ import annotations

import re
import subprocess

_TIME_RE = re.compile(r"time[=<]\s*(\d+)ms", re.IGNORECASE)


def ping_latency_ms(host: str, timeout_ms: int) -> float | None:
    try:
        proc = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            capture_output=True,
            text=True,
            check=False,
            timeout=max(1.0, (timeout_ms / 1000.0) + 1.0),
        )
    except Exception:
        return None

    output = f"{proc.stdout}\n{proc.stderr}"
    match = _TIME_RE.search(output)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def classify_network(latency_ms: float | None) -> str:
    if latency_ms is None:
        return "offline"
    if latency_ms <= 50:
        return "good"
    if latency_ms <= 150:
        return "ok"
    return "poor"
