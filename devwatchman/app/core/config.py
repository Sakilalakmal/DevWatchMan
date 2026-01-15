from __future__ import annotations

from pathlib import Path

APP_NAME: str = "DevWatchMan"
DB_PATH: Path = Path(__file__).resolve().parents[2] / "devwatchman.db"

SNAPSHOT_INTERVAL_SECONDS: int = 3
HISTORY_DEFAULT_HOURS: int = 24

WATCH_PORTS: list[int] = [3000, 5173, 8000, 1433, 5672, 15672]

ALERT_CPU_PERCENT: int = 85
ALERT_RAM_PERCENT: int = 90
ALERT_PORTS_REQUIRED: list[int] = [3000, 1433, 5672]
ALERT_COOLDOWN_SECONDS: int = 60

NETWORK_PING_HOST: str = "1.1.1.1"
NETWORK_PING_TIMEOUT_MS: int = 800
