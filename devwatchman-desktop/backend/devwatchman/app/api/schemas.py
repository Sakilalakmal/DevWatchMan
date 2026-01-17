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


class ListeningPortItem(BaseModel):
    local_ip: str
    port: int
    pid: int
    process_name: str


class ListeningPortsData(BaseModel):
    items: list[ListeningPortItem] = Field(default_factory=list)


class ListeningPortsResponse(BaseModel):
    ok: bool
    data: ListeningPortsData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ProfileItem(BaseModel):
    name: str
    watch_ports: list[int] = Field(default_factory=list)
    required_ports: list[int] = Field(default_factory=list)
    alert_cpu_percent: int
    alert_ram_percent: int


class ProfilesData(BaseModel):
    active: str
    profiles: list[ProfileItem] = Field(default_factory=list)


class ProfilesResponse(BaseModel):
    ok: bool
    data: ProfilesData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ProfileSelectData(BaseModel):
    active: str
    profile: ProfileItem


class ProfileSelectResponse(BaseModel):
    ok: bool
    data: ProfileSelectData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class DockerStatusData(BaseModel):
    available: bool
    reason: str


class DockerStatusResponse(BaseModel):
    ok: bool
    data: DockerStatusData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class DockerContainerStats(BaseModel):
    cpu_percent: float = 0.0
    mem_usage_bytes: int = 0
    mem_limit_bytes: int = 0
    mem_percent: float = 0.0
    net_rx_bytes: int = 0
    net_tx_bytes: int = 0


class DockerContainerItem(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: str
    created: str | None = None
    started_at: str | None = None
    restart_count: int = 0
    ports: list[str] = Field(default_factory=list)
    stats: DockerContainerStats = Field(default_factory=DockerContainerStats)


class DockerContainersData(BaseModel):
    items: list[DockerContainerItem] = Field(default_factory=list)


class DockerContainersResponse(BaseModel):
    ok: bool
    data: DockerContainersData | None = None
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
    acknowledged: bool = False
    acknowledged_ts_utc: str | None = None


class AlertsResponse(BaseModel):
    ok: bool
    data: list[AlertData] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class AlertAckData(BaseModel):
    id: int
    acknowledged: bool
    acknowledged_ts_utc: str


class AlertAckResponse(BaseModel):
    ok: bool
    data: AlertAckData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class MuteStatusData(BaseModel):
    muted: bool
    mute_until_utc: str | None = None


class MuteStatusResponse(BaseModel):
    ok: bool
    data: MuteStatusData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ProcessItem(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_bytes: int
    status: str
    username: str


class ProcessesData(BaseModel):
    items: list[ProcessItem] = Field(default_factory=list)


class ProcessesResponse(BaseModel):
    ok: bool
    data: ProcessesData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    id: int
    ts_utc: str
    kind: str
    message: str
    severity: str
    meta_json: str | None = None
    meta: dict[str, Any] | None = None


class TimelineData(BaseModel):
    items: list[TimelineEvent] = Field(default_factory=list)


class TimelineResponse(BaseModel):
    ok: bool
    data: TimelineData | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
