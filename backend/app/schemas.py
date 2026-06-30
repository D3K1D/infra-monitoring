from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ----- Metrics sent in by an agent -----
class MetricIn(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    os: Optional[str] = None
    location: Optional[str] = None
    cpu_percent: float
    memory_percent: float
    disk_percent: float


class MetricOut(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
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


# ----- Thresholds (admin-managed) -----
class ThresholdOut(BaseModel):
    metric_type: str
    warning_value: float
    critical_value: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThresholdUpdate(BaseModel):
    warning_value: float
    critical_value: float


# ----- Users (auth wiring comes next) -----
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "technician"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)
