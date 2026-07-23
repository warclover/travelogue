"""CSC W0 · Happy Path Recipe read-only snapshot (AC-CSC-01)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.config import AppConfig
from travelogue.orchestrator.happy_path_recipe import (
    ADVANCED_SETTINGS_KEYS,
    DANGER_DEFAULT_FALSE,
    L0_OPS_ROOTS,
    L1_RESULT_KEYS,
    appconfig_bool_map,
    orchestration_snapshot,
    studio_default_recipe,
)
from travelogue.orchestrator.studio_profile import StudioProfile

_BASELINE = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "acceptance-records"
    / "csc-w0-baseline-happy-path-recipe.json"
)


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


def test_studio_default_recipe_matches_w0_baseline_snapshot() -> None:
    """AC-CSC-01: default enablement set is frozen and reviewable."""
    assert _BASELINE.is_file(), f"missing baseline {_BASELINE}"
    expected = json.loads(_BASELINE.read_text(encoding="utf-8"))
    actual = _golden_slice(studio_default_recipe())
    assert actual == expected


def test_orchestration_matches_studio_profile_studio_default() -> None:
    snap = orchestration_snapshot(StudioProfile.studio_default())
    assert snap["run_clustering"] is True
    assert snap["apply_editorial_hints"] is True
    assert snap["export_layout"] == "auto"
    assert snap["ingest"]["resume_ingest"] is True
    assert snap["ingest"]["use_parallel_embed"] is True


def test_danger_tier_defaults_remain_false() -> None:
    bools = appconfig_bool_map(AppConfig())
    for path in DANGER_DEFAULT_FALSE:
        assert path in bools, path
        assert bools[path] is False, f"{path} must stay default False (Danger firewall)"


def test_bool_counts_match_prd_diagnostic_band() -> None:
    """W0 baseline band: 151 bools (incl. studio.ai_surface_enabled), 97 True / 54 False."""
    counts = studio_default_recipe()["counts"]
    assert counts["bool_fields"] == 151
    assert counts["default_true"] == 97
    assert counts["default_false"] == 54


def test_l1_budget_and_tiers_are_disjoint() -> None:
    """CSC D-CSC-04: L1 ≤10; Danger/Advanced settings not in L1."""
    assert len(L1_RESULT_KEYS) <= 10
    assert len(L0_OPS_ROOTS) >= 1
    l1 = set(L1_RESULT_KEYS)
    assert l1.isdisjoint(DANGER_DEFAULT_FALSE)
    assert l1.isdisjoint(ADVANCED_SETTINGS_KEYS)
    recipe = studio_default_recipe()
    assert recipe["l1_keys"] == list(L1_RESULT_KEYS)
