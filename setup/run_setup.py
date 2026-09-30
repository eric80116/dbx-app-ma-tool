"""Job entrypoint: create tables + seed synthetic data.

Runs both as a Databricks job task (serverless) and locally. Configuration is read
from argv (passed by the bundle) or the environment, so no .env is required on the job.

Usage:
    python run_setup.py [--catalog C] [--schema S] [--warehouse-id W]
                        [--audience-source-mode M] [--skip-seed]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    """Locate the repo root robustly.

    On Databricks serverless the file is exec'd, so ``__file__`` is undefined; fall back
    to ``sys.argv[0]`` (the runner passes the script path) and finally the cwd. The chosen
    root is the first candidate that actually contains ``src/ma_app``.
    """
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


def _apply_env(args: argparse.Namespace) -> None:
    if args.catalog:
        os.environ["MA_APP_TARGET_CATALOG"] = args.catalog
    if args.schema:
        os.environ["MA_APP_APP_SCHEMA"] = args.schema
    if args.warehouse_id:
        os.environ["MA_APP_WAREHOUSE_ID"] = args.warehouse_id
    if args.audience_source_mode:
        os.environ["MA_APP_AUDIENCE_SOURCE_MODE"] = args.audience_source_mode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=os.environ.get("MA_APP_TARGET_CATALOG"))
    parser.add_argument("--schema", default=os.environ.get("MA_APP_APP_SCHEMA"))
    parser.add_argument("--warehouse-id", default=os.environ.get("MA_APP_WAREHOUSE_ID"))
    parser.add_argument(
        "--audience-source-mode",
        default=os.environ.get("MA_APP_AUDIENCE_SOURCE_MODE", "local_snapshot"),
    )
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()
    _apply_env(args)

    from _bootstrap import get_db  # type: ignore
    from create_tables import create_all  # type: ignore
    from seed_demo_data import seed  # type: ignore

    db = get_db()
    created = create_all(db)
    print(f"Created/verified {len(created)} tables in {db.config.schema_fqn}")
    if args.skip_seed:
        print("Skipping seed (--skip-seed).")
        return
    counts = seed(db)
    print("Seeded synthetic demo data (source_type=SYNTHETIC_SNAPSHOT):")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
