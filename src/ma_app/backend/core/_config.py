from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..._metadata import app_name, app_slug

# --- Config ---

project_root = Path(__file__).parent.parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)

    # --- MA app configuration (all overridable via MA_APP_* env / bundle vars) ---
    # NOTE: nothing workspace-specific is hard-coded in source. These defaults are
    # development conveniences only and are overridden by the bundle at deploy time.
    target_catalog: str = Field(
        default="ma_app_demo",
        description="Catalog holding App-owned Delta tables.",
    )
    app_schema: str = Field(
        default="ma_app",
        description="Schema for App-owned operational tables.",
    )
    warehouse_id: str = Field(
        default="",
        description="SQL Warehouse id. Empty -> auto-resolved from the workspace.",
    )
    warehouse_name: str = Field(
        default="",
        description="Optional warehouse name to prefer when auto-resolving.",
    )
    audience_source_mode: str = Field(
        default="local_snapshot",
        description="'local_snapshot' or 'shared_table'.",
    )
    audience_table_override: str = Field(
        default="",
        description="Fully-qualified audience table/view. Empty -> derived default.",
    )
    reveal_pii_allowed: bool = Field(
        default=True,
        description="Whether the demo-only 'reveal contact values' toggle is permitted.",
    )
    scheduler_enabled: bool = Field(
        default=True,
        description="Enable real time-based scheduling via one-time Databricks jobs.",
    )
    dispatch_job_tag: str = Field(
        default="dispatch",
        description="Value of the 'ma_app' tag identifying the dispatcher job.",
    )

    @property
    def schema_fqn(self) -> str:
        return f"{self.target_catalog}.{self.app_schema}"

    def table(self, name: str) -> str:
        """Fully-qualified name of an App-owned table."""
        return f"{self.target_catalog}.{self.app_schema}.{name}"

    @property
    def audience_table(self) -> str:
        return self.audience_table_override or self.table("app_audience_members")

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")

    def __hash__(self) -> int:
        return hash(self.app_name)


# --- Logger ---

logger = logging.getLogger(app_name)
