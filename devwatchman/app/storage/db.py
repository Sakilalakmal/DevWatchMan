from __future__ import annotations

import logging
import sqlite3

from app.core.config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    expected_columns: dict[str, str] = {
        "cpu_percent": "REAL",
        "mem_percent": "REAL",
        "mem_used_bytes": "INTEGER",
        "mem_avail_bytes": "INTEGER",
        "mem_total_bytes": "INTEGER",
        "disk_percent": "REAL",
        "disk_used_bytes": "INTEGER",
        "disk_free_bytes": "INTEGER",
        "disk_total_bytes": "INTEGER",
        "net_sent_bps": "REAL",
        "net_recv_bps": "REAL",
    }

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                cpu_percent REAL,
                mem_percent REAL,
                mem_used_bytes INTEGER,
                mem_avail_bytes INTEGER,
                mem_total_bytes INTEGER,
                disk_percent REAL,
                disk_used_bytes INTEGER,
                disk_free_bytes INTEGER,
                disk_total_bytes INTEGER,
                net_sent_bps REAL,
                net_recv_bps REAL
            )
            """
        )

        existing_cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(snapshots)").fetchall()
        }
        for name, col_type in expected_columns.items():
            if name not in existing_cols:
                conn.execute(f"ALTER TABLE snapshots ADD COLUMN {name} {col_type}")

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_ts_utc ON snapshots(ts_utc)"
        )
        conn.commit()

    logger.info("SQLite initialized at %s", DB_PATH)
