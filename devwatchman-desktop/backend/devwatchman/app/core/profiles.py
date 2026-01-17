from __future__ import annotations

from dataclasses import dataclass

from app.core.config import ALERT_CPU_PERCENT, ALERT_PORTS_REQUIRED, ALERT_RAM_PERCENT, WATCH_PORTS
from app.storage.db import get_connection

APP_STATE_KEY_ACTIVE_PROFILE: str = "active_profile_name"


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    watch_ports: tuple[int, ...]
    required_ports: tuple[int, ...]
    alert_cpu_percent: int
    alert_ram_percent: int

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "watch_ports": list(self.watch_ports),
            "required_ports": list(self.required_ports),
            "alert_cpu_percent": int(self.alert_cpu_percent),
            "alert_ram_percent": int(self.alert_ram_percent),
        }


PROFILES: dict[str, Profile] = {
    "default": Profile(
        name="default",
        watch_ports=tuple(WATCH_PORTS),
        required_ports=tuple(ALERT_PORTS_REQUIRED),
        alert_cpu_percent=int(ALERT_CPU_PERCENT),
        alert_ram_percent=int(ALERT_RAM_PERCENT),
    ),
    "frontend-dev": Profile(
        name="frontend-dev",
        watch_ports=(3000, 5173, 8000),
        required_ports=(5173,),
        alert_cpu_percent=90,
        alert_ram_percent=92,
    ),
    "microservices": Profile(
        name="microservices",
        watch_ports=(8000, 8001, 8002, 1433, 5432, 5672, 6379, 15672),
        required_ports=(8000, 1433, 5672),
        alert_cpu_percent=85,
        alert_ram_percent=90,
    ),
}


def list_profiles() -> list[Profile]:
    return [PROFILES[name] for name in sorted(PROFILES.keys())]


def get_profile(name: str) -> Profile | None:
    return PROFILES.get(name)


def get_active_profile_name() -> str:
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            row = conn.execute(
                "SELECT value FROM app_state WHERE key = ?",
                (APP_STATE_KEY_ACTIVE_PROFILE,),
            ).fetchone()
            if row is None:
                return "default"
            value = str(row["value"] or "").strip()
            return value or "default"
    except Exception:
        return "default"


def set_active_profile_name(name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO app_state(key, value) VALUES(?, ?)",
            (APP_STATE_KEY_ACTIVE_PROFILE, name),
        )
        conn.commit()


def resolve_profile(name: str | None) -> Profile:
    if name:
        p = get_profile(name)
        if p is not None:
            return p
    return PROFILES["default"]

