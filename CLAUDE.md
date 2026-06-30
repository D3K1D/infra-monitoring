# Project conventions and decisions

This file records decisions already made in this codebase. Follow them in every
session instead of inventing new approaches. The full project requirements are in
the project instructions and the two assignment .docx files; this file only covers
what was decided during implementation.

## Established conventions (do not change)

- Field names are snake_case end-to-end: MySQL column -> SQLAlchemy model ->
  Pydantic schema -> JSON -> frontend JS all use the same name (e.g. `cpu_percent`,
  `last_seen`). Never rename a field at one layer only.
- `database/schema.sql` is the source of truth for the database. Do NOT add
  `Base.metadata.create_all()` or Alembic. Any schema change must update BOTH
  schema.sql and `backend/app/models.py` in the same step.
- All API routes live under the `/api` prefix, defined via `APIRouter(prefix="/api")`
  in one file per resource under `backend/app/routers/`. Business logic that touches
  the DB beyond a trivial query goes in `backend/app/services/`.
- Timestamps are generated server-side only (DB `CURRENT_TIMESTAMP` defaults or
  `datetime.now()` in the backend) and stored as naive local time. Agents never send
  timestamps, so clock skew between machines doesn't matter. Do not switch to UTC
  midway — every comparison (offline detection, charts) must stay in local time.
- Settings come from `.env` via `pydantic_settings` (`backend/app/config.py`).
  New tunables (timeouts, intervals, keys) get a Settings field + `.env.example` entry,
  never a hardcoded constant.
- Dependencies are pinned with exact versions in requirements.txt. bcrypt is pinned
  to 4.0.1 because passlib 1.7.4 breaks against bcrypt >= 4.1. Before building auth,
  run `pip install -r requirements.txt` in the existing venv and verify
  `hash_password`/`verify_password` actually work (they have not been exercised yet).
- Frontend: `js/api.js` holds all fetch calls, `js/app.js` holds rendering/logic.
  `API_BASE` is currently built from `window.location.hostname` (two-server dev
  setup); it becomes the relative path `"/api"` when same-origin serving lands in
  the auth step (see below). Never hardcode localhost or an IP there.
- Frontend style is the flat classic-Windows look in style.css (gray beveled window,
  navy title bar, teal desktop, no rounded corners, 12px Tahoma). New pages/elements
  reuse the existing bevel classes (`.window`, `.sunken-panel`, `.card`, `.badge`).
- Status enums are fixed strings: node `online|warning|offline`, alert severity
  `warning|critical`, alert status `active|acknowledged`, roles `admin|technician`,
  metric types `cpu|memory|disk`.
- Update README.md "Status" section and RUN.md whenever a new component changes how
  the system is started or what exists.

## Decisions for upcoming features (follow these when building)

### Alerts & thresholds engine (next up)
- Threshold check happens inside the metric ingestion path (`metric_service.store_metric`),
  comparing the reading against the `thresholds` table: >= critical_value -> critical,
  >= warning_value -> warning.
- Deduplicate alerts: before creating one, check for an existing ACTIVE alert for the
  same node + same condition (put the metric type in `trigger_reason` with a consistent
  format like `cpu 92.0% >= critical 85%` and match on prefix, or add a column —
  if a column is added, update schema.sql too). Without dedup, a hot CPU creates a new
  alert every 15 seconds; real systems (Nagios/Zabbix) alert once per episode.
- Node `status` reflects the latest reading: critical/warning threshold crossed ->
  `warning`, otherwise `online`. Offline overrides both.
- Offline detection: a background asyncio task started in FastAPI's lifespan handler,
  running every ~OFFLINE_TIMEOUT_SECONDS / 2. It marks nodes offline when
  `last_seen` is older than OFFLINE_TIMEOUT_SECONDS and creates a critical alert
  (deduplicated the same way). Do not compute offline status lazily in GET /nodes —
  alerts must fire even when nobody has the dashboard open.

### Authentication + same-origin serving (built together, in this order)
- Target architecture: Browser -> (Nginx, deployment stretch goal) -> FastAPI ->
  MySQL. Frontend and API are served from the SAME origin.
- Step 1, same-origin: mount `frontend/` with FastAPI StaticFiles at `/`
  (`html=True`) AFTER all routers are included, so `/api/*` keeps routing to the
  API. Then: switch `API_BASE` in js/api.js to `"/api"`, remove the CORS
  middleware, drop the separate `python -m http.server` terminal, and update
  RUN.md + README.md in the same step. Nginx is NOT needed for this — it stays a
  stretch goal that later proxies to the same single FastAPI origin.
- Step 2, cookie sessions: login (`POST /api/auth/login`) verifies the password
  and sets the JWT (python-jose, HS256, `SECRET_KEY` from .env) in an HttpOnly
  cookie: `httponly=True`, `samesite="lax"`, max-age from
  ACCESS_TOKEN_EXPIRE_MINUTES. Add the `secure` flag only when HTTPS exists
  (stretch goal) — setting it on plain LAN HTTP silently breaks login.
  The browser attaches the cookie automatically; frontend JS never stores,
  reads, or attaches tokens — no localStorage, no Authorization header.
  Logout endpoint clears the cookie. Same-origin must land first: cross-origin
  cookies on plain HTTP would require `SameSite=None; Secure`, which can't work
  without HTTPS.
- The current-user dependency reads the JWT from the cookie (not the
  Authorization header). On 401, the frontend redirects to the login page.
- SameSite=Lax is the CSRF mitigation — sufficient for this project; do not
  build CSRF tokens.
- Agents are NOT users and don't use cookies. Protect POST /api/metrics with a
  shared agent key instead: `AGENT_API_KEY` in the backend .env, sent by the
  agent as an `X-API-Key` header, configured in agent.config as API_KEY.
  Dashboard endpoints require the user cookie; ingest requires only the agent key.
- Role enforcement via a FastAPI dependency (e.g. `require_admin`): admins manage
  users and thresholds; technicians can view everything and acknowledge alerts.
- `/api/health` stays unauthenticated.

### History charts
- Endpoint shape: `GET /api/nodes/{node_id}/metrics?minutes=60` returning a list of
  MetricOut, used by Chart.js line charts. The `idx_metrics_node_time` index exists
  for exactly this query.
- Uptime % for the summary view is computed from metric check-in coverage over the
  chosen window (readings received vs. readings expected at the reporting interval).

## Multi-machine / deployment notes

- Three machines: Windows dev desktop (everything runs here now), old desktop ->
  future Ubuntu Server host, laptop = LAN client + optional second agent.
- For LAN testing from the laptop against the dev desktop: Windows Firewall needs
  an inbound rule for port 8000 (plus 5500 only while the separate static server
  still exists — it goes away with same-origin serving). On Ubuntu later:
  `ufw allow 8000` (or only 80 once Nginx fronts everything).
- MySQL stays bound to localhost — only the backend talks to it, never expose 3306.
- Give the server a DHCP reservation or static IP so agent.config API_URL values
  don't break when the router reassigns addresses.
- CORS middleware is temporary: it exists only for the current two-server dev
  setup and is removed entirely when StaticFiles same-origin serving lands (see
  the auth section). Do not re-add it afterward.

## Known gaps to address when touched

- The `metrics` table grows ~5,760 rows/node/day at a 15s interval — fine for a
  semester; do not build retention/pruning unless asked.

## Version control / repo hygiene (added 2026-06-30)

- Repo: github.com/D3K1D/infra-monitoring (Private for now; goes Public to show
  off later). Commits are authored as Andrew <D3K1D@users.noreply.github.com> via
  per-repo `git config` — never add Claude/AI as author or co-author, and keep
  CLAUDE.md and these notes out of the published repo.
- `.gitignore` (added 2026-06-30) excludes venv/, __pycache__/, .env, agent.config,
  *.docx, and CLAUDE.md. The initial push predated/ignored this, so those files got
  TRACKED. `.gitignore` does not untrack already-committed files: fix with
  `git rm -r --cached . && git add . && git commit` then push.
- SECURITY: if backend/.env (DB password + SECRET_KEY) was ever committed, it stays
  in git history even after untracking. Before going Public, rotate SECRET_KEY (and
  the MySQL password if real) and/or scrub history. Verify with
  `git ls-files | findstr .env` — only `.env.example` should appear.
- TODO (later cleanup pass before Public release): tidy the project tree, confirm
  no secrets or machine-specific paths are tracked, and review README/RUN for
  anything personal. Do this when explicitly asked, not mid-feature.
