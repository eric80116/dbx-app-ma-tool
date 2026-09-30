"""Job entrypoint: run the pytest integration/acceptance suite against the deployed schema.

Configuration comes from argv (passed by the bundle). Exits non-zero on test failure so
the job run reflects the result.
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


def main() -> None:
    parser = argparse.ArgumentParser()
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

    import pytest

    # Integration + acceptance suites require a live warehouse/schema.
    code = pytest.main(
        [
            str(ROOT / "tests" / "integration"),
            str(ROOT / "tests" / "acceptance"),
            "-m",
            "integration or acceptance",
            "-v",
        ]
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
