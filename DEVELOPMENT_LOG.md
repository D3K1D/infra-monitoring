# Project Development Log

This log records implementation milestones, verification results, and useful
demonstration evidence for the final presentation and video. Update it after
each completed development batch.

## Planned public release

- After final software acceptance and Linux deployment, preserve the current
  repository as the private development archive.
- Publish a clean repository snapshot as version 1.0 so the public project starts
  with the finished application, documentation, and no private planning history.

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

## 2026-07-22 - Batch 2: Core feature completion

### Changes

- Added admin-only user management. Admins can list accounts, promote or demote
  users, and delete other accounts. The backend prevents deletion of the current
  account and prevents removal of the final administrator.
- Completed the dashboard summary with Total, Online, Warning, and Offline node
  counts plus a selectable uptime window from 15 minutes through 7 days.
- Split the active-alert display into ongoing conditions and recovered events
  that still require acknowledgment, preserving the independent machine and
  operator lifecycles.
- Added 0-100% validation to warning and critical threshold updates.
- Changed disk-space bar colors to use the administrator's current disk warning
  and critical thresholds instead of fixed default values.
- Added the Users page to the existing classic interface and kept it hidden from
  Technician navigation. Backend role checks remain the security boundary.

### Automated verification

- 18 tests passed using the isolated test database.
- New coverage verifies admin-only user access, role changes, last-admin
  protection, account deletion safeguards, threshold bounds, and alert summary
  breakdowns.
- Every first-party JavaScript file passed syntax checking.

### Presentation and demo evidence

- Log in as an Admin to demonstrate role changes and account deletion safeguards,
  then log in as a Technician to show that the Users page and threshold editing
  are unavailable.
- Change the dashboard uptime window and show the summary updating without a page
  reload.
- Change the disk threshold and show that the node's disk bar uses the configured
  warning and critical colors.
- Show an alert recovering before acknowledgment to explain why machine recovery
  and operator review are tracked separately.

## 2026-07-22 - Batch 2 follow-up: Node warning explanations

### Changes

- Added current warning reasons to the node API using each node's latest metric
  reading and the administrator's configured thresholds.
- Added a dashboard tooltip to the WARNING status badge. Hovering over it, or
  focusing it with the keyboard, lists every current cause such as high CPU,
  high memory, nearly full disk space, or high disk activity.
- Kept the explanation independent from alerts. Acknowledging an alert does not
  remove the node warning or its explanation; only a recovered metric reading
  does.

### Automated verification

- Added regression coverage for multiple simultaneous warning causes,
  critical-threshold wording, continued visibility after acknowledgment, and
  removal after metric recovery.
- All 19 permanent backend tests passed after the change.

### Presentation and demo evidence

- Trigger more than one threshold on a node and hover over its WARNING status
  to show that the dashboard explains the live condition without opening the
  Alerts page.
