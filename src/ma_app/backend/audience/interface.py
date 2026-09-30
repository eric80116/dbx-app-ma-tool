"""Audience access boundary.

The App **consumes** an audience produced by CustomerLake Campaign Agents; it never
recreates the segmentation logic. For demo #1 the audience is a local synthetic
snapshot in this workspace. This `Protocol` is the seam that a future supported
mechanism (shared table, Delta Sharing, official API, reverse-ETL destination) can
implement without changing the rest of the App.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import AudienceDetail, AudienceMember, AudienceSummary


@runtime_checkable
class AudienceRepository(Protocol):
    def list_audiences(self) -> list[AudienceSummary]: ...

    def get_audience(
        self, audience_id: str, version: str | None = None
    ) -> AudienceDetail: ...

    def get_members(
        self, audience_id: str, version: str | None = None
    ) -> list[AudienceMember]: ...


class AudienceNotFound(Exception):
    def __init__(self, audience_id: str):
        super().__init__(f"Audience '{audience_id}' not found")
        self.audience_id = audience_id


class AudienceSourceUnavailable(Exception):
    """Raised when a configured shared audience source cannot be reached/authorized.

    Per the architecture rules, the App must fail clearly rather than silently
    falling back to a different audience.
    """
