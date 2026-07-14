"""Metric agent: collects this machine's CPU/memory/disk usage and reports it
to the monitoring backend on a fixed interval."""

import os
import platform
import socket
import time

import psutil
import requests


def load_config():
    """Read settings from agent.config (KEY=VALUE lines), falling back to defaults."""
    config = {
        "API_URL": "http://localhost:8000",
        "API_KEY": "",
        "NODE_NAME": "",
        "LOCATION": "",
        "INTERVAL": "15",
    }
    path = os.path.join(os.path.dirname(__file__), "agent.config")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def get_ip_address():
    """Best-effort primary IP. Opening a UDP socket does not send any packets."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def collect_metrics(node_name, location):
    """Read real system metrics from this machine.

    disk_percent is how FULL the drive is; disk_io_percent is how BUSY it is
    (share of the sample window spent on reads/writes, like Task Manager's
    disk column). Both are measured over the same one-second window as CPU.
    """
    io_before = psutil.disk_io_counters()
    cpu_percent = psutil.cpu_percent(interval=1)  # blocks for the 1s window
    io_after = psutil.disk_io_counters()

    disk_io_percent = 0.0
    if io_before is not None and io_after is not None:
        busy_ms = (io_after.read_time - io_before.read_time) + (
            io_after.write_time - io_before.write_time
        )
        # Overlapping/queued IO can exceed the wall-clock window; cap at 100.
        disk_io_percent = min(busy_ms / 1000 * 100, 100.0)

    return {
        "hostname": node_name or socket.gethostname(),
        "ip_address": get_ip_address(),
        "os": f"{platform.system()} {platform.release()}",
        "location": location or None,
        "cpu_percent": cpu_percent,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "disk_io_percent": round(disk_io_percent, 1),
    }


def main():
    config = load_config()
    api_url = config["API_URL"].rstrip("/")
    endpoint = f"{api_url}/api/metrics"
    interval = int(config["INTERVAL"])
    headers = {"X-API-Key": config["API_KEY"]}

    if not config["API_KEY"]:
        print("Warning: API_KEY is not set in agent.config; the backend will reject reports.")
    print(f"Agent starting. Reporting to {endpoint} every {interval}s.")

    while True:
        payload = collect_metrics(config["NODE_NAME"], config["LOCATION"])
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code == 201:
                print(
                    f"Sent: cpu={payload['cpu_percent']}% "
                    f"mem={payload['memory_percent']}% "
                    f"disk={payload['disk_percent']}% "
                    f"disk_io={payload['disk_io_percent']}%"
                )
            else:
                print(f"Backend returned {response.status_code}: {response.text}")
        except requests.RequestException as e:
            # Keep running through network/backend outages instead of crashing.
            print(f"Could not reach backend: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()
