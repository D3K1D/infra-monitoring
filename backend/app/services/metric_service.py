from datetime import datetime

from sqlalchemy.orm import Session

from .. import models, schemas
from . import alert_service


def upsert_node(db: Session, data: schemas.MetricIn) -> models.Node:
    """Find the node by hostname or create it, then refresh its identity fields."""
    node = db.query(models.Node).filter(models.Node.hostname == data.hostname).first()
    if node is None:
        node = models.Node(hostname=data.hostname)
        db.add(node)

    if data.ip_address is not None:
        node.ip_address = data.ip_address
    if data.os is not None:
        node.os = data.os
    if data.location is not None:
        node.location = data.location

    node.last_seen = datetime.now()
    node.status = "online"
    db.flush()  # assigns node.id without committing yet
    return node


def store_metric(db: Session, data: schemas.MetricIn) -> models.Metric:
    """Record one metric reading for the agent's node and persist it."""
    node = upsert_node(db, data)
    metric = models.Metric(
        node_id=node.id,
        cpu_percent=data.cpu_percent,
        memory_percent=data.memory_percent,
        disk_percent=data.disk_percent,
        disk_io_percent=data.disk_io_percent,
    )
    db.add(metric)
    db.flush()  # assigns metric.id so alerts can reference the reading's node
    alert_service.evaluate_metric(db, node, metric)
    db.commit()
    db.refresh(metric)
    return metric
