"""Job entry: reconcile scheduled campaigns (the periodic checking job).

Two responsibilities:
  (a) Safety net — dispatch any SCHEDULED campaign whose time has passed but which has no
      completed run (e.g. the one-time wrapper failed or was removed).
  (b) Cleanup — delete spent one-time wrapper jobs (name `ma-app-dispatch-*`, tag ma_app)
      whose campaign is now in a terminal state or no longer SCHEDULED.

Only ever touches App-owned tables and `ma-app-dispatch-*` jobs.
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
    parser.add_argument("--catalog", default=os.environ.get("MA_APP_TARGET_CATALOG"))
    parser.add_argument("--schema", default=os.environ.get("MA_APP_APP_SCHEMA"))
    parser.add_argument("--warehouse-id", default=os.environ.get("MA_APP_WAREHOUSE_ID"))
    args = parser.parse_args()
    for k, v in [
        ("MA_APP_TARGET_CATALOG", args.catalog),
        ("MA_APP_APP_SCHEMA", args.schema),
        ("MA_APP_WAREHOUSE_ID", args.warehouse_id),
    ]:
        if v:
            os.environ[k] = v

    from _bootstrap import get_db  # type: ignore
    from ma_app.backend.scheduler import (
        WRAPPER_NAME_PREFIX,
        WRAPPER_TAG_KEY,
        WRAPPER_TAG_VALUE,
    )
    from ma_app.backend.services import CampaignService

    db = get_db()
    svc = CampaignService(db)
    repo = svc.repo
    c = db.config

    # (a) Safety net: SCHEDULED + past due + no completed run.
    due = db.execute(
        f"SELECT campaign_id FROM {c.table('app_campaign')} "
        f"WHERE status = 'SCHEDULED' AND scheduled_at IS NOT NULL "
        f"AND scheduled_at <= current_timestamp()"
    )
    dispatched = 0
    for row in due:
        cid = row["campaign_id"]
        if repo.find_completed_run_by_key(f"IDEM-{cid}") is not None:
            continue
        campaign = repo.get_campaign(cid)
        if campaign is None:
            continue
        try:
            svc.dispatch(campaign, actor="reconcile")
            dispatched += 1
            print(f"[safety-net] dispatched overdue campaign {cid}")
        except Exception as exc:  # noqa: BLE001
            print(f"[safety-net] could not dispatch {cid}: {exc}")

    # (b) Cleanup: remove wrapper jobs whose campaign is terminal / no longer scheduled.
    removed = 0
    for job in db.ws.jobs.list():
        settings = getattr(job, "settings", None)
        name = getattr(settings, "name", "") or ""
        tags = getattr(settings, "tags", None) or {}
        if not name.startswith(WRAPPER_NAME_PREFIX):
            continue
        if tags.get(WRAPPER_TAG_KEY) != WRAPPER_TAG_VALUE:
            continue
        cid = name[len(WRAPPER_NAME_PREFIX):]
        campaign = repo.get_campaign(cid)
        terminal = campaign is None or campaign.status in {
            "COMPLETED", "FAILED", "CANCELLED", "DRAFT", "PENDING_APPROVAL",
        }
        if terminal and job.job_id:
            try:
                db.ws.jobs.delete(job.job_id)
                removed += 1
                print(f"[cleanup] removed spent wrapper job {job.job_id} ({name})")
            except Exception as exc:  # noqa: BLE001
                print(f"[cleanup] could not delete {job.job_id}: {exc}")

    print(f"Reconcile done: dispatched={dispatched}, wrapper_jobs_removed={removed}")


if __name__ == "__main__":
    main()
