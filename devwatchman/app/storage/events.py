from __future__ import annotations

import json
import sqlite3
from typing import Any


def insert_event(conn: sqlite3.Connection, event: dict[str, Any]) -> int:
    meta_json = event.get("meta_json")
    if meta_json is None and event.get("meta") is not None:
        meta_json = json.dumps(event["meta"], ensure_ascii=False, separators=(",", ":"))

    cur = conn.execute(
        """
        INSERT INTO events (ts_utc, kind, message, severity, meta_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event["ts_utc"],
            event["kind"],
            event["message"],
            event["severity"],
            meta_json,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _normalize_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    meta_json = d.get("meta_json")
    if meta_json:
        try:
            d["meta"] = json.loads(meta_json)
        except Exception:
            d["meta"] = None
    else:
        d["meta"] = None
    return d


def get_events(conn: sqlite3.Connection, since_ts_utc: str, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM events WHERE ts_utc >= ? ORDER BY ts_utc DESC LIMIT ?",
        (since_ts_utc, int(limit)),
    ).fetchall()
    return [_normalize_row(r) for r in rows]


def get_latest_events(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM events ORDER BY ts_utc DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    return [_normalize_row(r) for r in rows]

