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

## 2026-07-22 - Batch 3: Live Windows acceptance

### Live environment verification

- Confirmed the Batch 2 commit was clean and synchronized with GitHub before
  beginning acceptance testing.
- Connected to the real MySQL development database and compared it with
  `database/schema.sql`. All five tables, current columns, enum values, indexes,
  foreign keys, and four threshold rows were already present.
- Confirmed the previously documented upgrades were installed: alert
  `cleared_at`, metric `disk_io_percent`, the expanded threshold enum, and the
  `disk_io` threshold row. No migration or schema change was necessary.
- Confirmed the FastAPI health endpoint, MySQL service, and one local agent were
  running. The second previously monitored machine remained correctly offline.

### Automated and live API verification

- All 19 permanent tests passed against the isolated test database.
- Completed 46 live acceptance checks against FastAPI and the real MySQL data.
  Coverage included session and agent-key guards, static dashboard pages, node
  lists and warning explanations, node history ordering, all five summary
  windows, threshold validation, alert recovery/acknowledgment fields, the user
  list, last-admin protection, and self-deletion protection.
- The live checks were non-destructive. They did not create or remove users,
  change thresholds, acknowledge alerts, inject metrics, or rebuild tables.

### Agent, uptime, and offline evidence

- Measured the most recent 30 live reporting intervals. Every interval was
  exactly 15 seconds, confirming that the corrected agent scheduling works in
  the real application rather than only in the isolated tests.
- Confirmed the active node was seen within seconds and the disconnected node
  remained offline.
- Existing live alert history contained recovered offline episodes and only one
  currently open offline episode for the disconnected node. This verifies that
  a reconnection clears an episode and a continuously offline node does not
  receive duplicate open episodes.
- Fleet uptime produced valid results for 15-minute, 1-hour, 6-hour, and 24-hour
  windows. The values correctly reflected one actively reporting node and one
  offline node, plus the time when the active agent had not yet been restarted.

### Remaining acceptance boundary

- The Windows live database and API acceptance gate is complete. A complete
  operator walkthrough of threshold edits, alert acknowledgment, responsive UI
  behavior, and the final demo sequence will be repeated after deployment on
  the Linux server, where the final environment will be judged.

### Presentation and demo evidence

- Use the 30 consecutive 15-second readings to demonstrate that the original
  uptime under-count was diagnosed, corrected, and verified under live load.
- Show the schema comparison as evidence that upgrades were applied safely
  without deleting the existing monitoring history.
- Explain why the current fleet uptime is below 100%: the calculation includes
  both the actively reporting machine and the deliberately disconnected node.

## 2026-07-22 - Linux deployment: Temporary hard-drive installation

### Decision and purpose

- Installed Ubuntu Server 26.04 LTS for the senior-project deployment on the
  existing blank 1TB Seagate hard drive.
- Kept Ubuntu's Python 3.14 system environment intact. The monitoring backend
  and agent will use isolated Python 3.12 environments to preserve the tested
  dependency pins, especially the required passlib 1.7.4 and bcrypt 4.0.1
  combination, without altering working application code.
- Deferred Proxmox, RAID, Jellyfin, personal cloud storage, game servers, and
  public Internet access. The immediate goal is a dependable demonstration of
  the monitoring backend, dashboard, MySQL database, and Linux agent.
- The server has no built-in Wi-Fi. Ubuntu was initially installed offline,
  then connected through Ethernet so updates and remote administration could
  begin while a permanent switch arrangement is prepared.

### Installation and network verification

- Completed the UEFI installation and booted Ubuntu successfully from the 1TB
  hard drive.
- Verified Ubuntu 26.04 LTS with Linux kernel 7.0.0-28 and Python 3.14.4 as the
  untouched system Python environment.
- Verified 15 GiB usable memory with 4 GiB swap and approximately 14 GiB memory
  available immediately after startup.
- Verified the Seagate ST1000DM010 disk uses a 1 GiB UEFI system partition and
  a 930.5 GiB ext4 root partition. The root filesystem had 861 GiB available
  after installation and updates.
- Enabled IPv4 DHCP on the `eno1` Ethernet interface after the offline installer
  initially produced only IPv6 addresses.
- Confirmed package-server access and installed the initial Ubuntu updates.
- Received private LAN address `192.168.4.70` and verified an SSH login from the
  Windows development computer. No public router ports were opened.
- Installed Git 2.53.0, the required build utilities, and MySQL 8.4.10 from the
  Ubuntu repositories. Verified that MySQL is both enabled at boot and active.
- A future eero DHCP reservation will keep the address stable for the dashboard
  and monitoring agents.

### Temporary storage and future migration

- The Ubuntu installer will use the entire 1TB hard drive. There is no existing
  operating system or data to preserve on that drive.
- When the 512GB SSD arrives, the preferred long-term migration is a clean OS
  installation on the SSD followed by an application copy and MySQL
  dump/restore. This preserves monitoring history while avoiding the risks and
  wasted space involved in cloning a larger hard drive onto a smaller SSD.
- The hard drive will not be erased or repurposed until the SSD installation,
  application, and restored database have been verified and backed up.

### Demo evidence to capture

- Photograph or record the physical server and Ubuntu login screen.
- Show the monitoring dashboard loading from the Linux server's LAN address.
- Show the server monitoring itself and receiving a second node's reports.
- Demonstrate that the backend and agent start automatically after a reboot.

## 2026-07-23 - Linux dependency packaging correction

### Deployment finding

- A clean Python 3.12 backend environment reached test collection successfully,
  confirming that the pinned FastAPI, Pydantic, Passlib, and bcrypt packages
  install on Ubuntu 26.04 when isolated from its Python 3.14 system runtime.
- The permanent test suite then exposed an incomplete test dependency list:
  `tests/test_agent.py` imports the real agent module, but a fresh backend
  environment did not contain the agent's `psutil` and `requests` packages.
- This was a packaging problem rather than an application failure or Python
  compatibility issue. No production logic was changed.

### Correction

- Added the agent's existing exact `psutil` and `requests` pins to the backend
  requirements used by the permanent regression suite.
- Kept the versions aligned with `agent/requirements.txt` and documented why
  they are present, ensuring a fresh test environment is self-contained.

### Linux verification

- Pulled deployment-fix commit `467a978` onto the Ubuntu server using its
  repository-specific read-only deploy key.
- Created isolated backend and agent environments with CPython 3.12.13 while
  leaving Ubuntu's Python 3.14.4 system runtime unchanged.
- Installed the exact pinned dependencies successfully on Linux.
- All 19 permanent regression tests passed on the server in 7.75 seconds.
- Verified the agent environment with psutil 5.9.8 and requests 2.32.3.
- The single Passlib warning concerns Python's deprecated `crypt` module and is
  expected under Python 3.12; it does not affect the pinned bcrypt-based login
  path or the test result.

## 2026-07-23 - Linux live backend smoke test

### Real environment verification

- Connected the FastAPI backend to the real MySQL `monitoring` database using a
  dedicated local database account and secrets stored in a permission-restricted
  ignored `.env` file.
- Started Uvicorn on the server and received a successful `/api/health` response
  from another computer at the server's private LAN address.
- Loaded the complete dashboard frontend remotely, including its CSS and
  JavaScript assets.
- Confirmed that protected API requests returned HTTP 401 before authentication
  and HTTP 200 after authentication.
- Registered the first Linux deployment account, which correctly became the
  administrator, and loaded the authenticated dashboard, thresholds, nodes, and
  summary endpoints.
- The initially empty node list is expected because the Linux agent had not yet
  started reporting.

## 2026-07-23 - Cross-platform timestamp correction

### Deployment finding

- The Linux agent reported successfully and appeared on the authenticated
  dashboard, but its Last Seen value displayed four hours ahead for an Eastern
  Time browser.
- Ubuntu correctly keeps the server clock in UTC. MySQL `DATETIME` values and
  Python's naive datetime objects do not include a timezone marker, so the API
  returned a UTC clock value that the browser incorrectly treated as local.

### Correction

- Added API serialization that attaches the server's real UTC offset to every
  database-backed timestamp before it is sent as JSON.
- Applied the correction consistently to node last-seen values, metric history,
  alerts, threshold updates, and user creation times.
- Preserved the existing database schema and timestamp-writing behavior. This
  keeps the fix compatible with both the UTC Linux deployment and the
  Eastern-time Windows development environment.
- Extended regression coverage to require explicit timezone offsets on node and
  metric timestamps.

## 2026-07-23 - Automatic Linux service startup

### Deployment addition

- Added version-controlled systemd service definitions for the FastAPI backend
  and the Linux server's monitoring agent.
- Configured the backend to start after the network and MySQL are available.
- Configured the local agent to start after the backend service.
- Both processes run as the unprivileged `omni` account, use the existing
  isolated Python 3.12 environments, and restart automatically after an
  unexpected exit.
- Added installation, health-check, log-viewing, and update/restart
  instructions under `deployment/README.md`.

### Purpose

- Removes the need to keep SSH terminals open or start either program manually.
- Ensures monitoring resumes automatically after a server reboot.
- Keeps the deployment configuration repeatable for the final demonstration and
  the later migration from the temporary hard drive to an SSD.
