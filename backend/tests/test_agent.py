import importlib.util
import io
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


def test_load_config_accepts_windows_utf8_bom(monkeypatch):
    config_bytes = (
        b"\xef\xbb\xbf"
        b"API_URL=https://linuxserver.example.ts.net\n"
        b"API_KEY=test-key\n"
        b"LOCATION=Home Laptop\n"
    )

    def open_config(_path, encoding=None):
        return io.TextIOWrapper(io.BytesIO(config_bytes), encoding=encoding)

    monkeypatch.setattr(metric_agent.os.path, "exists", lambda _path: True)
    monkeypatch.setattr("builtins.open", open_config)

    config = metric_agent.load_config()

    assert config["API_URL"] == "https://linuxserver.example.ts.net"
    assert config["API_KEY"] == "test-key"
    assert config["LOCATION"] == "Home Laptop"
