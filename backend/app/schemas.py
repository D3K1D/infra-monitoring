from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ----- Metrics sent in by an agent -----
class MetricIn(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    os: Optional[str] = None
    location: Optional[str] = None
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    # Defaults to 0 so an agent that hasn't been updated yet can still report.
    disk_io_percent: float = 0.0


class MetricOut(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    disk_io_percent: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Nodes shown on the dashboard -----
class NodeOut(BaseModel):
    id: int
    hostname: str
    ip_address: Optional[str]
    os: Optional[str]
    location: Optional[str]
    status: str
    last_seen: Optional[datetime]
    # From the node's most recent reading; None until it has reported once.
    disk_percent: Optional[float] = None
    # Live threshold conditions from the latest reading. These describe why a
    # node is currently warning and do not depend on alert acknowledgment.
    warning_reasons: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ----- Alerts shown on the dashboard -----
class AlertOut(BaseModel):
    id: int
    node_id: int
    hostname: str
    severity: str
    trigger_reason: str
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[int]
    cleared_at: Optional[datetime]


# ----- Thresholds (admin-managed) -----
class ThresholdOut(BaseModel):
    metric_type: str
    warning_value: float
    critical_value: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThresholdUpdate(BaseModel):
    warning_value: float = Field(ge=0, le=100)
    critical_value: float = Field(ge=0, le=100)


# ----- Dashboard summary -----
class SummaryOut(BaseModel):
    total_nodes: int
    online: int
    warning: int
    offline: int
    active_alerts: int
    ongoing_alerts: int
    recovered_unacknowledged: int
    # None until at least one node has existed long enough to expect readings.
    uptime_percent: Optional[float]
    window_minutes: int


# ----- Users / auth -----
# Role is assigned server-side (first user = admin), never taken from the client.
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: Literal["admin", "technician"]
