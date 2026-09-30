"""Render a human-readable Markdown checklist from a pytest JUnit XML file.

Usage: python tests/_report.py <junit.xml> <out.md> [title]
Uses each test's docstring (captured by pytest as the <testcase> ... ) — falls back
to the test node name. ✅ pass · ❌ fail · ⏭️ skipped.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    junit = Path(sys.argv[1])
    out = Path(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else "Acceptance Test Report"

    tree = ET.parse(junit)
    root = tree.getroot()
    cases = root.iter("testcase")

    lines = [f"# {title}", ""]
    total = passed = failed = skipped = 0
    rows = []
    for case in cases:
        total += 1
        name = case.get("name", "")
        failure = case.find("failure") is not None or case.find("error") is not None
        skip = case.find("skipped") is not None
        if skip:
            mark, status = "⏭️", "skipped"
            skipped += 1
        elif failure:
            mark, status = "❌", "FAIL"
            failed += 1
        else:
            mark, status = "✅", "pass"
            passed += 1
        label = name.replace("test_", "").replace("_", " ")
        rows.append(f"- [{'x' if status == 'pass' else ' '}] {mark} {label} ({status})")

    lines.append(f"**{passed}/{total} passed** · {failed} failed · {skipped} skipped")
    lines.append("")
    lines.extend(rows)
    lines.append("")
    lines.append("_Synthetic data / mock activation only._")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out} ({passed}/{total} passed, {failed} failed, {skipped} skipped)")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
