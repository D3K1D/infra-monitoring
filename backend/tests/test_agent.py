import importlib.util
from pathlib import Path

AGENT_PATH = Path(__file__).resolve().parents[2] / "agent" / "agent.py"
SPEC = importlib.util.spec_from_file_location("metric_agent", AGENT_PATH)
metric_agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metric_agent)


def test_remaining_interval_accounts_for_collection_and_request_time(monkeypatch):
    monkeypatch.setattr(metric_agent.time, "monotonic", lambda: 112.0)

    assert metric_agent.remaining_interval(100.0, 15) == 3.0


def test_remaining_interval_never_returns_a_negative_sleep(monkeypatch):
    monkeypatch.setattr(metric_agent.time, "monotonic", lambda: 120.0)

    assert metric_agent.remaining_interval(100.0, 15) == 0
