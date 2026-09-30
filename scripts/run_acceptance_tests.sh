#!/usr/bin/env bash
# Run the acceptance suite (one test per customer requirement) and render a human-readable
# Markdown checklist alongside the JUnit XML in artifacts/test-results/.
set -euo pipefail
cd "$(dirname "$0")/.."

RESULTS="artifacts/test-results"
mkdir -p "$RESULTS"

if [[ -f .env ]]; then
  set -a; # shellcheck disable=SC1091
  source .env; set +a
fi

if [[ -z "${MA_APP_WAREHOUSE_ID:-}" ]]; then
  echo "MA_APP_WAREHOUSE_ID not set — acceptance tests require a live warehouse." >&2
  exit 2
fi

echo "==> Acceptance tests"
set +e
uv run pytest tests/acceptance -m acceptance --junitxml="$RESULTS/acceptance.xml" -v
status=$?
set -e

echo "==> Rendering Markdown report"
uv run python tests/_report.py "$RESULTS/acceptance.xml" "$RESULTS/acceptance-summary.md" "MA App Acceptance Report"

echo "Report: $RESULTS/acceptance-summary.md"
exit $status
