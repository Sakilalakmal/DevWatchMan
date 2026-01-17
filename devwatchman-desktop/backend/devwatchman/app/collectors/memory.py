from __future__ import annotations

import psutil


def collect_memory() -> dict[str, float | int]:
    mem = psutil.virtual_memory()
    return {
        "percent": float(mem.percent),
        "used_bytes": int(mem.used),
        "available_bytes": int(mem.available),
        "total_bytes": int(mem.total),
    }

