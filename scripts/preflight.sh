#!/usr/bin/env bash
#
# Preflight: check prerequisites, AUTO-DETECT resource values from the workspace, and
# fall back to INTERACTIVE prompts for anything that can't be resolved. Writes the result
# to .env (gitignored) so `apx dev`, the tests, and scripts/deploy.sh all pick it up.
#
# Resolves:
#   - Databricks profile          (arg / existing .env / DEFAULT)
#   - SQL warehouse id            (existing .env -> single workspace warehouse ->
#                                   interactive pick -> prompt)
#   - target catalog / app schema (existing .env -> defaults, confirmed interactively)
#
# Usage: scripts/preflight.sh [--profile <p>] [--refresh] [--non-interactive]
set -euo pipefail
cd "$(dirname "$0")/.."

REFRESH=""
INTERACTIVE="1"
[ -t 0 ] || INTERACTIVE=""   # no TTY -> never block on prompts
ARG_PROFILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) ARG_PROFILE="$2"; shift 2 ;;
    --refresh) REFRESH="1"; shift ;;
    --non-interactive) INTERACTIVE=""; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()  { printf '\033[1;32m    ✓ %s\033[0m\n' "$*"; }
warn(){ printf '\033[1;33m    ! %s\033[0m\n' "$*"; }
die() { printf '\033[1;31m    ✗ %s\033[0m\n' "$*" >&2; exit 1; }

# Load any existing values so re-running is idempotent (unless --refresh).
if [[ -f .env ]]; then set -a; # shellcheck disable=SC1091
  source .env; set +a; fi

# Defaults (overridable; used only when nothing else provides a value).
PROFILE="${ARG_PROFILE:-${DATABRICKS_CONFIG_PROFILE:-DEFAULT}}"
CATALOG="${MA_APP_TARGET_CATALOG:-ma_app_demo}"
SCHEMA="${MA_APP_APP_SCHEMA:-ma_app}"
REVEAL="${MA_APP_REVEAL_PII_ALLOWED:-true}"
MODE="${MA_APP_AUDIENCE_SOURCE_MODE:-local_snapshot}"
WAREHOUSE_ID="${MA_APP_WAREHOUSE_ID:-}"

ask() {  # ask <prompt> <default> -> echoes chosen value
  local prompt="$1" default="$2" ans
  if [[ -n "$INTERACTIVE" ]]; then
    read -r -p "    $prompt [$default]: " ans || true
    echo "${ans:-$default}"
  else
    echo "$default"
  fi
}

# --- 1. CLI + auth --------------------------------------------------------------
log "1/4 Checking Databricks CLI + auth"
command -v databricks >/dev/null 2>&1 || die "databricks CLI not found"
if [[ -z "$ARG_PROFILE" && -z "${DATABRICKS_CONFIG_PROFILE:-}" && -n "$INTERACTIVE" ]]; then
  PROFILE="$(ask "Databricks profile" "$PROFILE")"
fi
DBX=(databricks --profile "$PROFILE")
"${DBX[@]}" current-user me >/dev/null 2>&1 || die "not authenticated for profile '$PROFILE' (try: databricks auth login --profile $PROFILE)"
ok "authenticated as profile '$PROFILE'"

# --- 2. Warehouse: auto-detect, else pick, else prompt --------------------------
log "2/4 Resolving SQL warehouse"
if [[ -n "$WAREHOUSE_ID" && -z "$REFRESH" ]]; then
  ok "using configured warehouse $WAREHOUSE_ID (--refresh to re-detect)"
else
  # TSV of "id<TAB>name<TAB>state" (portable — no mapfile; bash 3.2 friendly).
  WH_TSV="$("${DBX[@]}" warehouses list -o json 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = []
whs = d if isinstance(d, list) else d.get("warehouses", [])
for w in whs:
    print("%s\t%s\t%s" % (w.get("id", ""), w.get("name", ""), w.get("state", "")))
' 2>/dev/null || true)"

  WH_IDS=(); WH_NAMES=(); WH_STATES=()
  while IFS=$'\t' read -r _id _name _state; do
    [[ -n "$_id" ]] || continue
    WH_IDS+=("$_id"); WH_NAMES+=("$_name"); WH_STATES+=("$_state")
  done <<< "$WH_TSV"

  count=${#WH_IDS[@]}
  if [[ "$count" -eq 0 ]]; then
    warn "no warehouses found for this profile"
    WAREHOUSE_ID="$(ask "Enter SQL warehouse id" "${WAREHOUSE_ID:-}")"
    [[ -n "$WAREHOUSE_ID" ]] || die "a SQL warehouse id is required"
  elif [[ "$count" -eq 1 ]]; then
    WAREHOUSE_ID="${WH_IDS[0]}"
    ok "auto-detected the only warehouse: ${WH_NAMES[0]} ($WAREHOUSE_ID)"
  else
    echo "    Multiple warehouses found:"
    for ((i = 0; i < count; i++)); do
      printf '      %d) %s  [%s]\n' "$((i + 1))" "${WH_NAMES[$i]}" "${WH_STATES[$i]}"
    done
    if [[ -n "$INTERACTIVE" ]]; then
      sel="$(ask "Select warehouse number" "1")"
      WAREHOUSE_ID="${WH_IDS[$((sel - 1))]}"
    else
      WAREHOUSE_ID="${WH_IDS[0]}"
      warn "non-interactive: defaulting to first warehouse $WAREHOUSE_ID"
    fi
    ok "using warehouse $WAREHOUSE_ID"
  fi
fi

# --- 3. Catalog / schema (defaults, confirmed) ----------------------------------
log "3/4 Resolving catalog + schema"
CATALOG="$(ask "App catalog" "$CATALOG")"
SCHEMA="$(ask "App schema" "$SCHEMA")"
# Best-effort existence check (non-fatal — deploy.sh creates the schema).
if "${DBX[@]}" catalogs get "$CATALOG" >/dev/null 2>&1; then
  ok "catalog '$CATALOG' exists"
else
  warn "catalog '$CATALOG' not found yet — scripts/deploy.sh will create it (needs default storage)"
fi

# --- 4. Write .env --------------------------------------------------------------
log "4/4 Writing .env"
cat > .env <<EOF
# Generated by scripts/preflight.sh — local, non-secret config (gitignored).
DATABRICKS_CONFIG_PROFILE=$PROFILE

MA_APP_TARGET_CATALOG=$CATALOG
MA_APP_APP_SCHEMA=$SCHEMA
MA_APP_WAREHOUSE_ID=$WAREHOUSE_ID
MA_APP_AUDIENCE_SOURCE_MODE=$MODE
MA_APP_REVEAL_PII_ALLOWED=$REVEAL

# Used by the APX sql addon.
DATABRICKS_SQL_WAREHOUSE_ID=$WAREHOUSE_ID
EOF
ok "wrote .env"

cat <<EOF

  profile   : $PROFILE
  warehouse : $WAREHOUSE_ID
  catalog   : $CATALOG.$SCHEMA
  mode      : $MODE

  Next: ./scripts/deploy.sh   (or: apx dev start for local development)
EOF
