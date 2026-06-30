# Running the Monitoring System (development)

Three programs run at the same time during development, each in its own
PowerShell terminal, started from the project root. MySQL runs in the background
as a Windows service.

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

**Terminal 3 - Dashboard**
```powershell
cd frontend
py -3.12 -m http.server 5500
```
Open http://localhost:5500

## Stop

Press Ctrl+C in each of the three terminals (or just close them). All code and
config is saved on disk, and node/metric data persists in MySQL.

## Notes

- The dashboard now has three pages, reachable from the menu bar at the top:
  Dashboard (nodes), Alerts (list + acknowledge), and Thresholds (edit limits).
  They are all served by the same static server above.
- If activating the venv is blocked ("running scripts is disabled"), run this
  once in that terminal, then activate again:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- MySQL starts automatically with Windows; no need to start or stop it manually.
- First-time-only setup (already done): create the venv, `pip install -r requirements.txt`,
  copy `.env.example` to `.env`, and load `database/schema.sql` into MySQL.
