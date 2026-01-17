from __future__ import annotations

import psutil


def _clamp_limit(limit: int) -> int:
    try:
        limit_int = int(limit)
    except Exception:
        return 500
    return max(1, min(2000, limit_int))


def _get_process_name(pid: int, cache: dict[int, str]) -> str:
    cached = cache.get(pid)
    if cached is not None:
        return cached
    try:
        name = psutil.Process(pid).name()
    except psutil.AccessDenied:
        name = "ACCESS_DENIED"
    except psutil.NoSuchProcess:
        name = "UNKNOWN"
    except Exception:
        name = "UNKNOWN"
    cache[pid] = name
    return name


def get_listening_ports(limit: int) -> list[dict]:
    limit = _clamp_limit(limit)

    try:
        conns = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return []
    except Exception:
        return []

    items: list[dict] = []
    seen: set[tuple[str, int, int]] = set()
    proc_name_cache: dict[int, str] = {}

    for c in conns:
        try:
            status = getattr(c, "status", None)
            if status != "LISTEN" and status != psutil.CONN_LISTEN:
                continue

            laddr = getattr(c, "laddr", None)
            if not laddr:
                continue

            local_ip = getattr(laddr, "ip", None) or (laddr[0] if isinstance(laddr, tuple) and len(laddr) >= 1 else None)
            port = getattr(laddr, "port", None) or (laddr[1] if isinstance(laddr, tuple) and len(laddr) >= 2 else None)
            if local_ip is None or port is None:
                continue

            pid_raw = getattr(c, "pid", None)
            pid = int(pid_raw) if pid_raw is not None else 0
            process_name = _get_process_name(pid, proc_name_cache) if pid > 0 else "UNKNOWN"

            key = (str(local_ip), int(port), pid)
            if key in seen:
                continue
            seen.add(key)

            items.append(
                {
                    "local_ip": str(local_ip),
                    "port": int(port),
                    "pid": pid,
                    "process_name": process_name,
                }
            )
        except Exception:
            continue

    items.sort(key=lambda x: (x["port"], x["local_ip"], x["pid"]))
    return items[:limit]

