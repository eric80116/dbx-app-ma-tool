"""Job entry: dispatch a single campaign (called by the one-time wrapper job).

Reuses CampaignService.dispatch() — same mock providers, guardrails, and idempotency as the
interactive path. Configuration + campaign_id come from argv / job parameters.

Usage: python run_dispatch.py --campaign-id CMP-... [--catalog C --schema S --warehouse-id W]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    candidates: list[Path] = []
    try:
        candidates.append(Path(__file__).resolve().parent.parent)  # type: ignore[name-defined]
    except NameError:
        pass
    if sys.argv and sys.argv[0]:
        p = Path(sys.argv[0]).resolve()
        candidates.extend([p.parent.parent, p.parent])
    candidates.extend([Path.cwd(), Path.cwd().parent])
    for c in candidates:
        if (c / "src" / "ma_app").exists():
            return c
    return candidates[0] if candidates else Path.cwd()


ROOT = _repo_root()
for p in (str(ROOT / "src"), str(ROOT / "setup")):
    if p not in sys.path:
        sys.path.insert(0, p)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--catalog", default=os.environ.get("MA_APP_TARGET_CATALOG"))
    parser.add_argument("--schema", default=os.environ.get("MA_APP_APP_SCHEMA"))
    parser.add_argument("--warehouse-id", default=os.environ.get("MA_APP_WAREHOUSE_ID"))
    args = parser.parse_args()
    if args.catalog:
        os.environ["MA_APP_TARGET_CATALOG"] = args.catalog
    if args.schema:
        os.environ["MA_APP_APP_SCHEMA"] = args.schema
    if args.warehouse_id:
        os.environ["MA_APP_WAREHOUSE_ID"] = args.warehouse_id

    from _bootstrap import get_db  # type: ignore
    from ma_app.backend.services import CampaignService

    db = get_db()
    svc = CampaignService(db)
    campaign = svc.repo.get_campaign(args.campaign_id)
    if campaign is None:
        raise SystemExit(f"Campaign {args.campaign_id} not found — nothing to dispatch.")
    run = svc.dispatch(campaign, actor="scheduler")
    print(
        f"Dispatched {args.campaign_id}: run={run.dispatch_run_id} status={run.status} "
        f"success={run.success_count} failure={run.failure_count} skipped={run.skipped_count}"
    )


if __name__ == "__main__":
    main()
