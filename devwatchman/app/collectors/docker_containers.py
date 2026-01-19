from __future__ import annotations

from typing import Any


def _humanize_docker_error(err: Exception) -> str:
    msg = (str(err) or "").strip()
    lower = msg.lower()

    # Windows Docker Desktop / named pipe missing
    if "createfile" in lower and "the system cannot find the file specified" in lower:
        return "Docker engine not running (start Docker Desktop)"
    if "docker_engine" in lower and ("file not found" in lower or "cannot find" in lower):
        return "Docker engine not running (start Docker Desktop)"
    if "is the docker daemon running" in lower:
        return "Docker engine not running (start Docker Desktop)"

    # Permissions / access
    if "access is denied" in lower or "permission" in lower:
        return "Docker not accessible (permission denied)"

    # Timeouts / networking
    if "timed out" in lower or "timeout" in lower:
        return "Docker engine not responding (timeout)"

    if not msg:
        return "docker unavailable"

    # Keep UI readable: one line, bounded length
    first_line = msg.splitlines()[0].strip()
    if len(first_line) > 180:
        return first_line[:177] + "..."
    return first_line


def _get_docker():
    try:
        import docker  # type: ignore

        return docker
    except Exception:
        return None


def docker_available() -> tuple[bool, str]:
    docker = _get_docker()
    if docker is None:
        return False, "python package 'docker' not installed"

    try:
        client = docker.from_env()
        client.ping()
        return True, "ok"
    except Exception as e:
        return False, _humanize_docker_error(e)


def _safe_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


def _format_ports(attrs: dict[str, Any] | None) -> list[str]:
    if not attrs:
        return []
    try:
        ports = attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
    except Exception:
        ports = {}

    results: list[str] = []
    if not isinstance(ports, dict):
        return results

    for container_port, bindings in ports.items():
        if not bindings:
            continue
        if isinstance(bindings, list):
            for b in bindings:
                if not isinstance(b, dict):
                    continue
                host_ip = b.get("HostIp") or "0.0.0.0"
                host_port = b.get("HostPort")
                if host_port:
                    results.append(f"{host_ip}:{host_port}->{container_port}")
        elif isinstance(bindings, dict):
            host_ip = bindings.get("HostIp") or "0.0.0.0"
            host_port = bindings.get("HostPort")
            if host_port:
                results.append(f"{host_ip}:{host_port}->{container_port}")
    return results


def list_containers(*, include_stopped: bool = True) -> list[dict[str, Any]]:
    docker = _get_docker()
    if docker is None:
        return []

    try:
        client = docker.from_env()
        containers = client.containers.list(all=bool(include_stopped))
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for c in containers:
        try:
            attrs = getattr(c, "attrs", None) or {}
            state = (attrs.get("State") or {}) if isinstance(attrs, dict) else {}
            name = getattr(c, "name", None) or attrs.get("Name") or ""
            if isinstance(name, str) and name.startswith("/"):
                name = name[1:]
            item = {
                "id": getattr(c, "id", "") or "",
                "name": str(name or ""),
                "image": str(getattr(getattr(c, "image", None), "tags", None) or (attrs.get("Config", {}).get("Image") if isinstance(attrs, dict) else "") or ""),
                "status": str(getattr(c, "status", "") or ""),
                "state": str(state.get("Status") or getattr(c, "status", "") or ""),
                "created": _safe_iso(attrs.get("Created") if isinstance(attrs, dict) else None),
                "started_at": _safe_iso(state.get("StartedAt") if isinstance(state, dict) else None),
                "restart_count": int(attrs.get("RestartCount") or state.get("RestartCount") or 0),
                "ports": _format_ports(attrs if isinstance(attrs, dict) else None),
            }
            items.append(item)
        except Exception:
            continue

    items.sort(key=lambda x: (str(x.get("name") or ""), str(x.get("id") or "")))
    return items


def _compute_cpu_percent(stats: dict[str, Any]) -> float:
    try:
        cpu_stats = stats.get("cpu_stats") or {}
        precpu_stats = stats.get("precpu_stats") or {}
        cpu_total = float((cpu_stats.get("cpu_usage") or {}).get("total_usage") or 0.0)
        pre_cpu_total = float((precpu_stats.get("cpu_usage") or {}).get("total_usage") or 0.0)
        system_cpu = float(cpu_stats.get("system_cpu_usage") or 0.0)
        pre_system_cpu = float(precpu_stats.get("system_cpu_usage") or 0.0)

        cpu_delta = cpu_total - pre_cpu_total
        system_delta = system_cpu - pre_system_cpu

        online = cpu_stats.get("online_cpus")
        if isinstance(online, int) and online > 0:
            num_cpus = online
        else:
            percpu = (cpu_stats.get("cpu_usage") or {}).get("percpu_usage") or []
            num_cpus = len(percpu) if isinstance(percpu, list) and len(percpu) > 0 else 1

        if system_delta <= 0 or cpu_delta <= 0:
            return 0.0
        return (cpu_delta / system_delta) * float(num_cpus) * 100.0
    except Exception:
        return 0.0


def _extract_network_bytes(stats: dict[str, Any]) -> tuple[int, int]:
    rx = 0
    tx = 0
    try:
        networks = stats.get("networks") or {}
        if isinstance(networks, dict):
            for v in networks.values():
                if not isinstance(v, dict):
                    continue
                rx += int(v.get("rx_bytes") or 0)
                tx += int(v.get("tx_bytes") or 0)
    except Exception:
        rx = 0
        tx = 0
    return rx, tx


def get_container_stats(container_id: str) -> dict[str, Any]:
    docker = _get_docker()
    if docker is None:
        return {
            "cpu_percent": 0.0,
            "mem_usage_bytes": 0,
            "mem_limit_bytes": 0,
            "mem_percent": 0.0,
            "net_rx_bytes": 0,
            "net_tx_bytes": 0,
        }

    try:
        client = docker.from_env()
        stats = client.api.stats(container_id, stream=False)
    except Exception:
        return {
            "cpu_percent": 0.0,
            "mem_usage_bytes": 0,
            "mem_limit_bytes": 0,
            "mem_percent": 0.0,
            "net_rx_bytes": 0,
            "net_tx_bytes": 0,
        }

    try:
        mem_stats = stats.get("memory_stats") or {}
        mem_usage = int(mem_stats.get("usage") or 0)
        mem_limit = int(mem_stats.get("limit") or 0)
        mem_percent = (float(mem_usage) / float(mem_limit) * 100.0) if mem_limit > 0 else 0.0
        rx, tx = _extract_network_bytes(stats)
        return {
            "cpu_percent": float(_compute_cpu_percent(stats)),
            "mem_usage_bytes": mem_usage,
            "mem_limit_bytes": mem_limit,
            "mem_percent": float(mem_percent),
            "net_rx_bytes": int(rx),
            "net_tx_bytes": int(tx),
        }
    except Exception:
        return {
            "cpu_percent": 0.0,
            "mem_usage_bytes": 0,
            "mem_limit_bytes": 0,
            "mem_percent": 0.0,
            "net_rx_bytes": 0,
            "net_tx_bytes": 0,
        }

