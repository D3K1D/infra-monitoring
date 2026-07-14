# Data Center Infrastructure Monitoring and Alert Management System

Self-hosted monitoring tool. A Python agent reports CPU/memory/disk usage from each
machine to a FastAPI backend, which stores readings in MySQL and serves them to a
web dashboard.

## Project layout

```
backend/      FastAPI app, database models, API routes
  app/
    config.py            settings loaded from environment / .env
    database.py          SQLAlchemy engine and session
    models.py            users, nodes, metrics, thresholds, alerts
    schemas.py           Pydantic request/response models
    security.py          password hashing + JWT session tokens
    deps.py              auth dependencies (current user, admin, agent key)
    main.py              app entry point, health check, static frontend serving
    routers/             API endpoints (auth, metrics, nodes, alerts, thresholds, summary)
    services/            business logic (metric ingestion, alert engine)
agent/        psutil metric agent that runs on each monitored machine
database/     schema.sql to create the MySQL tables
frontend/     static dashboard (HTML / CSS / JS, Chart.js later)
```

## Setup

### 1. Database
```bash
mysql -u root -p < database/schema.sql
```

### 2. Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit DB credentials, SECRET_KEY, AGENT_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Check it: open http://localhost:8000/api/health — should return `{"status":"ok"}`.
Interactive API docs are at http://localhost:8000/docs.

### 3. Agent
```bash
cd agent
pip install -r requirements.txt
cp agent.config.example agent.config   # set API_URL and API_KEY (= AGENT_API_KEY)
python3 agent.py
```

### 4. Dashboard
The backend serves the frontend on the same port — open http://localhost:8000
(no separate static server). Register an account on the login page; the first
account created becomes the admin, later accounts are technicians.

## Status

The full monitoring pipeline works end to end: agents report CPU/memory/disk to
the backend, readings are stored in MySQL and checked against thresholds,
deduplicated alerts fire on warning/critical crossings, and a background task
marks nodes offline on missed check-ins. The dashboard shows nodes, alerts
(with acknowledgment), and admin-editable thresholds.

Authentication is in place: registration and login with bcrypt-hashed passwords,
JWT sessions in HttpOnly cookies, role-based access (admin vs technician — only
admins can change thresholds), and agents authenticate with a shared X-API-Key.
The frontend is served by FastAPI on the same origin as the API.

History charts are in: each hostname on the dashboard links to a node detail
page with CPU, memory, disk space, and disk activity charts (Chart.js, bundled
locally) over a selectable window, and the dashboard summary shows fleet uptime
computed from check-in coverage. Disk is tracked as two metrics: space used and
drive activity (Task Manager style), both alertable. Alerts are episode-based:
one alert per excursion, cleared when the metric recovers below the warning
threshold.

All core features are complete. Next: deployment to the Ubuntu server, then
stretch goals.
