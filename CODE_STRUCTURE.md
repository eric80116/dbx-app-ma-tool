# Code Structure

A map of the repository and the two key extension seams. See `README.md` for the
architecture and workspace boundary.

```
.
├── databricks.yml              # DAB: bundle, variables, targets (dev), artifacts (apx build)
├── app.yml                     # Deployed App manifest: uvicorn command + env vars
├── resources/
│   ├── app.yml                 # App resource (source_code_path ../.build)
│   ├── jobs.yml                # Serverless jobs: setup/seed, dispatcher, reconcile, tests
│   └── permissions.yml         # Bundle-level permissions
├── setup/
│   ├── _bootstrap.py           # Build a Db from WorkspaceClient + AppConfig
│   ├── create_tables.py        # DDL for the 9 App-owned Delta tables (idempotent)
│   ├── seed_demo_data.py       # Deterministic synthetic seed (seed=42, ref 2026-09-29)
│   ├── run_setup.py            # Job entrypoint: create + seed (config via argv)
│   ├── run_dispatch.py         # Job entrypoint: dispatch one campaign (scheduled trigger)
│   ├── run_reconcile.py        # Job entrypoint: safety-net dispatch + wrapper-job cleanup
│   └── run_tests_task.py       # Job entrypoint: pytest integration/acceptance
├── scripts/
│   ├── deploy.sh               # One-command validate → deploy → start → seed → grant → health
│   ├── print_app_url.sh        # Print deployed App URL
│   ├── teardown.sh             # Safe, allowlist-based teardown (--confirm required)
│   ├── run_tests.sh            # Unit (+ integration if configured) → artifacts/test-results
│   └── run_acceptance_tests.sh # Per-requirement acceptance report
├── src/ma_app/
│   ├── backend/                # FastAPI backend (see below)
│   └── ui/                     # React frontend (see below)
├── tests/                      # unit / integration / acceptance
└── artifacts/test-results/     # JUnit XML + readable summaries (generated)
```

## Backend (`src/ma_app/backend/`)

```
app.py            # FastAPI entrypoint: create_app(routers=[router, health_router]) + error handlers
router.py         # Aggregates route modules onto the /api router; version + current-user
models.py         # Pydantic models + enums (Channel, CampaignStatus, DeliveryEventType, …)
db.py             # Db: SQL Warehouse access via the App service principal (parameterized);
                  #   sql_literal / bulk_insert_values / Ts / Dt helpers; DbDependency
repositories.py   # AppRepository: Delta CRUD for offers/campaigns/approvals/dispatch/events/audit
services.py       # CampaignService (create/submit/approve/reject/cancel/schedule/preview/dispatch/
                  #   metrics) + DashboardService. Enforces guardrails server-side.
scheduler.py      # ── SEAM 3: real scheduling ── to_quartz_oneshot() + Scheduler: create/cancel
                  #   the one-time wrapper job (App SP) that triggers ma_app_dispatch_job
domain/
  state_machine.py  # Allowed campaign transitions; can_dispatch; InvalidTransition
  eligibility.py    # MemberContext + classify() → ELIGIBLE / SKIPPED_* (pure, testable)
  metrics.py        # compute_metrics(): rates from Delta-derived counts
audience/           # ── SEAM 1: replaceable audience source ──
  interface.py      #   AudienceRepository protocol + AudienceNotFound / AudienceSourceUnavailable
  local_snapshot.py #   Default: reads the local synthetic snapshot
  shared_table.py   #   Placeholder: validates a shared table, fails clearly if unreachable
  __init__.py       #   get_audience_repository(db) picks by MA_APP_AUDIENCE_SOURCE_MODE
providers/          # ── SEAM 2: replaceable activation channel ──
  interface.py      #   ActivationProvider protocol + result dataclasses
  _base.py          #   Deterministic mock funnel (seed=42)
  mock_push.py / mock_sms.py / mock_coupon.py
  __init__.py       #   get_provider(channel)
routes/
  health.py         # /health (bare) + /api/system/config
  audiences.py      # /api/audiences[...], /api/offers  (PII masked by default)
  campaigns.py      # /api/campaigns CRUD + submit/approve/reject/cancel/schedule/preview/dispatch/metrics/audit
  dashboard.py      # /api/dashboard
  _common.py        # actor_from(headers)
core/               # APX framework glue (config, dependency injection, sql addon, static)
```

### Seam 1 — `AudienceRepository`

The App **consumes** an audience; it never rebuilds Campaign Agents logic. Swapping the
source (local snapshot → shared table → Delta Sharing → official API) means implementing
this one protocol and selecting it via `MA_APP_AUDIENCE_SOURCE_MODE`. Nothing else in the
App changes.

### Seam 2 — `ActivationProvider`

Every channel implements `validate()` + `send()`. The mock providers write deterministic
delivery events; a real FCM/SMS/coupon provider can replace them without touching
`CampaignService`.

## Frontend (`src/ma_app/ui/`)

```
routes/            # TanStack Router file routes (dashboard, audiences, campaigns, approvals)
  _sidebar/        # Sidebar-wrapped pages
components/
  ui/              # shadcn/ui base components
  apx/             # APX layout (sidebar, navbar, theme)
lib/
  api.ts           # AUTO-GENERATED from the backend OpenAPI schema — DO NOT EDIT
  selector.ts      # Default query selector for suspense hooks
styles/            # Tailwind / globals
```

Data fetching uses generated React Query suspense hooks (e.g. `useListAudiencesSuspense`,
`useDispatchCampaign`). Each backend route's `operation_id` becomes the hook name, so
adding an endpoint + rebuilding regenerates the client automatically.

## Setup, resources, tests

- **setup/** runs both locally (via `.env`) and as a serverless job (config via argv).
  It only ever writes to `<catalog>.<schema>`.
- **resources/** are the DAB definitions (App + jobs + permissions). Env vars for the
  deployed App live in `app.yml`, not in `databricks.yml`.
- **tests/** — `unit/` (pure, no Databricks), `integration/` (live warehouse/schema),
  `acceptance/` (one check per customer requirement). Markers: `unit`, `integration`,
  `acceptance`.
