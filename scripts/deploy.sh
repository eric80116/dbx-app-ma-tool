#!/usr/bin/env bash
#
# One-command deploy for the MA orchestration demo App.
#
# Steps (each must succeed or the script exits non-zero):
#   1. Verify required CLIs exist.
#   2. Validate the Databricks Asset Bundle.
#   3. Validate the target catalog, schema, and warehouse are reachable.
#   4. Deploy the bundle (App + jobs).
#   5. Start the App  (Databricks Apps must be started with `bundle run` after deploy).
#   6. Run the setup/seed job (creates tables + loads the synthetic snapshot).
#   7. Grant the App service principal least-privilege UC + warehouse access
#      (the SP only exists after the App is created, so this is a post-deploy step).
#   8. Health-check the deployed App (GET /health -> {"status":"ok"}).
#   9. Print the App URL and demo instructions (no secrets).
#
# Usage: scripts/deploy.sh [--profile <profile>] [-t <target>]
set -euo pipefail

PROFILE="${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
TARGET="dev"
APP_KEY="ma_app"           # bundle resource key
APP_NAME="ma-app"          # deployed app name
SETUP_JOB_KEY="ma_app_setup_job"

# Config (overridable via env); mirrors databricks.yml variables / app.yml env.
CATALOG="${MA_APP_TARGET_CATALOG:-ma_app_demo}"
SCHEMA="${MA_APP_APP_SCHEMA:-ma_app}"
WAREHOUSE_ID="${MA_APP_WAREHOUSE_ID:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    -t|--target) TARGET="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m    ✓ %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m    ✗ %s\033[0m\n' "$*" >&2; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Pick up preflight-resolved values (.env is gitignored). Run scripts/preflight.sh first
# to auto-detect the warehouse and write .env; the defaults below are the last resort.
if [[ -f .env ]]; then set -a; # shellcheck disable=SC1091
  source .env; set +a
fi
PROFILE="${DATABRICKS_CONFIG_PROFILE:-$PROFILE}"
CATALOG="${MA_APP_TARGET_CATALOG:-$CATALOG}"
SCHEMA="${MA_APP_APP_SCHEMA:-$SCHEMA}"
WAREHOUSE_ID="${MA_APP_WAREHOUSE_ID:-$WAREHOUSE_ID}"

# --- 1. CLIs --------------------------------------------------------------------
log "1/9 Checking required CLIs"
command -v databricks >/dev/null 2>&1 || die "databricks CLI not found"
command -v apx >/dev/null 2>&1 || die "apx CLI not found (needed for 'apx build' artifact)"
command -v python3 >/dev/null 2>&1 || die "python3 not found"
ok "databricks, apx, python3 present"

# Auto-detect a warehouse if none is configured (keeps the repo portable — no hard-coded ids).
if [[ -z "$WAREHOUSE_ID" ]]; then
  log "No warehouse configured — running preflight to auto-detect one"
  ./scripts/preflight.sh --profile "$PROFILE" --non-interactive || die "preflight could not resolve a warehouse"
  if [[ -f .env ]]; then set -a; # shellcheck disable=SC1091
    source .env; set +a
  fi
  WAREHOUSE_ID="${MA_APP_WAREHOUSE_ID:-}"
  CATALOG="${MA_APP_TARGET_CATALOG:-$CATALOG}"
  [[ -n "$WAREHOUSE_ID" ]] || die "no SQL warehouse available for profile '$PROFILE'"
fi

DBX=(databricks --profile "$PROFILE")

# Helper: run a SQL statement on the warehouse; prints state, fails on non-SUCCEEDED.
run_sql() {
  local stmt="$1"
  local payload state
  payload=$(python3 -c 'import json,sys; print(json.dumps({"warehouse_id":sys.argv[1],"statement":sys.argv[2],"wait_timeout":"30s"}))' "$WAREHOUSE_ID" "$stmt")
  state=$("${DBX[@]}" api post /api/2.0/sql/statements --json "$payload" 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("status") or {}).get("state","UNKNOWN"))')
  [[ "$state" == "SUCCEEDED" ]]
}

# --- 2. Bundle validate ---------------------------------------------------------
log "2/9 Validating bundle"
"${DBX[@]}" bundle validate -t "$TARGET" >/dev/null || die "bundle validate failed"
ok "bundle valid"

# --- 3. Validate catalog / schema / warehouse -----------------------------------
log "3/9 Validating catalog, schema, warehouse"
"${DBX[@]}" warehouses get "$WAREHOUSE_ID" >/dev/null 2>&1 || die "warehouse $WAREHOUSE_ID not found"
ok "warehouse $WAREHOUSE_ID exists"
run_sql "DESCRIBE CATALOG \`$CATALOG\`" || die "catalog $CATALOG not reachable"
ok "catalog $CATALOG reachable"
run_sql "CREATE SCHEMA IF NOT EXISTS \`$CATALOG\`.\`$SCHEMA\`" || die "cannot ensure schema $CATALOG.$SCHEMA"
ok "schema $CATALOG.$SCHEMA ready"

# --- 4. Deploy ------------------------------------------------------------------
log "4/9 Deploying bundle (builds frontend via 'apx build')"
"${DBX[@]}" bundle deploy -t "$TARGET" || die "bundle deploy failed"
ok "bundle deployed"

# --- 5. Start the App -----------------------------------------------------------
log "5/9 Starting the App (required for Databricks Apps after deploy)"
"${DBX[@]}" bundle run "$APP_KEY" -t "$TARGET" || die "failed to start app '$APP_KEY'"
ok "app start issued"

# --- 6. Setup / seed job --------------------------------------------------------
log "6/9 Running setup + seed job"
"${DBX[@]}" bundle run "$SETUP_JOB_KEY" -t "$TARGET" || die "setup job failed"
ok "tables created and synthetic snapshot seeded"

# --- 7. Grant the App service principal least-privilege access ------------------
log "7/9 Granting App service principal UC + warehouse access"
APP_JSON="$("${DBX[@]}" apps get "$APP_NAME" -o json 2>/dev/null)" || die "cannot read app '$APP_NAME'"
SP_ID="$(printf '%s' "$APP_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("service_principal_client_id") or d.get("service_principal_name") or "")')"
[[ -n "$SP_ID" ]] || die "could not resolve App service principal id"
ok "App service principal: $SP_ID"

run_sql "GRANT USE CATALOG ON CATALOG \`$CATALOG\` TO \`$SP_ID\`" || die "grant USE CATALOG failed"
run_sql "GRANT USE SCHEMA ON SCHEMA \`$CATALOG\`.\`$SCHEMA\` TO \`$SP_ID\`" || die "grant USE SCHEMA failed"
run_sql "GRANT SELECT ON SCHEMA \`$CATALOG\`.\`$SCHEMA\` TO \`$SP_ID\`" || die "grant SELECT failed"
run_sql "GRANT MODIFY ON SCHEMA \`$CATALOG\`.\`$SCHEMA\` TO \`$SP_ID\`" || die "grant MODIFY failed"
ok "UC grants applied on $CATALOG.$SCHEMA"

# Warehouse CAN_USE for the App SP (idempotent PATCH adds without removing others).
WH_ACL=$(python3 -c 'import json,sys; print(json.dumps({"access_control_list":[{"service_principal_name":sys.argv[1],"permission_level":"CAN_USE"}]}))' "$SP_ID")
"${DBX[@]}" api patch "/api/2.0/permissions/warehouses/$WAREHOUSE_ID" --json "$WH_ACL" >/dev/null \
  && ok "warehouse CAN_USE granted" \
  || echo "    ! warehouse permission PATCH failed (grant CAN_USE on $WAREHOUSE_ID manually)"

# Let the App SP trigger the dispatcher job (its one-time wrapper uses run_job_task).
DISPATCH_JOB_ID="$("${DBX[@]}" jobs list -o json 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = []
jobs = d if isinstance(d, list) else d.get("jobs", [])
for j in jobs:
    tags = (j.get("settings") or {}).get("tags") or {}
    if tags.get("ma_app") == "dispatch":
        print(j.get("job_id")); break
' 2>/dev/null || true)"
if [[ -n "$DISPATCH_JOB_ID" ]]; then
  JOB_ACL=$(python3 -c 'import json,sys; print(json.dumps({"access_control_list":[{"service_principal_name":sys.argv[1],"permission_level":"CAN_MANAGE_RUN"}]}))' "$SP_ID")
  "${DBX[@]}" api patch "/api/2.0/permissions/jobs/$DISPATCH_JOB_ID" --json "$JOB_ACL" >/dev/null \
    && ok "App SP can trigger dispatcher job $DISPATCH_JOB_ID (scheduling enabled)" \
    || echo "    ! could not grant CAN_MANAGE_RUN on dispatcher job (scheduling may fail)"
else
  echo "    ! dispatcher job (tag ma_app=dispatch) not found — scheduling unavailable"
fi
# NOTE: the App SP must also be entitled to create jobs (+ serverless). In most workspaces
# this is default; if scheduling returns SCHEDULER_UNAVAILABLE, grant the SP those
# entitlements (SCIM) or run scheduled dispatch via the reconcile job only.

# --- 8. Health check ------------------------------------------------------------
log "8/9 Health-checking the App"
APP_URL="$(printf '%s' "$APP_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("url",""))')"
if [[ -n "$APP_URL" ]]; then
  # The App may take a moment to come online after start.
  HEALTH_OK=""
  for i in $(seq 1 20); do
    TOKEN="$("${DBX[@]}" auth token 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || true)"
    if [[ -n "$TOKEN" ]]; then
      BODY="$(curl -fsS -H "Authorization: Bearer $TOKEN" "${APP_URL%/}/health" 2>/dev/null || true)"
      if printf '%s' "$BODY" | grep -q '"status"'; then HEALTH_OK="1"; break; fi
    fi
    sleep 6
  done
  [[ -n "$HEALTH_OK" ]] && ok "health check passed" || echo "    ! health check not confirmed yet; check 'databricks apps logs $APP_NAME'"
else
  echo "    ! App URL not available yet"
fi

# --- 9. Summary -----------------------------------------------------------------
log "9/9 Done"
cat <<EOF

  App name : $APP_NAME
  App URL  : ${APP_URL:-"(run scripts/print_app_url.sh)"}
  Catalog  : $CATALOG.$SCHEMA   (App-owned, synthetic data only)
  Warehouse: $WAREHOUSE_ID

  Demo banner: "Synthetic data / mock activation only"

  Next: open the App URL, review the Dashboard, open the 'Lapsed High-Value'
  audience, create a campaign, preview eligibility, submit -> approve -> dispatch,
  then review metrics and audit history. See README.md §Demo walkthrough.

  Logs: databricks apps logs $APP_NAME --profile $PROFILE
EOF
