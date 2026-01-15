from __future__ import annotations

import sqlite3
from typing import Any


def insert_alert(conn: sqlite3.Connection, alert: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO alerts (ts_utc, type, message, severity, acknowledged, acknowledged_ts_utc)
        VALUES (?, ?, ?, ?, 0, NULL)
        """,
        (
            alert["ts_utc"],
            alert["type"],
            alert["message"],
            alert["severity"],
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_recent_alerts(
    conn: sqlite3.Connection, *, limit: int = 50, include_ack: bool = False
) -> list[dict[str, Any]]:
    if include_ack:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY ts_utc DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY ts_utc DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [dict(r) for r in rows]


def acknowledge_alert(conn: sqlite3.Connection, alert_id: int, ts_utc: str) -> bool:
    cur = conn.execute(
        """
        UPDATE alerts
        SET acknowledged = 1,
            acknowledged_ts_utc = ?
        WHERE id = ?
        """,
        (ts_utc, int(alert_id)),
    )
    conn.commit()
    return int(cur.rowcount) > 0


def set_alert_setting(conn: sqlite3.Connection, key: str, value: str | None) -> None:
    if value is None:
        conn.execute("DELETE FROM alert_settings WHERE key = ?", (key,))
    else:
        conn.execute(
            """
            INSERT INTO alert_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
    conn.commit()


def get_alert_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute(
        "SELECT value FROM alert_settings WHERE key = ? LIMIT 1",
        (key,),
    ).fetchone()
    return str(row["value"]) if row else None

