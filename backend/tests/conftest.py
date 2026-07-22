import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Test settings must take precedence over any developer machine's .env file.
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-tests"
os.environ["AGENT_API_KEY"] = "test-agent-key"
os.environ["OFFLINE_TIMEOUT_SECONDS"] = "60"
os.environ["AGENT_INTERVAL_SECONDS"] = "15"

from app import models  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_AGENT_KEY = "test-agent-key"


@compiles(BigInteger, "sqlite")
def compile_big_integer_for_sqlite(type_, compiler, **kwargs):
    """SQLite auto-increments only columns declared with the exact INTEGER type."""
    return "INTEGER"


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def seed_thresholds(db):
    db.add_all(
        [
            models.Threshold(metric_type="cpu", warning_value=75, critical_value=85),
            models.Threshold(metric_type="memory", warning_value=80, critical_value=90),
            models.Threshold(metric_type="disk", warning_value=80, critical_value=90),
            models.Threshold(metric_type="disk_io", warning_value=85, critical_value=95),
        ]
    )
    db.commit()


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", os.environ["SECRET_KEY"])
    monkeypatch.setattr(settings, "agent_api_key", TEST_AGENT_KEY)
    monkeypatch.setattr(settings, "offline_timeout_seconds", 60)
    monkeypatch.setattr(settings, "agent_interval_seconds", 15)


@pytest.fixture()
def database():
    Base.metadata.create_all(bind=engine)
    seed_db = TestingSessionLocal()
    try:
        seed_thresholds(seed_db)
    finally:
        seed_db.close()

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(database):
    session = database()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(database):
    def override_get_db():
        session = database()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
