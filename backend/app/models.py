from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "technician"), nullable=False, default="technician")
    created_at = Column(DateTime, server_default=func.now())


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    hostname = Column(String(100), unique=True, nullable=False)
    ip_address = Column(String(45))
    os = Column(String(100))
    location = Column(String(100))
    status = Column(
        Enum("online", "warning", "offline"), nullable=False, default="offline"
    )
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    metrics = relationship("Metric", back_populates="node", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="node", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(BigInteger, primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)
    disk_io_percent = Column(Float, nullable=False, default=0)
    recorded_at = Column(DateTime, server_default=func.now())

    node = relationship("Node", back_populates="metrics")


class Threshold(Base):
    __tablename__ = "thresholds"

    id = Column(Integer, primary_key=True)
    metric_type = Column(
        Enum("cpu", "memory", "disk", "disk_io"), unique=True, nullable=False
    )
    warning_value = Column(Float, nullable=False)
    critical_value = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    severity = Column(Enum("warning", "critical"), nullable=False)
    trigger_reason = Column(String(255), nullable=False)
    status = Column(Enum("active", "acknowledged"), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    cleared_at = Column(DateTime)

    node = relationship("Node", back_populates="alerts")
