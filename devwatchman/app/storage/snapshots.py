from __future__ import annotations

import sqlite3
from typing import Any


def insert_snapshot(conn: sqlite3.Connection, snapshot: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO snapshots (
            ts_utc,
            cpu_percent,
            mem_percent,
            mem_used_bytes,
            mem_avail_bytes,
            mem_total_bytes,
            disk_percent,
            disk_used_bytes,
            disk_free_bytes,
            disk_total_bytes,
            net_sent_bps,
            net_recv_bps
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot["ts_utc"],
            snapshot.get("cpu_percent"),
            snapshot.get("mem_percent"),
            snapshot.get("mem_used_bytes"),
            snapshot.get("mem_avail_bytes"),
            snapshot.get("mem_total_bytes"),
            snapshot.get("disk_percent"),
            snapshot.get("disk_used_bytes"),
            snapshot.get("disk_free_bytes"),
            snapshot.get("disk_total_bytes"),
            snapshot.get("net_sent_bps"),
            snapshot.get("net_recv_bps"),
        ),
    )
    conn.commit()


def get_latest_snapshot(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM snapshots ORDER BY ts_utc DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def get_snapshot_history(
    conn: sqlite3.Connection, since_ts_utc: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM snapshots WHERE ts_utc >= ? ORDER BY ts_utc ASC",
        (since_ts_utc,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_snapshot_history_1m(
    conn: sqlite3.Connection, since_ts_utc: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            bucket_start_utc,
            avg_cpu_percent,
            avg_mem_percent,
            avg_disk_percent,
            avg_net_sent_bps,
            avg_net_recv_bps
        FROM snapshots_1m
        WHERE bucket_start_utc >= ?
        ORDER BY bucket_start_utc ASC
        """,
        (since_ts_utc,),
    ).fetchall()

    results: list[dict[str, Any]] = []
    for i, r in enumerate(rows, start=1):
        results.append(
            {
                "id": i,
                "ts_utc": r["bucket_start_utc"],
                "cpu_percent": r["avg_cpu_percent"],
                "mem_percent": r["avg_mem_percent"],
                "disk_percent": r["avg_disk_percent"],
                "net_sent_bps": r["avg_net_sent_bps"],
                "net_recv_bps": r["avg_net_recv_bps"],
                "mem_used_bytes": None,
                "mem_avail_bytes": None,
                "mem_total_bytes": None,
                "disk_used_bytes": None,
                "disk_free_bytes": None,
                "disk_total_bytes": None,
            }
        )
    return results


def get_snapshot_history_15m(
    conn: sqlite3.Connection, since_ts_utc: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            bucket_start_utc,
            avg_cpu_percent,
            avg_mem_percent,
            avg_disk_percent,
            avg_net_sent_bps,
            avg_net_recv_bps
        FROM snapshots_15m
        WHERE bucket_start_utc >= ?
        ORDER BY bucket_start_utc ASC
        """,
        (since_ts_utc,),
    ).fetchall()

    results: list[dict[str, Any]] = []
    for i, r in enumerate(rows, start=1):
        results.append(
            {
                "id": i,
                "ts_utc": r["bucket_start_utc"],
                "cpu_percent": r["avg_cpu_percent"],
                "mem_percent": r["avg_mem_percent"],
                "disk_percent": r["avg_disk_percent"],
                "net_sent_bps": r["avg_net_sent_bps"],
                "net_recv_bps": r["avg_net_recv_bps"],
                "mem_used_bytes": None,
                "mem_avail_bytes": None,
                "mem_total_bytes": None,
                "disk_used_bytes": None,
                "disk_free_bytes": None,
                "disk_total_bytes": None,
            }
        )
    return results
