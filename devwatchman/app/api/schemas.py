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


class PortStatusData(BaseModel):
    port: int
    listening: bool
    pid: int | None = None
    process_name: str | None = None


class PortsResponse(BaseModel):
    ok: bool
    data: list[PortStatusData] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class NetworkData(BaseModel):
    host: str
    timeout_ms: int
    latency_ms: float | None = None
    status: str


class NetworkResponse(BaseModel):
    ok: bool
    data: NetworkData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class AlertData(BaseModel):
    id: int
    ts_utc: str
    type: str
    message: str
    severity: str


class AlertsResponse(BaseModel):
    ok: bool
    data: list[AlertData] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
