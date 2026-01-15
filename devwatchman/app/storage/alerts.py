from __future__ import annotations

import sqlite3
from typing import Any


def insert_alert(conn: sqlite3.Connection, alert: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO alerts (ts_utc, type, message, severity)
        VALUES (?, ?, ?, ?)
        """,
        (
            alert["ts_utc"],
            alert["type"],
            alert["message"],
            alert["severity"],
        ),
    )
    conn.commit()


def get_recent_alerts(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY ts_utc DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    return [dict(r) for r in rows]

