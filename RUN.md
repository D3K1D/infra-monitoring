# Running the Monitoring System (development)

Two programs run at the same time during development, each in its own
PowerShell terminal, started from the project root. MySQL runs in the background
as a Windows service. The backend serves the dashboard itself, so there is no
separate static file server anymore.

First-time setup (venv, `.env`, and loading the schema) is covered in README.md.
Once that is done, the steps below are all you need each time — you do not
recreate the venv or reload the schema again.

## Start

**Terminal 1 - Backend API**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Confirm: open http://localhost:8000/api/health -> should show {"status":"ok"}

**Terminal 2 - Metric agent**
```powershell
cd agent
..\backend\venv\Scripts\Activate.ps1
python agent.py
```
Prints a "Sent: cpu=...% mem=...% disk=...%" line every 15 seconds.

**Dashboard**

Open http://localhost:8000 (or http://<server-ip>:8000 from another device on
the LAN). The backend serves the frontend files directly. You will be sent to
the login page; the first account registered becomes the admin, everyone after
is a technician.

## Run the regression tests

The tests use an isolated SQLite database and do not touch the MySQL data.

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest
```

## Stop

Press Ctrl+C in each of the two terminals (or just close them). All code and
config is saved on disk, and node/metric data persists in MySQL.

## Notes

- The dashboard menu has four pages: Dashboard (nodes and summary), Alerts
  (condition + acknowledgment state), Thresholds (edit limits), and Users
  (admin-only role/account management). Hostname links open a node's history page.
- If activating the venv is blocked ("running scripts is disabled"), run this
  once in that terminal, then activate again:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- MySQL starts automatically with Windows; no need to start or stop it manually.
- First-time-only setup (already done): create the venv, `pip install -r requirements.txt`,
  copy `.env.example` to `.env`, and load `database/schema.sql` into MySQL.
- Auth setup (one time after the auth feature): add `AGENT_API_KEY=<random string>`
  to `backend/.env`, and set the SAME value as `API_KEY=` in `agent.config` on every
  machine running the agent (desktop AND laptop) — otherwise agents get 401s.
  Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`.
