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
    security.py          password hashing
    main.py              app entry point + CORS + health check
    routers/             API endpoints (metrics, nodes, alerts, thresholds)
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
cp .env.example .env        # then edit DB credentials and SECRET_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Check it: open http://localhost:8000/api/health — should return `{"status":"ok"}`.
Interactive API docs are at http://localhost:8000/docs.

### 3. Agent
```bash
cd agent
pip install -r requirements.txt
cp agent.config.example agent.config   # set API_URL to the backend address
python3 agent.py
```

### 4. Frontend
Serve the `frontend/` folder with any static server, e.g.:
```bash
cd frontend
python3 -m http.server 5500
```
Open http://localhost:5500.

## Status

Foundation is in place: database schema, the metric agent, and the dashboard
scaffold. The backend handles metric ingestion and node listing, and now includes
the alerts engine: incoming readings are checked against the thresholds table,
deduplicated alerts are raised on warning/critical crossings, a background task
marks nodes offline on missed check-ins, and the API exposes alert listing,
acknowledgement, and threshold management (`/api/alerts`, `/api/thresholds`).

Next steps: the dashboard alerts page and threshold-management UI, then
authentication with role-based access, then the Chart.js history charts.
