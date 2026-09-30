#!/usr/bin/env bash
# Print the deployed App URL.
# Usage: scripts/print_app_url.sh [--profile <profile>]
set -euo pipefail

PROFILE="${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
APP_NAME="ma-app"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

URL="$(databricks --profile "$PROFILE" apps get "$APP_NAME" -o json 2>/dev/null \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("url",""))')"

if [[ -z "$URL" ]]; then
  echo "App '$APP_NAME' not found or has no URL yet (has it been deployed?)." >&2
  exit 1
fi
echo "$URL"
