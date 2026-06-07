#!/usr/bin/env python3
"""Synthetic probe regression for LTE templates (V-P16-07 · PR warn)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from travelogue.layout_templates.probe_regress import run_probe_for_template, run_probe_regress
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, LayoutTemplateEngine

# Re-export for tests / admission callers that import from scripts.
__all__ = ["run_probe_for_template", "run_probe_regress", "run_screenshot_probe"]


def run_screenshot_probe(engine: LayoutTemplateEngine, *, update_baselines: bool = False) -> dict:
    """Playwright cover/contain screenshot diff against golden PNG baselines."""
    from travelogue.layout_templates.probe_screenshot import run_screenshot_probe as _run

    return _run(engine, update_baselines=update_baselines)


def main() -> int:
    parser = argparse.ArgumentParser(description="LTE synthetic probe regression")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_DIR)
    parser.add_argument("--strict", action="store_true", help="Treat screenshot warnings as failure (with --screenshot)")
    parser.add_argument(
        "--strict-geometry",
        action="store_true",
        help="Treat geometry/saliency probe warnings as failure (nightly only)",
    )
    parser.add_argument(
        "--screenshot",
        action="store_true",
        help="Playwright cover/contain screenshot diff (V-P16-07)",
    )
    parser.add_argument(
        "--update-baselines",
        action="store_true",
        help="Write/refresh probe PNG baselines under layout_templates/probes/baselines/",
    )
    args = parser.parse_args()
    engine = LayoutTemplateEngine.load(args.templates)
    payload = run_probe_regress(engine)
    if args.screenshot or args.update_baselines:
        shot = run_screenshot_probe(
            engine,
            update_baselines=args.update_baselines,
        )
        payload["screenshotProbe"] = shot
        if args.strict and not shot.get("skipped") and not shot.get("ok", True):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.strict_geometry and payload["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
