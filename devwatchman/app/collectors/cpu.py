from __future__ import annotations

import psutil


def collect_cpu() -> dict[str, float]:
    return {"percent": float(psutil.cpu_percent(interval=None))}

