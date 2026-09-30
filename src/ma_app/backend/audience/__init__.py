"""Audience access layer (replaceable boundary)."""

from __future__ import annotations

from ..db import Db
from .interface import (
    AudienceNotFound,
    AudienceRepository,
    AudienceSourceUnavailable,
)
from .local_snapshot import LocalSnapshotAudienceRepository
from .shared_table import SharedTableAudienceRepository

__all__ = [
    "AudienceRepository",
    "AudienceNotFound",
    "AudienceSourceUnavailable",
    "LocalSnapshotAudienceRepository",
    "SharedTableAudienceRepository",
    "get_audience_repository",
]


def get_audience_repository(db: Db) -> AudienceRepository:
    """Select the audience repository based on configured source mode."""
    mode = (db.config.audience_source_mode or "local_snapshot").strip().lower()
    if mode == "shared_table":
        return SharedTableAudienceRepository(db)
    if mode == "local_snapshot":
        return LocalSnapshotAudienceRepository(db)
    raise ValueError(
        f"Unknown MA_APP_AUDIENCE_SOURCE_MODE '{mode}'. "
        f"Expected 'local_snapshot' or 'shared_table'."
    )
