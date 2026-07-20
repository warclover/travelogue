"""LTN gap-close · C1 rescue / C3 prior / H8 / AC-C-02 / AC-C-07 leftovers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.log import MosaicWindowLog, format_log_entry
from travelogue.layout_engine.mosaic.scorer import (
    _apply_hero_gap_prior,
    _wasted_hero_penalty,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "fixtures" / "ltn"


def test_ac_c07_metric_reads_raw_log_not_window_trim():
    """AC-C-07 · metrics must see full rejectedTemplates; window keeps Top3 only."""
    rejected = [{"templateId": f"t{i}", "reason": "hard_invalid"} for i in range(5)]
    raw = MosaicWindowLog(rejected_templates=rejected).to_dict()
    window = format_log_entry(raw, "window")
    assert len(raw["rejectedTemplates"]) == 5
    assert len(window["rejectedTemplates"]) == 3


def test_ac_c07_no_grid9_boost_removed():
    from travelogue.layout_engine.mosaic import scorer

    src = Path(scorer.__file__).read_text(encoding="utf-8")
    assert "R_GRID9_LAND" in src  # comment documents removal
    assert "total = min(1.0, total * 1.06)" not in src


def test_c5_non_hero_emit_releases_armed_reserve():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.arm_hero_reserve()
    st.note_screen("screen-portrait-3")
    assert st.hero_reserve == "released"


def test_c3_wasted_hero_penalty_on_equal_dense_with_gap():
    # 6 landscapes with sharp hero gap → equal-weight dense pays wasted_hero.
    aspects = {f"a{i}": "landscape" for i in range(4)}
    assets = {
        "a0": {
            "id": "a0",
            "width": 3200,
            "height": 1800,
            "quality": {"sharpness": 0.95},
            "takenAt": "2024-06-01T12:00:00Z",
            "userTier": "featured",
        },
        "a1": {
            "id": "a1",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.40},
            "takenAt": "2024-06-01T12:01:00Z",
        },
        "a2": {
            "id": "a2",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.41},
            "takenAt": "2024-06-01T12:02:00Z",
        },
        "a3": {
            "id": "a3",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.42},
            "takenAt": "2024-06-01T12:03:00Z",
        },
    }
    screen = {
        "patternId": PATTERN_LANDSCAPE_4,
        "slots": [{"assetId": f"a{i}", "slot": i} for i in range(4)],
    }
    pen = _wasted_hero_penalty(
        screen,
        PATTERN_LANDSCAPE_4,
        aspects=aspects,
        assets_by_id=assets,
    )
    assert pen == pytest.approx(0.35)


def test_c3_hero_gap_prior_boosts_main_role():
    aspects = {f"a{i}": "landscape" for i in range(4)}
    assets = {
        "a0": {
            "id": "a0",
            "width": 3200,
            "height": 1800,
            "quality": {"sharpness": 0.95},
            "takenAt": "2024-06-01T12:00:00Z",
            "userTier": "featured",
        },
        "a1": {
            "id": "a1",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.40},
            "takenAt": "2024-06-01T12:01:00Z",
        },
        "a2": {
            "id": "a2",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.41},
            "takenAt": "2024-06-01T12:02:00Z",
        },
        "a3": {
            "id": "a3",
            "width": 3000,
            "height": 1687,
            "quality": {"sharpness": 0.42},
            "takenAt": "2024-06-01T12:03:00Z",
        },
    }
    reasons: list[str] = []
    total = _apply_hero_gap_prior(
        0.5,
        reasons,
        pattern_id=PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        asset_ids=["a0", "a1", "a2", "a3"],
        aspects=aspects,
        assets_by_id=assets,
    )
    assert total == pytest.approx(0.55)
    assert "R_HERO_GAP_PRIOR" in reasons


def test_h8_active_set_gate_ok():
    from scripts.ltn_active_set_gate import check

    report = check()
    assert report["ok"] is True
    assert report["activeUnionCount"] <= 12


def _oracle_hero_window_count(trip: dict) -> int:
    """Quota-free opportunity oracle proxy on fixture assets (AC-C-02 sample)."""
    from travelogue.config import MosaicConfig
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

    assets = {a["id"]: a for a in trip.get("assets") or [] if a.get("id")}
    aspects = {
        aid: str(a.get("aspectKind") or "landscape") for aid, a in assets.items()
    }
    ids = list(assets)
    if len(ids) < 4:
        return 0
    cfg = MosaicConfig(enabled=True, min_candidate_score=0.0)
    hits = 0
    for size in (4, 5, 6):
        if len(ids) < size:
            continue
        for start in range(0, len(ids) - size + 1):
            window = ids[start : start + size]
            bundle = generate_window_candidates_with_rejections(
                window,
                aspects,
                assets,
                cfg=cfg,
            )
            for c in bundle.candidates:
                if not c.hard_valid:
                    continue
                if ScreenLayoutPlannerState.pattern_has_main_role(c.pattern_id):
                    hits += 1
                    break
    return hits


def test_ac_c02_h9_oracle_positive_has_opportunity():
    trip = json.loads((FIXTURES / "trip.ltn_oracle_positive.json").read_text(encoding="utf-8"))
    assert _oracle_hero_window_count(trip) >= 1


def test_ac_c02_h9_oracle_negative_is_zero_or_low():
    trip = json.loads((FIXTURES / "trip.ltn_oracle_negative.json").read_text(encoding="utf-8"))
    # Negative fixture: sparse / no cohesive hero opportunity.
    assert _oracle_hero_window_count(trip) == 0


def test_c1_mcs_all_sizes_failed_reason_constant_present():
    from travelogue.layout_engine.mosaic import hook

    src = Path(hook.__file__).read_text(encoding="utf-8")
    assert "mcs_all_sizes_failed" in src
    assert "_try_mcs_single_hero_rescue" in src
