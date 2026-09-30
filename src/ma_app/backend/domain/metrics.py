"""Metric calculations (pure). Rates are computed from counts; the counts themselves
are always read from Delta tables, never hard-coded."""

from __future__ import annotations

from ..models import CampaignMetrics


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def compute_metrics(campaign_id: str, counts: dict[str, int]) -> CampaignMetrics:
    requested = counts.get("REQUESTED", 0)
    skipped = (
        counts.get("SKIPPED_NO_CONSENT", 0)
        + counts.get("SKIPPED_INACTIVE", 0)
        + counts.get("SKIPPED_INVALID_CONTACT", 0)
    )
    sent = counts.get("SENT", 0)
    delivered = counts.get("DELIVERED", 0)
    opened = counts.get("OPENED", 0)
    clicked = counts.get("CLICKED", 0)
    redeemed = counts.get("REDEEMED", 0)
    failed = counts.get("FAILED", 0)
    eligible = sent + failed  # attempted sends == eligible members

    return CampaignMetrics(
        campaign_id=campaign_id,
        requested=requested,
        eligible=eligible,
        skipped=skipped,
        sent=sent,
        delivered=delivered,
        opened=opened,
        clicked=clicked,
        redeemed=redeemed,
        failed=failed,
        failure_rate=_rate(failed, eligible),
        open_rate=_rate(opened, delivered),
        click_through_rate=_rate(clicked, delivered),
        redemption_rate=_rate(redeemed, delivered),
    )
