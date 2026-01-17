from __future__ import annotations

import os
from pathlib import Path

import psutil


def collect_disk() -> dict[str, float | int]:
    candidates: list[str] = []

    home_anchor = Path.home().anchor
    if home_anchor:
        candidates.append(home_anchor)

    cwd_anchor = Path.cwd().anchor
    if cwd_anchor and cwd_anchor not in candidates:
        candidates.append(cwd_anchor)

    system_drive = os.environ.get("SystemDrive")
    if system_drive:
        candidates.append(f"{system_drive}\\")

    candidates.append("/")

    last_exc: Exception | None = None
    for path in candidates:
        try:
            usage = psutil.disk_usage(path)
            return {
                "percent": float(usage.percent),
                "used_bytes": int(usage.used),
                "free_bytes": int(usage.free),
                "total_bytes": int(usage.total),
            }
        except Exception as exc:
            last_exc = exc

    raise RuntimeError("Unable to determine disk usage") from last_exc
