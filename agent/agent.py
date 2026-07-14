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
    """Read real system metrics from this machine."""
    return {
        "hostname": node_name or socket.gethostname(),
        "ip_address": get_ip_address(),
        "os": f"{platform.system()} {platform.release()}",
        "location": location or None,
        # interval=1 makes psutil measure CPU over a one-second window.
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
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
                    f"disk={payload['disk_percent']}%"
                )
            else:
                print(f"Backend returned {response.status_code}: {response.text}")
        except requests.RequestException as e:
            # Keep running through network/backend outages instead of crashing.
            print(f"Could not reach backend: {e}")

        time.sleep(interval)


if __name__ == "__main__":
    main()
