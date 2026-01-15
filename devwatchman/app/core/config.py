from __future__ import annotations

from pathlib import Path

APP_NAME: str = "DevWatchMan"
DB_PATH: Path = Path(__file__).resolve().parents[2] / "devwatchman.db"

SNAPSHOT_INTERVAL_SECONDS: int = 3
HISTORY_DEFAULT_HOURS: int = 24
