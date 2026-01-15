from __future__ import annotations

import psutil


def get_port_status(watch_ports: list[int]) -> list[dict[str, int | bool | str | None]]:
    port_to_pid: dict[int, int] = {}

    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, OSError):
        connections = []

    for conn in connections:
        try:
            if conn.status != psutil.CONN_LISTEN:
                continue
            if conn.laddr is None:
                continue
            port_to_pid[int(conn.laddr.port)] = int(conn.pid) if conn.pid else 0
        except Exception:
            continue

    name_cache: dict[int, str | None] = {}

    results: list[dict[str, int | bool | str | None]] = []
    for port in watch_ports:
        pid_val = port_to_pid.get(port)
        listening = pid_val is not None

        pid: int | None
        if not listening or not pid_val:
            pid = None
        else:
            pid = pid_val

        process_name: str | None = None
        if pid is not None:
            if pid in name_cache:
                process_name = name_cache[pid]
            else:
                try:
                    process_name = psutil.Process(pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    process_name = None
                name_cache[pid] = process_name

        results.append(
            {
                "port": port,
                "listening": listening,
                "pid": pid,
                "process_name": process_name,
            }
        )

    return results
