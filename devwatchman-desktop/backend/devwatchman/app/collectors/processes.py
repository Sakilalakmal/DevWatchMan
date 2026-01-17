from __future__ import annotations

import time
from typing import Any

import psutil


def get_top_processes(limit: int) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 50))

    processes: list[psutil.Process] = []
    base_info: dict[int, dict[str, Any]] = {}

    for proc in psutil.process_iter(attrs=["pid", "name", "status", "username"]):
        try:
            pid = int(proc.info.get("pid") or proc.pid)
            base_info[pid] = {
                "pid": pid,
                "name": str(proc.info.get("name") or "unknown"),
                "status": str(proc.info.get("status") or "unknown"),
                "username": str(proc.info.get("username") or "ACCESS_DENIED"),
            }
            processes.append(proc)
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except psutil.AccessDenied:
            pid = int(getattr(proc, "pid", 0) or 0)
            if pid:
                base_info[pid] = {
                    "pid": pid,
                    "name": "unknown",
                    "status": "unknown",
                    "username": "ACCESS_DENIED",
                }
            continue
        except Exception:
            continue

    time.sleep(0.15)

    results: list[dict[str, Any]] = []
    for proc in processes:
        try:
            pid = int(proc.pid)
            info = base_info.get(pid)
            if not info:
                continue

            try:
                cpu_percent = float(proc.cpu_percent(interval=None))
            except psutil.AccessDenied:
                cpu_percent = 0.0

            try:
                mem_bytes = int(proc.memory_info().rss)
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                mem_bytes = 0

            username = info.get("username") or "ACCESS_DENIED"
            if username is None or username == "":
                username = "ACCESS_DENIED"

            results.append(
                {
                    "pid": pid,
                    "name": info.get("name") or "unknown",
                    "cpu_percent": cpu_percent,
                    "memory_bytes": mem_bytes,
                    "status": info.get("status") or "unknown",
                    "username": username,
                }
            )
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    results.sort(
        key=lambda x: (float(x.get("cpu_percent") or 0.0), int(x.get("memory_bytes") or 0)),
        reverse=True,
    )
    return results[:safe_limit]

