"""Audience and offer read endpoints (App consumes the audience snapshot)."""

from __future__ import annotations

from ..audience import get_audience_repository
from ..core import Dependencies, create_router
from ..db import DbDependency
from ..models import AudienceDetail, AudienceMember, AudienceSummary, OfferOut
from ..repositories import AppRepository

router = create_router()


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, _, domain = email.partition("@")
    head = local[0] if local else "*"
    return f"{head}***@{domain}"


def _mask_phone(phone: str | None) -> str | None:
    if not phone:
        return phone
    digits = [c for c in phone if c.isdigit()]
    if len(digits) < 4:
        return "****"
    return "***-***-" + "".join(digits[-4:])


def _mask_member(m: AudienceMember) -> AudienceMember:
    return m.model_copy(
        update={"email": _mask_email(m.email), "phone": _mask_phone(m.phone)}
    )


@router.get(
    "/audiences", response_model=list[AudienceSummary], operation_id="listAudiences"
)
def list_audiences(db: DbDependency):
    return get_audience_repository(db).list_audiences()


@router.get(
    "/audiences/{audience_id}",
    response_model=AudienceDetail,
    operation_id="getAudience",
)
def get_audience(audience_id: str, db: DbDependency, version: str | None = None):
    return get_audience_repository(db).get_audience(audience_id, version)


@router.get(
    "/audiences/{audience_id}/members",
    response_model=list[AudienceMember],
    operation_id="listAudienceMembers",
)
def list_audience_members(
    audience_id: str,
    db: DbDependency,
    config: Dependencies.Config,
    version: str | None = None,
    limit: int = 50,
    reveal: bool = False,
):
    members = get_audience_repository(db).get_members(audience_id, version)
    members = members[: max(0, limit)] if limit else members
    # Mask contact values by default. Only reveal when both the request opts in AND
    # the deployment permits the demo-only reveal control.
    if reveal and config.reveal_pii_allowed:
        return members
    return [_mask_member(m) for m in members]


@router.get("/offers", response_model=list[OfferOut], operation_id="listOffers")
def list_offers(db: DbDependency, active_only: bool = False):
    return AppRepository(db).list_offers(active_only=active_only)
