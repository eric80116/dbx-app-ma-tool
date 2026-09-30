#!/usr/bin/env bash
#
# Safe teardown of App-owned resources ONLY.
#
# Without --confirm this is a DRY RUN: it prints exactly what would be deleted and exits
# without making any change.
#
# Guarantees:
#   * Drops only the explicit ALLOWLIST of App-owned tables in <catalog>.<schema>.
#   * Never uses DROP SCHEMA CASCADE unless the schema is verified to have been created
#     solely by this bundle (it is not, by default -> we drop table-by-table).
#   * Removes the App + jobs via `databricks bundle destroy`.
#   * NEVER touches CMEG source tables, CustomerLake audience views, any catalog other
#     than the configured App catalog, or any external shared audience table.
#
# Usage: scripts/teardown.sh [--confirm] [--drop-schema] [--profile <profile>] [-t <target>]
set -euo pipefail

PROFILE="${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
TARGET="dev"
CONFIRM=""
DROP_SCHEMA=""

# Config (overridable via env).
CATALOG="${MA_APP_TARGET_CATALOG:-ma_app_demo}"
SCHEMA="${MA_APP_APP_SCHEMA:-ma_app}"
WAREHOUSE_ID="${MA_APP_WAREHOUSE_ID:-}"

# Hard guard: the ONLY catalog this script may ever write to.
readonly ALLOWED_CATALOG="ma_app_demo"
readonly APP_NAME="ma-app"

# ALLOWLIST of App-owned tables. Nothing outside this list is ever dropped.
APP_TABLES=(
  app_delivery_event
  app_dispatch_run
  app_campaign_approval
  app_campaign
  app_channel_consent
  app_audience_members
  app_audience_catalog
  app_offer_catalog
  app_audit_log
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm) CONFIRM="1"; shift ;;
    --drop-schema) DROP_SCHEMA="1"; shift ;;
    --profile) PROFILE="$2"; shift 2 ;;
    -t|--target) TARGET="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m    ✗ %s\033[0m\n' "$*" >&2; exit 1; }

DBX=(databricks --profile "$PROFILE")

run_sql() {
  local stmt="$1" state
  local payload
  payload=$(python3 -c 'import json,sys; print(json.dumps({"warehouse_id":sys.argv[1],"statement":sys.argv[2],"wait_timeout":"30s"}))' "$WAREHOUSE_ID" "$stmt")
  state=$("${DBX[@]}" api post /api/2.0/sql/statements --json "$payload" 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("status") or {}).get("state","UNKNOWN"))')
  [[ "$state" == "SUCCEEDED" ]]
}

# One-time dispatch wrapper jobs the App created dynamically. ALLOWLIST: only jobs whose
# name starts with "ma-app-dispatch-" AND carry tag ma_app=dispatch_wrapper. "id<TAB>name".
wrapper_jobs() {
  "${DBX[@]}" jobs list -o json 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = []
jobs = d if isinstance(d, list) else d.get("jobs", [])
for j in jobs:
    s = j.get("settings") or {}
    name = s.get("name", "") or ""
    tags = s.get("tags") or {}
    if name.startswith("ma-app-dispatch-") and tags.get("ma_app") == "dispatch_wrapper":
        print("%s\t%s" % (j.get("job_id"), name))
' 2>/dev/null || true
}

# --- Ownership verification (fail-closed) ---------------------------------------
log "Verifying teardown target is App-owned"
[[ "$CATALOG" == "$ALLOWED_CATALOG" ]] || die "Refusing: configured catalog '$CATALOG' is not the App-owned '$ALLOWED_CATALOG'. Teardown aborted."
[[ -n "$SCHEMA" && "$SCHEMA" != "default" ]] || die "Refusing: unsafe schema '$SCHEMA'."
echo "    target schema: $CATALOG.$SCHEMA (allowed)"

# Confirm the schema exists and is reachable before proceeding.
run_sql "DESCRIBE SCHEMA \`$CATALOG\`.\`$SCHEMA\`" || die "Cannot verify schema $CATALOG.$SCHEMA ownership/existence. Aborting."

FQ_TABLES=()
for t in "${APP_TABLES[@]}"; do FQ_TABLES+=("$CATALOG.$SCHEMA.$t"); done

# --- Dry run --------------------------------------------------------------------
if [[ -z "$CONFIRM" ]]; then
  log "DRY RUN (no --confirm) — nothing will be deleted"
  echo "Would DROP the following App-owned tables:"
  for t in "${FQ_TABLES[@]}"; do echo "    - $t"; done
  [[ -n "$DROP_SCHEMA" ]] && echo "Would DROP SCHEMA $CATALOG.$SCHEMA (only after verifying it is bundle-exclusive)"
  echo "Would DELETE these one-time dispatch wrapper jobs (name ma-app-dispatch-* + tag):"
  while IFS=$'\t' read -r jid jname; do [[ -n "$jid" ]] && echo "    - $jid  ($jname)"; done <<< "$(wrapper_jobs)"
  echo "Would run: databricks bundle destroy -t $TARGET   (removes App '$APP_NAME' + jobs)"
  echo
  echo "NEVER touched: CMEG source tables, CustomerLake audience views, any catalog"
  echo "other than $ALLOWED_CATALOG, any external shared audience table."
  echo
  echo "Re-run with --confirm to execute."
  exit 0
fi

# --- Execute --------------------------------------------------------------------
log "Dropping App-owned tables (allowlist only)"
dropped=0
for t in "${APP_TABLES[@]}"; do
  if run_sql "DROP TABLE IF EXISTS \`$CATALOG\`.\`$SCHEMA\`.\`$t\`"; then
    echo "    dropped $CATALOG.$SCHEMA.$t"; dropped=$((dropped+1))
  else
    echo "    ! could not drop $CATALOG.$SCHEMA.$t (may not exist)"
  fi
done

if [[ -n "$DROP_SCHEMA" ]]; then
  log "Dropping schema (RESTRICT — refuses if unknown objects remain)"
  # RESTRICT (not CASCADE) so we never blast objects we did not create.
  run_sql "DROP SCHEMA IF EXISTS \`$CATALOG\`.\`$SCHEMA\` RESTRICT" \
    && echo "    dropped schema $CATALOG.$SCHEMA" \
    || echo "    ! schema not dropped (objects remain / not empty) — left intact"
fi

log "Deleting one-time dispatch wrapper jobs (allowlist: ma-app-dispatch-* + tag)"
wrapper_removed=0
while IFS=$'\t' read -r jid jname; do
  [[ -n "$jid" ]] || continue
  if "${DBX[@]}" jobs delete "$jid" >/dev/null 2>&1; then
    echo "    deleted job $jid ($jname)"; wrapper_removed=$((wrapper_removed+1))
  else
    echo "    ! could not delete job $jid ($jname)"
  fi
done <<< "$(wrapper_jobs)"

log "Destroying bundle resources (App + jobs)"
"${DBX[@]}" bundle destroy -t "$TARGET" --auto-approve || die "bundle destroy failed"

log "Teardown summary"
echo "    tables dropped : $dropped / ${#FQ_TABLES[@]}"
echo "    wrapper jobs    : $wrapper_removed deleted"
echo "    bundle resources: destroyed (App + jobs)"
echo "    catalogs touched: $CATALOG only"
echo "    CMEG source data: untouched"
