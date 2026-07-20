"""LTN D1 rhythmGap hints + D2 classic_magazine peak band."""

from __future__ import annotations

from travelogue.layout_contract.rhythm_gap import assign_rhythm_gaps_on_append
from travelogue.layout_engine.beat import beat_score_multiplier


def test_city_change_marks_prev_l2():
    assets = {
        "a0": {"id": "a0", "place": {"city": "Tokyo"}},
        "a1": {"id": "a1", "place": {"city": "Osaka"}},
    }
    prev = {
        "screenId": "s1",
        "patternId": "screen-landscape-1",
        "slots": [{"assetId": "a0"}],
        "rhythmGap": "L1",
    }
    cur = {
        "screenId": "s2",
        "patternId": "screen-landscape-1",
        "slots": [{"assetId": "a1"}],
    }
    assign_rhythm_gaps_on_append(cur, prev_screen=prev, assets_map=assets)
    assert prev["rhythmGap"] == "L2"
    assert cur["rhythmGap"] == "L1"


def test_after_mosaic_hero_marks_l2():
    prev = {
        "screenId": "s1",
        "patternId": "screen-mosaic-4-hero-70-sidebar",
        "narrativeRole": "mosaic_hero",
        "slots": [{"assetId": "a0", "role": "main"}, {"assetId": "a1"}],
        "rhythmGap": "L1",
    }
    cur = {
        "screenId": "s2",
        "patternId": "screen-landscape-1",
        "slots": [{"assetId": "a2"}],
    }
    assign_rhythm_gaps_on_append(cur, prev_screen=prev, assets_map={})
    assert prev["rhythmGap"] == "L2"


def test_cohesive_dense_run_tightens_to_l0():
    prev = {
        "screenId": "s1",
        "patternId": "screen-mosaic-4-2l2p-weighted",
        "narrativeRole": "mosaic_flat",
        "preserveGroup": True,
        "slots": [{"assetId": "a0"}, {"assetId": "a1"}],
        "rhythmGap": "L1",
    }
    cur = {
        "screenId": "s2",
        "patternId": "screen-portrait-2",
        "narrativeRole": "pair",
        "preserveGroup": True,
        "slots": [{"assetId": "a2"}, {"assetId": "a3"}],
    }
    assign_rhythm_gaps_on_append(cur, prev_screen=prev, assets_map={})
    assert prev["rhythmGap"] == "L0"


def test_classic_magazine_peak_band_mid_chapter():
    mid = beat_score_multiplier(
        "screen-mosaic-5-main-hero-plus-4",
        screen_index=6,
        chapter_screen_count=10,
        beat_profile="classic_magazine",
    )
    # progress = 6/9 ≈ 0.667 → peak band
    assert mid == 1.12
    early = beat_score_multiplier(
        "screen-mosaic-5-main-hero-plus-4",
        screen_index=3,
        chapter_screen_count=10,
        beat_profile="classic_magazine",
    )
    # progress = 3/9 ≈ 0.33 → outside opening (<0.25) and peak (0.55–0.70)
    assert early == 1.0
    opening = beat_score_multiplier(
        "screen-mosaic-5-main-hero-plus-4",
        screen_index=0,
        chapter_screen_count=10,
        beat_profile="classic_magazine",
    )
    assert opening == 1.12


def test_rhythm_tokens_present_in_overlays():
    from pathlib import Path

    text = Path("templates/visual-journal/journal-screens-overlays.css").read_text(
        encoding="utf-8"
    )
    assert "--rhythm-l0-gap" in text
    assert "--rhythm-l1-gap" in text
    assert "--rhythm-l2-gap" in text
    assert 'data-rhythm-gap="L2"' in text
