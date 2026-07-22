# Project Development Log

This log records implementation milestones, verification results, and useful
demonstration evidence for the final presentation and video. Update it after
each completed development batch.

## Earlier project milestones

### Initial monitoring pipeline

- Designed the MySQL schema for users, nodes, metrics, thresholds, and alerts.
- Built the FastAPI application structure with routers, schemas, models, and
  services kept in separate modules.
- Built the psutil metric agent and connected it to the backend over the LAN.
- Created the classic desktop-style dashboard with node search, status filters,
  and automatic refresh.

### Alerting and thresholds

- Added warning and critical thresholds for CPU, memory, disk space, and disk
  activity.
- Added background offline detection and critical offline alerts.
- Reworked alerts into episodes so acknowledgment and physical recovery remain
  separate events.
- Added Alerts and Thresholds dashboard pages.

### Authentication and dashboard history

- Added bcrypt password hashing, JWT cookie sessions, and Admin/Technician roles.
- Protected agent ingestion with a shared API key.
- Changed the application to same-origin serving through FastAPI.
- Split disk monitoring into space used and drive activity.
- Added four historical charts and the fleet uptime calculation.

## 2026-07-22 - Batch 1: Reliability and permanent testing

### Changes

- Corrected the agent reporting cadence. Metric collection takes about one
  second, so the agent now measures elapsed cycle time and sleeps only for the
  remainder of the configured interval. A 15-second interval now means one
  reporting cycle every 15 seconds instead of approximately every 16 seconds.
- Added a permanent pytest suite under `backend/tests/` using an isolated SQLite
  database. The suite never reads from or writes to the development MySQL data.
- Added exact dependency pins for pytest and HTTPX. The existing load-bearing
  `passlib==1.7.4` and `bcrypt==4.0.1` pins were preserved.

### Automated verification

- 14 tests passed.
- Coverage includes password hashing, registration, login/logout, session
  cookies, role enforcement, agent-key authentication, metric ingestion, node
  updates, alert deduplication, escalation, acknowledgment, recovery, offline
  detection, history filtering, summary counts, uptime math, and agent timing.

### Presentation and demo evidence

- Show the agent's elapsed-time scheduling as an example of diagnosing a real
  monitoring accuracy problem.
- Show the pytest result as evidence that the core backend behaviors are now
  reproducible instead of relying on temporary test scripts.
- Demonstrate that recovery and acknowledgment are intentionally independent:
  the system records both what the machine did and what the operator reviewed.
