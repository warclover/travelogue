#!/usr/bin/env python3
"""One-shot reverse migration: legacy mosaic sources → LTE YAML (PRD §7, T2)."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from travelogue.layout_templates.legacy_bridge import (
    all_legacy_pattern_ids,
    reverse_pattern_to_yaml_dict,
)
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate layout template YAML from legacy mosaic sources")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_TEMPLATES_DIR,
        help="Output directory for *.yaml templates",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print paths only")
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    ids = sorted(all_legacy_pattern_ids())
    for pattern_id in ids:
        doc = reverse_pattern_to_yaml_dict(pattern_id)
        path = out / f"{pattern_id}.yaml"
        if args.dry_run:
            print(path)
            continue
        path.write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        print(f"wrote {path.name}")
    print(f"total: {len(ids)} templates → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
