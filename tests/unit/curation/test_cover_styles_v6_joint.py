"""Cover Styles V6 · M2 joint pick, lock, repick."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.fit import (
    style_avoid_penalty,
    style_fit_score,
)
from travelogue.cover_engine.joint import (
    apply_joint_pick,
    apply_style_keep_cover,
    hash_fallback_pick,
    pick_cover_style_and_asset,
    repick_cover_for_style,
    score_pair,
)
from travelogue.cover_engine.registry import get_profile
from travelogue.cover_engine.types import CoverJointExplain
from travelogue.curation.curate import sync_trip_covers


def _asset(aid: str, fx: float, fy: float, *, score_hint: float = 1.0) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": 1600,
        "height": 1200,
        "focalPoint": {"x": fx, "y": fy},
        "userTier": "featured",
        # lightweight fields so cover scoring has something to chew on
        "sharpness": 0.7 + 0.05 * score_hint,
        "aesthetic": {"overall": 0.6 + 0.05 * score_hint},
    }


def _trip(assets: list[dict], *, locked: bool = False) -> dict:
    return {
        "tripId": "joint-demo",
        "exportLayout": "auto",
        "meta": {"coverOpeningStyle": "veil-footer", "title": "测试"},
        "assets": assets,
        "coverAssetId": assets[0]["id"] if assets else "",
        "curation": {"coverJointLocked": locked} if locked else {},
        "chapters": [],
    }


def test_band_cut_penalizes_focal_in_safe_zone() -> None:
    profile = get_profile("band-cut")
    bad = _asset("bad", 0.5, 0.63)
    good = _asset("good", 0.5, 0.35)
    assert style_avoid_penalty(bad, profile) > style_avoid_penalty(good, profile)


def test_cameo_prefers_center_subject() -> None:
    profile = get_profile("cameo-aperture")
    center = _asset("c", 0.51, 0.44)
    center["faceCount"] = 1
    edge = _asset("e", 0.1, 0.2)
    assert style_fit_score(center, profile) > style_fit_score(edge, profile)


def test_cameo_ignores_sentinel_default_focal() -> None:
    """Missing / (0.5,0.45) sentinel must not inflate cameo fit."""
    profile = get_profile("cameo-aperture")
    sentinel = _asset("s", 0.5, 0.45)
    loose = _asset("l", 0.36, 0.33)
    tight = _asset("t", 0.51, 0.44)
    tight["faceCount"] = 1
    assert style_fit_score(sentinel, profile) == 0.0
    assert style_fit_score(loose, profile) == 0.0
    assert style_fit_score(tight, profile) > 0.0


def test_score_pair_joint_formula() -> None:
    asset = _asset("a1", 0.5, 0.4)
    explain = score_pair(asset, "veil-footer", quality=10.0, quality_max=10.0)
    assert explain.style_id == "veil-footer"
    assert explain.asset_id == "a1"
    assert explain.source == "joint-v6"
    assert explain.joint == explain.quality + 0.35 * explain.fit - 0.5 * explain.avoid_penalty


def test_pick_cover_style_and_asset_returns_assignable() -> None:
    from travelogue.cover_engine import assignable_style_ids

    assets = [
        _asset("upper", 0.5, 0.3, score_hint=2),
        _asset("band-hit", 0.5, 0.63, score_hint=3),
        _asset("center", 0.5, 0.45, score_hint=1.5),
    ]
    trip = _trip(assets)
    explain = pick_cover_style_and_asset(trip, layout="web", k=5)
    assert explain.style_id in set(assignable_style_ids())
    assert explain.asset_id in {a["id"] for a in assets}
    assert explain.source in ("joint-v6", "hash-fallback")


def test_band_cut_not_optimal_when_focal_in_strip() -> None:
    """AC-CSV6-20 · 切带忌讳图不得成为 band-cut 最优对（有替代时）。"""
    assets = [
        _asset("strip", 0.5, 0.63, score_hint=5),
        _asset("safe", 0.5, 0.3, score_hint=4.8),
    ]
    _trip(assets)
    # Force compare pairs for band-cut only via score_pair
    qmax = 5.0
    strip = score_pair(assets[0], "band-cut", quality=5.0, quality_max=qmax)
    safe = score_pair(assets[1], "band-cut", quality=4.8, quality_max=qmax)
    assert safe.joint > strip.joint


def test_apply_joint_pick_locks() -> None:
    trip = _trip([_asset("a1", 0.5, 0.4)])
    explain = pick_cover_style_and_asset(trip, layout="web")
    apply_joint_pick(trip, explain, lock=True, layout="web")
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["meta"]["coverOpeningStyle"] == explain.style_id
    assert trip["curation"]["coverByLayout"]["web"] == explain.asset_id
    assert trip["curation"]["coverStyleExplain"]["source"] == explain.source


def test_apply_joint_pick_marks_title_art_stale_when_cover_changes() -> None:
    """换封面照片时主动置 titleArt.stale（展示层另有 coverAssetId 指纹比对）。"""
    trip = _trip([_asset("a1", 0.5, 0.4), _asset("a2", 0.55, 0.45)])
    trip["exportLayout"] = "web"
    trip["coverAssetId"] = "a1"
    trip["meta"]["titleArt"] = {
        "enabled": True,
        "stale": False,
        "coverAssetId": "a1",
        "assetPath": "x.png",
    }
    explain = CoverJointExplain(
        source="test",
        style_id="veil-footer",
        asset_id="a2",
        joint=1.0,
        quality=1.0,
        fit=1.0,
        avoid_penalty=0.0,
        low_confidence=False,
    )
    apply_joint_pick(trip, explain, lock=True, layout="web")
    assert trip["coverAssetId"] == "a2"
    assert trip["meta"]["titleArt"]["stale"] is True


def test_sync_trip_covers_respects_lock() -> None:
    assets = [
        _asset("a1", 0.5, 0.3, score_hint=2),
        _asset("a2", 0.55, 0.4, score_hint=1),
    ]
    trip = _trip(assets)
    sync_trip_covers(trip, export_layout="auto", force=True)
    assert trip["curation"].get("coverJointLocked") is True
    style = trip["meta"]["coverOpeningStyle"]
    web = trip["curation"]["coverByLayout"]["web"]

    # Mutate assets order / scores would change pick; lock must freeze web
    trip["assets"].append(_asset("a3", 0.52, 0.44, score_hint=9))
    trip["assets"][-1]["faceCount"] = 1
    sync_trip_covers(trip, export_layout="auto", force=False)
    assert trip["meta"]["coverOpeningStyle"] == style
    assert trip["curation"]["coverByLayout"]["web"] == web


def test_sync_trip_covers_force_reopens_joint() -> None:
    assets = [_asset("a1", 0.5, 0.3), _asset("a2", 0.55, 0.4)]
    trip = _trip(assets)
    sync_trip_covers(trip, export_layout="auto", force=True)
    first_web = trip["curation"]["coverByLayout"]["web"]
    sync_trip_covers(trip, export_layout="auto", force=True)
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["curation"]["coverByLayout"]["web"]  # still set
    assert first_web  # smoke


def test_repick_cover_for_style_keeps_lock() -> None:
    # cameo-aperture retired 2026-08-03; use band-cut (still assignable) to
    # exercise the same repick/lock mechanics — center focal (fy=0.44) still
    # nets a higher band-cut fit (upper_scene + horizon) than the edge asset.
    assets = [
        _asset("center", 0.51, 0.44, score_hint=2),
        _asset("edge", 0.1, 0.2, score_hint=2),
    ]
    assets[0]["faceCount"] = 1
    trip = _trip(assets)
    explain = repick_cover_for_style(trip, "band-cut", layout="web")
    assert explain.style_id == "band-cut"
    assert explain.source == "manual"
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["meta"]["coverOpeningStyle"] == "band-cut"
    assert trip["curation"]["coverByLayout"]["web"] == explain.asset_id
    assert explain.asset_id == "center"


def test_apply_style_keep_cover() -> None:
    assets = [_asset("keep-me", 0.5, 0.3)]
    trip = _trip(assets)
    trip["curation"] = {"coverByLayout": {"web": "keep-me", "mobile": "keep-me"}}
    explain = apply_style_keep_cover(trip, "folio-overlap")
    assert explain.asset_id == "keep-me"
    assert trip["meta"]["coverOpeningStyle"] == "folio-overlap"
    assert trip["curation"]["coverJointLocked"] is True
    assert "coverSecondaryAssetId" not in trip["meta"]


def test_apply_style_keep_cover_rejects_retired_style() -> None:
    """2026-08-03: diptych-seam retired — Studio keep-cover path must refuse it
    (mirrors the Studio picker no longer offering it)."""
    assets = [_asset("keep-me", 0.5, 0.3)]
    trip = _trip(assets)
    trip["curation"] = {"coverByLayout": {"web": "keep-me", "mobile": "keep-me"}}
    with pytest.raises(ValueError):
        apply_style_keep_cover(trip, "diptych-seam")


def test_repick_opening_rejects_explicit_retired_style() -> None:
    """assetId + retired styleId must not re-activate a retired opening."""
    from travelogue.cover_engine.api import repick_opening

    assets = [_asset("keep-me", 0.5, 0.3), _asset("alt", 0.5, 0.35)]
    trip = _trip(assets)
    trip["meta"]["coverOpeningStyle"] = "veil-footer"
    with pytest.raises(ValueError, match="not assignable"):
        repick_opening(trip, asset_id="alt", style_id="diptych-seam")
    assert trip["meta"]["coverOpeningStyle"] == "veil-footer"


def test_repick_opening_asset_only_keeps_legacy_retired_style() -> None:
    """Asset-only repick on a legacy retired trip must keep rendering style."""
    from travelogue.cover_engine.api import repick_opening

    assets = [_asset("keep-me", 0.5, 0.3), _asset("alt", 0.5, 0.35)]
    trip = _trip(assets)
    trip["meta"]["coverOpeningStyle"] = "diptych-seam"
    trip["curation"] = {"coverByLayout": {"web": "keep-me", "mobile": "keep-me"}}
    repick_opening(trip, asset_id="alt")
    assert trip["meta"]["coverOpeningStyle"] == "diptych-seam"
    assert trip["curation"]["coverByLayout"]["web"] == "alt"


def test_diptych_secondary_pick_logic_kept_for_legacy_trips() -> None:
    """diptych-seam is retired (no longer selectable), but already-locked
    legacy trips still render via the same secondary-panel pick logic — keep
    it covered directly so it doesn't bitrot."""
    from travelogue.cover_engine.joint import _with_diptych_secondary

    scene = _asset("scene", 0.5, 0.35, score_hint=3)
    person = _asset("person", 0.5, 0.44, score_hint=2)
    person["faceCount"] = 1
    candidates = [{"asset": scene, "quality": 0.8}, {"asset": person, "quality": 0.6}]
    explain = CoverJointExplain(source="manual", style_id="diptych-seam", asset_id="scene")
    result = _with_diptych_secondary(explain, candidates, trip_id="joint-demo")
    assert result.secondary_asset_id == "person"


def test_hash_fallback_pick_source() -> None:
    from travelogue.cover_engine import assignable_style_ids

    trip = _trip([_asset("a1", 0.5, 0.4)])
    explain = hash_fallback_pick(trip, layout="web")
    assert explain.source == "hash-fallback"
    assert explain.style_id in set(assignable_style_ids())


def test_apply_joint_pick_ignores_retired_style_id() -> None:
    """2026-08-03: diptych-seam retired — apply_joint_pick must not persist a
    retired styleId (e.g. from a stale cached explain); trip keeps its prior
    coverOpeningStyle instead. secondaryAssetId is only ever written when
    style_id == 'diptych-seam', so it stays unset here too."""
    scene = _asset("scene", 0.5, 0.35, score_hint=3)
    person = _asset("person", 0.5, 0.44, score_hint=2)
    person["faceCount"] = 1
    trip = _trip([scene, person])  # _trip() defaults meta.coverOpeningStyle="veil-footer"
    explain = CoverJointExplain(
        source="joint-v6",
        style_id="diptych-seam",
        asset_id="scene",
        joint=1.0,
        quality=1.0,
        fit=0.5,
        avoid_penalty=0.0,
        low_confidence=False,
        secondary_asset_id="person",
    )
    apply_joint_pick(trip, explain, lock=True, layout="web")
    assert trip["meta"]["coverOpeningStyle"] == "veil-footer"

    explain_clear = CoverJointExplain(
        source="manual",
        style_id="veil-footer",
        asset_id="scene",
        joint=0.5,
        quality=0.5,
        fit=0.3,
        avoid_penalty=0.0,
        low_confidence=False,
    )
    apply_joint_pick(trip, explain_clear, lock=True, layout="web")
    assert "coverSecondaryAssetId" not in trip["meta"]


def test_joint_pick_distribution_not_cameo_collapsed() -> None:
    """Regression: varied focals must not all collapse to cameo-aperture."""
    from collections import Counter

    # Mix of upper / right / band-safe / true-center / atmosphere focals
    pools = [
        [_asset("u1", 0.5, 0.28, score_hint=3), _asset("u2", 0.55, 0.32, score_hint=2)],
        [_asset("r1", 0.72, 0.45, score_hint=3), _asset("r2", 0.68, 0.50, score_hint=2)],
        [_asset("b1", 0.5, 0.35, score_hint=3), _asset("b2", 0.48, 0.40, score_hint=2)],
        [
            _asset("c1", 0.51, 0.44, score_hint=3),
            _asset("c2", 0.49, 0.43, score_hint=2),
        ],
        [_asset("m1", 0.35, 0.55, score_hint=3), _asset("m2", 0.60, 0.58, score_hint=2)],
        [_asset("loose", 0.36, 0.33, score_hint=3), _asset("loose2", 0.40, 0.30, score_hint=2)],
        [_asset("sent", 0.5, 0.45, score_hint=3), _asset("sent2", 0.5, 0.45, score_hint=2)],
        [_asset("left", 0.22, 0.40, score_hint=3), _asset("up", 0.5, 0.25, score_hint=2.5)],
    ]
    pools[3][0]["faceCount"] = 1
    pools[3][1]["faceCount"] = 1
    for i, assets in enumerate(pools):
        for a in assets:
            a["aesthetic"] = {"overall": 0.62 + 0.01 * i}

    counts: Counter[str] = Counter()
    for i, assets in enumerate(pools):
        trip = _trip(assets)
        trip["tripId"] = f"dist-{i}"
        explain = pick_cover_style_and_asset(trip, layout="web", k=5)
        counts[explain.style_id] += 1

    assert counts["cameo-aperture"] <= max(2, len(pools) // 2), counts
    assert len(counts) >= 3, counts


def test_loose_center_prefers_veil_or_band_over_cameo() -> None:
    """Roughly mid-upper scene must not win as cameo solely via wide center window."""
    from travelogue.cover_engine import assignable_style_ids

    assets = [
        _asset("loose", 0.36, 0.33, score_hint=5),
        _asset("loose2", 0.40, 0.30, score_hint=4),
    ]
    trip = _trip(assets)
    explain = pick_cover_style_and_asset(trip, layout="web", k=5)
    assert explain.style_id != "cameo-aperture"
    assert explain.style_id in set(assignable_style_ids())