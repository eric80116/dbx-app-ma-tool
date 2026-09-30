"""Shared pytest fixtures.

Unit tests use pure logic + fakes (no DB). Integration/acceptance tests need a live
warehouse; they are skipped automatically when MA_APP_WAREHOUSE_ID is not configured.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for p in (str(SRC), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Load .env for local integration runs (best-effort).
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:  # pragma: no cover
    pass


def _warehouse_configured() -> bool:
    return bool(os.environ.get("MA_APP_WAREHOUSE_ID"))


requires_warehouse = pytest.mark.skipif(
    not _warehouse_configured(),
    reason="MA_APP_WAREHOUSE_ID not set; skipping live-warehouse test.",
)


@pytest.fixture(scope="session")
def db():
    """A live Db (App service principal via local profile)."""
    if not _warehouse_configured():
        pytest.skip("MA_APP_WAREHOUSE_ID not set")
    from databricks.sdk import WorkspaceClient

    from ma_app.backend.core._config import AppConfig
    from ma_app.backend.db import Db

    return Db(WorkspaceClient(), AppConfig())  # type: ignore[call-arg]


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient over the real app (uses the live warehouse)."""
    if not _warehouse_configured():
        pytest.skip("MA_APP_WAREHOUSE_ID not set")
    from fastapi.testclient import TestClient

    from ma_app.backend.app import app

    with TestClient(app) as c:
        yield c
