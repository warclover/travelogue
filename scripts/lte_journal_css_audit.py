#!/usr/bin/env python3
"""Audit journal-screens.css hand-written grid inventory (R-P16-14)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from travelogue.layout_templates.css_gen import (
    LTE_MARKER_END,
    LTE_MARKER_START,
    _journal_text_without_overlay_block,
    lte_grid_classes_outside_marker,
)
from travelogue.paths import JOURNAL_SCREENS_CSS

_OUTSIDE_GRID_RE = re.compile(r"layout-screen__grid--[\w-]+")


def audit_journal_css(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    text_no_overlays = _journal_text_without_overlay_block(text)
    start = text_no_overlays.find(LTE_MARKER_START)
    end = text_no_overlays.find(LTE_MARKER_END)
    if start < 0 or end < 0:
        raise SystemExit(f"Missing LTE markers in {path}")
    outside = text_no_overlays[:start] + text_no_overlays[end + len(LTE_MARKER_END) :]
    inventory = sorted(set(_OUTSIDE_GRID_RE.findall(outside)))
    dupes = lte_grid_classes_outside_marker(text)
    return {
        "path": str(path),
        "outsideGeneratedGridClassCount": len(inventory),
        "outsideGeneratedGridClasses": inventory,
        "duplicateGridClassesOutsideMarker": dupes,
        "auditNote": "Inventory excludes @journal-overlays selectors; gate on duplicateGridClassesOutsideMarker.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit hand-written grid CSS outside LTE generated block")
    ap.add_argument("--path", type=Path, default=Path(JOURNAL_SCREENS_CSS))
    ap.add_argument("--max-outside", type=int, default=None)
    ap.add_argument("--max-duplicates", type=int, default=0)
    ap.add_argument("--fail-on-duplicates", action="store_true")
    args = ap.parse_args(argv)
    report = audit_journal_css(args.path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.max_outside is not None and report["outsideGeneratedGridClassCount"] > args.max_outside:
        return 1
    dupes = report["duplicateGridClassesOutsideMarker"]
    max_dupes = args.max_duplicates if args.max_duplicates is not None else 0
    if args.fail_on_duplicates and dupes:
        return 1
    if len(dupes) > max_dupes:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
