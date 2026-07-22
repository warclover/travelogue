#!/usr/bin/env python3
"""CSC · Recipe baseline gate (D-CSC-10 / AC-CSC-01).

Fails when live ``AppConfig`` default True set or Recipe golden slice
diverges from ``csc-w0-baseline-happy-path-recipe.json`` without an
intentional baseline update.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "acceptance-records" / "csc-w0-baseline-happy-path-recipe.json"


def _golden_slice(recipe: dict) -> dict:
    return {
        "recipe_id": recipe["recipe_id"],
        "schema_version": recipe["schema_version"],
        "orchestration": recipe["orchestration"],
        "layout_exit": {
            "studio_export_layout": recipe["layout_exit"]["studio_export_layout"],
            "web_layout_engine_config": recipe["layout_exit"]["web_layout_engine_config"],
        },
        "counts": recipe["counts"],
        "appconfig_bools": recipe["appconfig_bools"],
        "danger_must_stay_false": recipe["danger_must_stay_false"],
        "l0_ops_roots": recipe["l0_ops_roots"],
        "l1_keys": recipe["l1_keys"],
        "advanced_settings_keys": recipe["advanced_settings_keys"],
    }


def main() -> int:
    if not BASELINE.is_file():
        print(f"missing baseline: {BASELINE}", file=sys.stderr)
        return 1

    from travelogue.orchestrator.happy_path_recipe import studio_default_recipe

    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    actual = _golden_slice(studio_default_recipe())
    if actual == expected:
        print(
            "CSC recipe baseline OK:",
            f"{actual['counts']['default_true']} True /",
            f"{actual['counts']['default_false']} False ·",
            f"L1={len(actual['l1_keys'])}",
        )
        return 0

    exp_true = {p for p, v in expected["appconfig_bools"].items() if v}
    act_true = {p for p, v in actual["appconfig_bools"].items() if v}
    added = sorted(act_true - exp_true)
    removed = sorted(exp_true - act_true)
    print("CSC recipe baseline DRIFT (update baseline only with review):", file=sys.stderr)
    if added:
        print("  new default True:", file=sys.stderr)
        for p in added:
            print(f"    + {p}", file=sys.stderr)
    if removed:
        print("  lost default True:", file=sys.stderr)
        for p in removed:
            print(f"    - {p}", file=sys.stderr)
    if actual["counts"] != expected["counts"]:
        print(f"  counts: {expected['counts']} -> {actual['counts']}", file=sys.stderr)
    if actual["l1_keys"] != expected["l1_keys"]:
        print(f"  l1_keys: {expected['l1_keys']} -> {actual['l1_keys']}", file=sys.stderr)
    if actual["orchestration"] != expected["orchestration"]:
        print("  orchestration changed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
