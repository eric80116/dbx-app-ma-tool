"""Shared bootstrap for setup/seed scripts (run locally or as a Databricks job task).

Builds a `Db` from a default-auth WorkspaceClient plus AppConfig. Works locally via the
`DATABRICKS_CONFIG_PROFILE` in `.env`, and on Databricks via the job's identity.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when run as a plain script.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from databricks.sdk import WorkspaceClient  # noqa: E402

from ma_app.backend.core._config import AppConfig  # noqa: E402
from ma_app.backend.db import Db  # noqa: E402


def get_db() -> Db:
    config = AppConfig()  # type: ignore[call-arg]
    if not config.warehouse_id:
        raise SystemExit(
            "MA_APP_WAREHOUSE_ID is not set. Configure it via .env or bundle variables."
        )
    return Db(WorkspaceClient(), config)
