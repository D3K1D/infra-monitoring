# Ubuntu service installation

These service files run the monitoring backend and the Linux server's local
agent automatically. They are written for the current deployment account
(`omni`) and repository path (`/home/omni/infra-monitoring`).

The backend uses its existing `backend/.env` file and Python 3.12 virtual
environment. The agent uses its existing `agent/agent.config` file and separate
Python 3.12 virtual environment. Neither service changes Ubuntu's system Python.

## Install

Stop any manually running backend and agent processes before installing the
services. From the repository root:

```bash
sudo cp deployment/systemd/infra-monitoring-backend.service /etc/systemd/system/
sudo cp deployment/systemd/infra-monitoring-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now infra-monitoring-backend.service
sudo systemctl enable --now infra-monitoring-agent.service
```

## Verify

```bash
systemctl is-enabled infra-monitoring-backend.service
systemctl is-active infra-monitoring-backend.service
systemctl is-enabled infra-monitoring-agent.service
systemctl is-active infra-monitoring-agent.service
curl http://127.0.0.1:8000/api/health
```

Each service should report `enabled` and `active`. The health request should
return `{"status":"ok"}`.

Recent service output can be viewed with:

```bash
sudo journalctl -u infra-monitoring-backend.service -n 50 --no-pager
sudo journalctl -u infra-monitoring-agent.service -n 50 --no-pager
```

## Restart after a project update

After pulling a later application update, restart both services:

```bash
sudo systemctl restart infra-monitoring-backend.service
sudo systemctl restart infra-monitoring-agent.service
```

## Private remote access with Tailscale

Tailscale provides encrypted access without publishing the dashboard or opening
router ports. Install it on the server and join the same private tailnet as the
authorized client devices:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

After approving the server in the Tailscale authentication page, confirm that
the service is active and obtain the server's private Tailscale address:

```bash
sudo systemctl is-active tailscaled
tailscale ip -4
```

The dashboard can be reached privately at
`http://<tailscale-ip>:8000`. For a private HTTPS address without the port
number, configure Tailscale Serve:

```bash
sudo tailscale serve --bg 8000
tailscale serve status
```

Enable HTTPS certificates when prompted, but leave Tailscale Funnel disabled.
Serve remains private to authorized tailnet devices; Funnel would publish the
service to the Internet.
