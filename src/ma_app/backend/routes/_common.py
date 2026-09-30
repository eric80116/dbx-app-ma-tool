"""Shared helpers for route modules."""

from __future__ import annotations

from ..core._headers import DatabricksAppsHeaders


def actor_from(headers: DatabricksAppsHeaders) -> str:
    """Best-effort acting-user identity for audit/approval records.

    In a deployed Databricks App these headers are populated per request. Locally they
    are absent, so we fall back to a clearly-synthetic demo identity.
    """
    return headers.user_email or headers.user_name or "demo_user"
