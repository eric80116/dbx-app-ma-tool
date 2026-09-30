#!/usr/bin/env bash
# Run the test suite. Unit tests always run; integration + acceptance run only when a
# SQL warehouse is configured (MA_APP_WAREHOUSE_ID, e.g. via .env). JUnit XML is written
# to artifacts/test-results/.
set -euo pipefail
cd "$(dirname "$0")/.."

RESULTS="artifacts/test-results"
mkdir -p "$RESULTS"

# Load .env so MA_APP_WAREHOUSE_ID is available for live tests.
if [[ -f .env ]]; then
  set -a; # shellcheck disable=SC1091
  source .env; set +a
fi

echo "==> Unit tests"
uv run pytest tests/unit -m unit --junitxml="$RESULTS/unit.xml" -q

if [[ -n "${MA_APP_WAREHOUSE_ID:-}" ]]; then
  echo "==> Integration tests (live warehouse ${MA_APP_WAREHOUSE_ID})"
  uv run pytest tests/integration -m integration --junitxml="$RESULTS/integration.xml" -q
  echo "==> Acceptance tests"
  uv run pytest tests/acceptance -m acceptance --junitxml="$RESULTS/acceptance.xml" -q
else
  echo "==> Skipping integration + acceptance (MA_APP_WAREHOUSE_ID not set)"
fi

echo "All requested tests passed. Results in $RESULTS/"
