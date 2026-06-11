#!/usr/bin/env python3
"""P19 S4-06 · BSP 3:2 viewport stage aspect gate (DQ-05).

Usage:
  python scripts/p19_bsp_gate.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.layout_templates.probe_screenshot import (
    BSP_STAGE_3_2_TEMPLATE_IDS,
    run_bsp_stage_aspect_probe,
)
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 BSP 3:2 viewport gate")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "book-quality" / "bsp-gate.json",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "p19-bsp-gate.json",
    )
    args = parser.parse_args()

    reset_engine_cache_for_tests()
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    probe = run_bsp_stage_aspect_probe(engine, template_ids=BSP_STAGE_3_2_TEMPLATE_IDS)
    report = {
        "schema": "travelogue.acceptance.p19-bsp-gate",
        "version": 1,
        "date": date.today().isoformat(),
        "templateIds": list(BSP_STAGE_3_2_TEMPLATE_IDS),
        "probe": probe,
        "ok": bool(probe.get("ok")),
        "skipped": bool(probe.get("skipped")),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.archive.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if probe.get("skipped"):
        print(f"BSP probe skipped: {probe.get('reason')} -> {args.out}")
        return 0
    print(f"BSP 3:2 gate ok={report['ok']} -> {args.out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
