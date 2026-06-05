"""PA-T07 / PA-T08 · aesthetic integration in cover + hero scoring."""

from __future__ import annotations

from travelogue.curation.aesthetic_score import aesthetic_multiplier, median_aesthetic_overall
from travelogue.curation.curate_scoring import (
    build_cover_explain,
    cover_score,
    effective_hero_score,
    hero_score,
    pick_chapter_hero,
    pick_cover_asset_id,
    score_ranked_cover_ids,
)
from travelogue.curation.screen_planner import _pick_main_landscape_id


def _asset(
    aid: str,
    *,
    overall: float | None = None,
    composition: float = 0.7,
    subject_clarity: float = 0.7,
    sharpness: float = 200.0,
    width: int = 1200,
    height: int = 1600,
    aspect: str = "portrait",
) -> dict:
    entry: dict = {
        "id": aid,
        "width": width,
        "height": height,
        "aspectKind": aspect,
        "quality": {"sharpness": sharpness, "meanLuma": 0.5},
        "dominantTone": "#4488cc",
    }
    if overall is not None:
        entry["quality"]["aesthetic"] = {
            "version": "pa-v0.1",
            "overall": overall,
            "dims": {
                "composition": composition,
                "subjectClarity": subject_clarity,
            },
        }
    return entry


def test_aesthetic_multiplier_clamps_to_design_window() -> None:
    high = _asset("a", overall=0.9)
    low = _asset("b", overall=0.3)
    med = median_aesthetic_overall([high, low])
    assert aesthetic_multiplier(high, median_overall=med) == 1.3
    assert aesthetic_multiplier(low, median_overall=med) == 0.7


def test_aesthetic_multiplier_fail_open_without_overall() -> None:
    assert aesthetic_multiplier(_asset("x", overall=None), median_overall=0.5) == 1.0


def test_cover_score_boosts_high_aesthetic_over_median() -> None:
    pool = [_asset("low", overall=0.40), _asset("high", overall=0.80)]
    med = median_aesthetic_overall(pool)
    low = cover_score(
        pool[0], "mobile", median_sharp=200.0, median_overall=med, aesthetic_enabled=True
    )
    high = cover_score(
        pool[1], "mobile", median_sharp=200.0, median_overall=med, aesthetic_enabled=True
    )
    assert high > low


def test_cover_score_unchanged_when_aesthetic_disabled() -> None:
    pool = [_asset("low", overall=0.40), _asset("high", overall=0.80)]
    med = median_aesthetic_overall(pool)
    base = cover_score(pool[0], "mobile", median_sharp=200.0, aesthetic_enabled=False)
    with_ae = cover_score(
        pool[0], "mobile", median_sharp=200.0, median_overall=med, aesthetic_enabled=False
    )
    assert base == with_ae


def test_build_cover_explain_lists_aesthetic_factor() -> None:
    pool = [_asset("a", overall=0.40), _asset("b", overall=0.80)]
    med = median_aesthetic_overall(pool)
    explain = build_cover_explain(
        pool[1], "mobile", median_sharp=200.0, median_overall=med, aesthetic_enabled=True
    )
    codes = {item["code"] for item in explain}
    assert "aesthetic" in codes


def test_pick_cover_prefers_higher_aesthetic() -> None:
    assets = [
        _asset("dull", overall=0.35, sharpness=250.0),
        _asset("vivid", overall=0.85, sharpness=200.0),
    ]
    picked = pick_cover_asset_id(assets, export_layout="mobile", aesthetic_enabled=True)
    assert picked == "vivid"


def test_hero_score_uses_aesthetic_dims_when_enabled() -> None:
    plain = _asset(
        "a",
        overall=0.5,
        composition=0.5,
        subject_clarity=0.5,
        width=1600,
        height=900,
        aspect="landscape",
    )
    strong = _asset(
        "b",
        overall=0.9,
        composition=0.9,
        subject_clarity=0.9,
        width=1600,
        height=900,
        aspect="landscape",
    )
    assert hero_score(strong, aesthetic_enabled=True) > hero_score(
        plain, aesthetic_enabled=True
    )


def test_hero_falls_back_to_sharpness_without_aesthetic_block() -> None:
    sharp = _asset("sharp", overall=None, sharpness=400.0, width=1600, height=900, aspect="landscape")
    soft = _asset("soft", overall=None, sharpness=80.0, width=1600, height=900, aspect="landscape")
    pool = [sharp, soft]
    assert hero_score(
        sharp, median_sharp=200.0, aesthetic_enabled=True, pool=pool
    ) > hero_score(soft, median_sharp=200.0, aesthetic_enabled=True, pool=pool)


def test_pick_chapter_hero_prefers_aesthetic_with_sharpness_tiebreak() -> None:
    assets = {
        "a": _asset(
            "a",
            overall=0.55,
            width=1600,
            height=900,
            aspect="landscape",
            sharpness=100.0,
        ),
        "b": _asset(
            "b",
            overall=0.75,
            width=1600,
            height=900,
            aspect="landscape",
            sharpness=100.0,
        ),
    }
    hero = pick_chapter_hero(["a", "b"], assets, aesthetic_enabled=True)
    assert hero == "b"


def test_pick_main_landscape_prefers_aesthetic_overall() -> None:
    assets = {
        "wide-weak": _asset(
            "wide-weak",
            overall=0.40,
            width=2000,
            height=900,
            aspect="landscape",
        ),
        "wide-strong": _asset(
            "wide-strong",
            overall=0.85,
            width=1600,
            height=900,
            aspect="landscape",
        ),
    }
    main = _pick_main_landscape_id(
        ["wide-weak", "wide-strong"], assets, aesthetic_enabled=True
    )
    assert main == "wide-strong"


def test_score_ranked_cover_top_matches_pick_cover_asset_id() -> None:
    web_assets = [
        _asset("weak", overall=0.35, width=3000, height=2000, aspect="landscape"),
        _asset("strong", overall=0.88, width=3200, height=1800, aspect="landscape"),
        _asset("mid", overall=0.55, width=2800, height=1600, aspect="landscape"),
    ]
    mobile_assets = [
        _asset("weak-p", overall=0.35, width=1200, height=2000, aspect="portrait"),
        _asset("strong-p", overall=0.88, width=1080, height=1920, aspect="portrait"),
        _asset("mid-p", overall=0.55, width=900, height=1600, aspect="portrait"),
    ]
    for layout, assets in (("web", web_assets), ("mobile", mobile_assets)):
        picked = pick_cover_asset_id(assets, export_layout=layout, aesthetic_enabled=True)
        ranked = score_ranked_cover_ids(
            assets,
            export_layout=layout,
            limit=3,
        )
        assert ranked
        assert ranked[0]["assetId"] == picked


def test_effective_hero_score_anchor_still_applies_with_aesthetic() -> None:
    base = _asset("a", overall=0.6, width=1600, height=900, aspect="landscape")
    tagged = {**base, "tags": ["寺"]}
    plain = effective_hero_score(base, aesthetic_enabled=True)
    boosted = effective_hero_score(tagged, memory_anchors=["寺"], aesthetic_enabled=True)
    assert boosted > plain
