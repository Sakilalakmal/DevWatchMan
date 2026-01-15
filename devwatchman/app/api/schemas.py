from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthData(BaseModel):
    status: str


class SnapshotData(BaseModel):
    id: int
    ts_utc: str
    cpu_percent: float | None = None
    mem_percent: float | None = None
    mem_used_bytes: int | None = None
    mem_avail_bytes: int | None = None
    mem_total_bytes: int | None = None
    disk_percent: float | None = None
    disk_used_bytes: int | None = None
    disk_free_bytes: int | None = None
    disk_total_bytes: int | None = None
    net_sent_bps: float | None = None
    net_recv_bps: float | None = None


class HealthResponse(BaseModel):
    ok: bool
    data: HealthData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class SnapshotResponse(BaseModel):
    ok: bool
    data: SnapshotData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    ok: bool
    data: list[SnapshotData] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

