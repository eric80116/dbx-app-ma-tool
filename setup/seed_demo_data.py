"""Seed deterministic synthetic demo data.

- Fixed seed 42, reference date 2026-09-29.
- ~2000 synthetic customers; audiences reference them (customer_id unique within an
  audience). All data is clearly SYNTHETIC_SNAPSHOT with example.com emails and
  non-dialable 555-01xx phones. NO real PII.
- Idempotent: clears App-owned tables first (TRUNCATE), then re-seeds. Never touches
  any CMEG source object.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from ma_app.backend.db import Db, Dt, Ts, bulk_insert_values

SEED = 42
REF_DATE = date(2026, 9, 29)
REF_TS = "2026-09-29 09:00:00"
N_CUSTOMERS = 2000

FIRST_NAMES = [
    "Avery", "Blair", "Cameron", "Dakota", "Emerson", "Finley", "Gray", "Harper",
    "Indigo", "Jordan", "Kai", "Logan", "Morgan", "Noel", "Oakley", "Peyton",
    "Quinn", "Reese", "Sage", "Tatum", "Umi", "Val", "Wren", "Xen", "Yael", "Zion",
]
LAST_NAMES = [
    "Adler", "Brooks", "Chen", "Diaz", "Evans", "Ford", "Gupta", "Hughes", "Ito",
    "Jones", "Kim", "Lopez", "Meyer", "Nguyen", "Ortiz", "Patel", "Reyes", "Singh",
    "Tan", "Uddin", "Vega", "Wong", "Xu", "Yamada", "Zhang",
]
COUNTRIES = ["SG", "MY", "ID", "TH", "PH"]
STATES = {
    "SG": ["Central", "East", "North", "West"],
    "MY": ["Selangor", "Penang", "Johor"],
    "ID": ["Jakarta", "West Java", "Bali"],
    "TH": ["Bangkok", "Chiang Mai"],
    "PH": ["Metro Manila", "Cebu"],
}
METROS = ["Metro-A", "Metro-B", "Metro-C", "Metro-D"]
LOYALTY = ["Bronze", "Silver", "Gold", "Platinum"]


def _fmt_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _build_customers(rng: random.Random) -> list[dict]:
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        cust_id = f"CUST-{i:06d}"
        country = rng.choice(COUNTRIES)
        # Account status mix: ~80% Active, ~12% Inactive, ~8% Suspended.
        r = rng.random()
        account_status = "Active" if r < 0.80 else ("Inactive" if r < 0.92 else "Suspended")
        # Preferred channel: App ~45%, SMS ~30%, Email ~25%.
        rc = rng.random()
        preferred = "App" if rc < 0.45 else ("SMS" if rc < 0.75 else "Email")
        # ~5% have missing/invalid phone (SMS invalid-contact skip is demonstrable).
        if rng.random() < 0.05:
            phone = None
        else:
            phone = f"+1-555-01{rng.randint(0, 99):02d}"  # reserved non-dialable range
        join_days = rng.randint(120, 2000)
        loyalty_join = REF_DATE - timedelta(days=join_days)
        created = REF_DATE - timedelta(days=rng.randint(join_days, join_days + 400))
        customers.append(
            {
                "customer_id": cust_id,
                "household_id": f"HH-{(i // 3) + 1:06d}",
                "first_name": rng.choice(FIRST_NAMES),
                "last_name": rng.choice(LAST_NAMES),
                "email": f"user{i:06d}@example.com",
                "phone": phone,
                "country": country,
                "state_province": rng.choice(STATES[country]),
                "metro_area": rng.choice(METROS),
                "loyalty_status": rng.choices(LOYALTY, weights=[40, 30, 20, 10])[0],
                "loyalty_join_date": loyalty_join.isoformat(),
                "account_status": account_status,
                "preferred_channel": preferred,
                "date_created": created.isoformat(),
            }
        )
    return customers


AUDIENCES = [
    {
        "audience_id": "AUD-LAPSED-HIGHVALUE",
        "audience_name": "Lapsed High-Value",
        "segment": "lapsed_highvalue",
        "description": "High-value customers who have lapsed and prefer App Push.",
    },
    {
        "audience_id": "AUD-PUSH-ENGAGED",
        "audience_name": "Push-Engaged",
        "segment": "push_engaged",
        "description": "Customers highly engaged with App Push.",
    },
    {
        "audience_id": "AUD-COUPON-REDEEMERS",
        "audience_name": "Coupon Redeemers",
        "segment": "coupon_redeemers",
        "description": "Customers who frequently redeem coupons.",
    },
]
AUD_VERSION = "v2026.09.29"


def _member_row(cust: dict, audience_id: str, segment: str) -> list:
    return [
        cust["customer_id"], cust["household_id"], cust["first_name"], cust["last_name"],
        cust["email"], cust["phone"], cust["country"], cust["state_province"],
        cust["metro_area"], cust["loyalty_status"], Dt(cust["loyalty_join_date"]),
        cust["account_status"], cust["preferred_channel"], segment,
        Dt(cust["date_created"]), Ts(REF_TS),
        audience_id, AUD_VERSION, "SYNTHETIC_SNAPSHOT", Ts(REF_TS),
    ]


def _batched_insert(db: Db, table: str, cols: list[str], rows: list[list], batch: int = 500) -> None:
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        db.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES {bulk_insert_values(chunk)}"
        )


def seed(db: Db) -> dict[str, int]:  # noqa: C901 - linear seeding script
    rng = random.Random(SEED)
    c = db.config
    counts: dict[str, int] = {}

    # Clean slate for App-owned tables only.
    for t in [
        "app_delivery_event", "app_dispatch_run", "app_campaign_approval",
        "app_campaign", "app_channel_consent", "app_audience_members",
        "app_audience_catalog", "app_offer_catalog", "app_audit_log",
    ]:
        db.execute(f"TRUNCATE TABLE {c.table(t)}")

    customers = _build_customers(rng)

    # --- audience members: each audience references a distinct subset -------------
    member_cols = [
        "customer_id", "household_id", "first_name", "last_name", "email", "phone",
        "country", "state_province", "metro_area", "loyalty_status", "loyalty_join_date",
        "account_status", "preferred_channel", "customer_segment", "date_created",
        "last_updated", "audience_id", "audience_version", "source_type", "loaded_at",
    ]
    member_rows: list[list] = []
    audience_member_counts: dict[str, int] = {}

    # Primary audience: all customers.
    for cust in customers:
        member_rows.append(_member_row(cust, "AUD-LAPSED-HIGHVALUE", "lapsed_highvalue"))
    audience_member_counts["AUD-LAPSED-HIGHVALUE"] = len(customers)

    # Push-engaged: App-preferred customers.
    push = [c2 for c2 in customers if c2["preferred_channel"] == "App"]
    for cust in push:
        member_rows.append(_member_row(cust, "AUD-PUSH-ENGAGED", "push_engaged"))
    audience_member_counts["AUD-PUSH-ENGAGED"] = len(push)

    # Coupon redeemers: a deterministic ~30% sample.
    coupon = [c2 for c2 in customers if rng.random() < 0.30]
    for cust in coupon:
        member_rows.append(_member_row(cust, "AUD-COUPON-REDEEMERS", "coupon_redeemers"))
    audience_member_counts["AUD-COUPON-REDEEMERS"] = len(coupon)

    _batched_insert(db, c.table("app_audience_members"), member_cols, member_rows)
    counts["audience_members"] = len(member_rows)

    # --- audience catalog ----------------------------------------------------------
    cat_cols = [
        "audience_id", "audience_name", "audience_version", "source_type",
        "source_workspace", "source_table", "member_count", "description",
        "created_at", "last_refreshed_at", "is_active",
    ]
    cat_rows = [
        [
            a["audience_id"], a["audience_name"], AUD_VERSION, "SYNTHETIC_SNAPSHOT",
            "app_workspace", c.table("app_audience_members"),
            audience_member_counts[a["audience_id"]], a["description"],
            Ts(REF_TS), Ts(REF_TS), True,
        ]
        for a in AUDIENCES
    ]
    _batched_insert(db, c.table("app_audience_catalog"), cat_cols, cat_rows)
    counts["audiences"] = len(cat_rows)

    # --- consent: one row per distinct customer -----------------------------------
    consent_cols = [
        "customer_id", "app_push_opt_in", "sms_opt_in", "email_opt_in",
        "do_not_contact", "consent_updated_at", "consent_source",
    ]
    consent_rows: list[list] = []
    for cust in customers:
        dnc = rng.random() < 0.05  # >=5% do_not_contact
        push_opt = (rng.random() >= 0.10) and not dnc  # >=10% opted out of push
        sms_opt = (rng.random() >= 0.10) and not dnc  # >=10% opted out of sms
        email_opt = (rng.random() >= 0.15) and not dnc
        consent_rows.append(
            [
                cust["customer_id"], push_opt, sms_opt, email_opt, dnc,
                Ts(REF_TS), "SYNTHETIC_SEED",
            ]
        )
    _batched_insert(db, c.table("app_channel_consent"), consent_cols, consent_rows)
    counts["consent"] = len(consent_rows)

    # --- offers --------------------------------------------------------------------
    offer_cols = [
        "offer_id", "offer_name", "offer_type", "discount_value", "min_spend",
        "valid_from", "valid_to", "eligible_channel", "active_flag", "created_at",
    ]
    valid_from = (REF_DATE - timedelta(days=7)).isoformat()
    valid_to = (REF_DATE + timedelta(days=60)).isoformat()
    offer_rows = [
        ["OFFER-020", "20% Welcome Back", "PERCENT", 20.0, 0.0, Dt(valid_from), Dt(valid_to), "ANY", True, Ts(REF_TS)],
        ["OFFER-015", "15% VIP Appreciation", "PERCENT", 15.0, 50.0, Dt(valid_from), Dt(valid_to), "ANY", True, Ts(REF_TS)],
        ["OFFER-050", "50 SGD Fixed Discount", "FIXED", 50.0, 150.0, Dt(valid_from), Dt(valid_to), "COUPON", True, Ts(REF_TS)],
        ["OFFER-FREESHIP", "Free Shipping", "SHIPPING", 0.0, 0.0, Dt(valid_from), Dt(valid_to), "ANY", True, Ts(REF_TS)],
    ]
    _batched_insert(db, c.table("app_offer_catalog"), offer_cols, offer_rows)
    counts["offers"] = len(offer_rows)

    # --- campaigns (4 required states + 1 completed for dashboard metrics) ---------
    campaign_cols = [
        "campaign_id", "audience_id", "audience_version", "campaign_name", "channel",
        "offer_id", "message_title", "message_body", "deep_link", "scheduled_at",
        "status", "created_by", "approved_by", "created_at", "updated_at",
        "idempotency_key",
    ]
    future = _fmt_ts(datetime(2026, 10, 5, 9, 0, 0))
    seed_campaigns = [
        ["CMP-SEED-DRAFT", "AUD-LAPSED-HIGHVALUE", "Winback Draft", "APP_PUSH", "OFFER-020", "DRAFT", None, None],
        ["CMP-SEED-PENDING", "AUD-PUSH-ENGAGED", "Push Engagement Blast", "APP_PUSH", "OFFER-015", "PENDING_APPROVAL", "seed_creator", None],
        ["CMP-SEED-APPROVED", "AUD-LAPSED-HIGHVALUE", "VIP Winback", "SMS", "OFFER-015", "APPROVED", "seed_creator", "seed_approver"],
        ["CMP-SEED-SCHEDULED", "AUD-COUPON-REDEEMERS", "Coupon Redemption Push", "COUPON", "OFFER-050", "SCHEDULED", "seed_creator", "seed_approver"],
        ["CMP-SEED-COMPLETED", "AUD-PUSH-ENGAGED", "September Push Recap", "APP_PUSH", "OFFER-020", "COMPLETED", "seed_creator", "seed_approver"],
    ]
    campaign_rows: list[list] = []
    for cid, aud, name, channel, offer, status, creator, approver in seed_campaigns:
        sched = Ts(future) if status in {"SCHEDULED"} else Ts(None)
        campaign_rows.append(
            [
                cid, aud, AUD_VERSION, name, channel, offer,
                f"{name}", f"Enjoy {offer} — we miss you!", "app://home/offers",
                sched, status, creator, approver, Ts(REF_TS), Ts(REF_TS),
                f"IDEM-{cid}",
            ]
        )
    _batched_insert(db, c.table("app_campaign"), campaign_cols, campaign_rows)
    counts["campaigns"] = len(campaign_rows)

    # --- approvals for seeded campaigns -------------------------------------------
    appr_cols = ["approval_id", "campaign_id", "action", "actor", "comment", "created_at"]
    appr_rows = [
        ["APR-SEED-1", "CMP-SEED-PENDING", "SUBMITTED", "seed_creator", None, Ts(REF_TS)],
        ["APR-SEED-2", "CMP-SEED-APPROVED", "SUBMITTED", "seed_creator", None, Ts(REF_TS)],
        ["APR-SEED-3", "CMP-SEED-APPROVED", "APPROVED", "seed_approver", "Looks good", Ts(REF_TS)],
        ["APR-SEED-4", "CMP-SEED-SCHEDULED", "SUBMITTED", "seed_creator", None, Ts(REF_TS)],
        ["APR-SEED-5", "CMP-SEED-SCHEDULED", "APPROVED", "seed_approver", "Approved for schedule", Ts(REF_TS)],
        ["APR-SEED-6", "CMP-SEED-COMPLETED", "SUBMITTED", "seed_creator", None, Ts(REF_TS)],
        ["APR-SEED-7", "CMP-SEED-COMPLETED", "APPROVED", "seed_approver", "Approved", Ts(REF_TS)],
    ]
    _batched_insert(db, c.table("app_campaign_approval"), appr_cols, appr_rows)
    counts["approvals"] = len(appr_rows)

    # --- seed dispatch run + delivery events for the completed campaign -----------
    # Clearly separated from live runs by the RUN-SEED prefix.
    run_id = "RUN-SEED-COMPLETED"
    run_cols = [
        "dispatch_run_id", "campaign_id", "started_at", "finished_at", "status",
        "requested_count", "eligible_count", "success_count", "failure_count",
        "skipped_count", "error_message", "idempotency_key",
    ]
    ev_cols = [
        "delivery_event_id", "dispatch_run_id", "campaign_id", "customer_id", "channel",
        "event_type", "event_ts", "provider_message_id", "failure_reason", "created_at",
    ]
    # Build a deterministic funnel over the push-engaged, opted-in, active customers.
    ev_rng = random.Random(SEED + 7)
    sample = [c2 for c2 in push if c2["account_status"] == "Active"][:600]
    ev_rows: list[list] = []
    sent = delivered = opened = clicked = failed = 0
    base = datetime(2026, 9, 29, 9, 0, 0)
    for idx, cust in enumerate(sample, start=1):
        cid = cust["customer_id"]
        msg = f"MOCK-PUSH-{idx:06d}"
        ev_rows.append(["EVT-S-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "REQUESTED", Ts(_fmt_ts(base)), msg, None, Ts(REF_TS)])
        if ev_rng.random() > 0.96:
            failed += 1
            ev_rows.append(["EVT-F-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "FAILED", Ts(_fmt_ts(base)), msg, "mock_transient", Ts(REF_TS)])
            continue
        sent += 1
        ev_rows.append(["EVT-SE-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "SENT", Ts(_fmt_ts(base)), msg, None, Ts(REF_TS)])
        if ev_rng.random() <= 0.93:
            delivered += 1
            ev_rows.append(["EVT-D-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "DELIVERED", Ts(_fmt_ts(base + timedelta(seconds=30))), msg, None, Ts(REF_TS)])
            if ev_rng.random() <= 0.42:
                opened += 1
                ev_rows.append(["EVT-O-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "OPENED", Ts(_fmt_ts(base + timedelta(seconds=120))), msg, None, Ts(REF_TS)])
                if ev_rng.random() <= 0.28:
                    clicked += 1
                    ev_rows.append(["EVT-C-{:06d}".format(idx), run_id, "CMP-SEED-COMPLETED", cid, "APP_PUSH", "CLICKED", Ts(_fmt_ts(base + timedelta(seconds=180))), msg, None, Ts(REF_TS)])

    run_rows = [[
        run_id, "CMP-SEED-COMPLETED", Ts(_fmt_ts(base)), Ts(_fmt_ts(base + timedelta(minutes=5))),
        "COMPLETED", len(sample), sent + failed, sent, failed, 0, None, "IDEM-CMP-SEED-COMPLETED",
    ]]
    _batched_insert(db, c.table("app_dispatch_run"), run_cols, run_rows)
    _batched_insert(db, c.table("app_delivery_event"), ev_cols, ev_rows)
    counts["dispatch_runs"] = 1
    counts["delivery_events"] = len(ev_rows)

    # --- audit trail for seeded campaigns -----------------------------------------
    audit_cols = ["audit_id", "actor", "action", "resource_type", "resource_id", "metadata_json", "created_at"]
    audit_rows = [
        [f"AUD-SEED-{i}", "seed_creator", "CREATE", "campaign", cid_[0], "{}", Ts(REF_TS)]
        for i, cid_ in enumerate(seed_campaigns, start=1)
    ]
    audit_rows.append(["AUD-SEED-D", "seed_approver", "DISPATCH", "campaign", "CMP-SEED-COMPLETED", '{"run_id": "RUN-SEED-COMPLETED"}', Ts(REF_TS)])
    _batched_insert(db, c.table("app_audit_log"), audit_cols, audit_rows)
    counts["audit"] = len(audit_rows)

    return counts


def main() -> None:
    from _bootstrap import get_db  # type: ignore

    db = get_db()
    counts = seed(db)
    print("Seeded synthetic demo data (source_type=SYNTHETIC_SNAPSHOT):")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
