#!/usr/bin/env python3
"""One-off import rewrites for M-B4b physical migration."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = [
    ("travelogue.curation.mosaic.", "travelogue.layout_engine.mosaic."),
    ("travelogue.curation.screen_planner_attach", "travelogue.layout_engine.planner.screen_planner_attach"),
    ("travelogue.curation.screen_planner_stages", "travelogue.layout_engine.planner.screen_planner_stages"),
    ("travelogue.curation.screen_planner", "travelogue.layout_engine.planner.screen_planner"),
    ("travelogue.curation.layout_search", "travelogue.layout_engine.planner.layout_search"),
]

TARGET_DIRS = [
    ROOT / "travelogue" / "layout_engine" / "planner",
    ROOT / "travelogue" / "layout_engine" / "mosaic",
]


def rewrite_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for directory in TARGET_DIRS:
        for path in directory.rglob("*.py"):
            if rewrite_file(path):
                changed += 1
                print(f"updated {path.relative_to(ROOT)}")
    print(f"done: {changed} files")


if __name__ == "__main__":
    main()
