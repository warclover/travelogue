"""Cover Styles V6 · M2 joint pick, lock, repick."""

from __future__ import annotations

from travelogue.cover_engine.fit import (
    style_avoid_penalty,
    style_fit_below_threshold,
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
    bad = _asset("bad", 0.5, 0.72)
    good = _asset("good", 0.5, 0.35)
    assert style_avoid_penalty(bad, profile) > style_avoid_penalty(good, profile)


def test_cameo_prefers_center_subject() -> None:
    profile = get_profile("cameo-aperture")
    center = _asset("c", 0.5, 0.45)
    edge = _asset("e", 0.1, 0.2)
    assert style_fit_score(center, profile) > style_fit_score(edge, profile)


def test_score_pair_joint_formula() -> None:
    asset = _asset("a1", 0.5, 0.4)
    explain = score_pair(asset, "veil-footer", quality=10.0, quality_max=10.0)
    assert explain.style_id == "veil-footer"
    assert explain.asset_id == "a1"
    assert explain.source == "joint-v6"
    assert explain.joint == explain.quality + 0.35 * explain.fit - 0.5 * explain.avoid_penalty


def test_pick_cover_style_and_asset_returns_assignable() -> None:
    assets = [
        _asset("upper", 0.5, 0.3, score_hint=2),
        _asset("band-hit", 0.5, 0.72, score_hint=3),
        _asset("center", 0.5, 0.45, score_hint=1.5),
    ]
    trip = _trip(assets)
    explain = pick_cover_style_and_asset(trip, layout="web", k=5)
    assert explain.style_id in {
        "veil-footer",
        "folio-overlap",
        "band-cut",
        "cameo-aperture",
        "type-monument",
    }
    assert explain.asset_id in {a["id"] for a in assets}
    assert explain.source in ("joint-v6", "hash-fallback")


def test_band_cut_not_optimal_when_focal_in_strip() -> None:
    """AC-CSV6-20 · 切带忌讳图不得成为 band-cut 最优对（有替代时）。"""
    assets = [
        _asset("strip", 0.5, 0.72, score_hint=5),
        _asset("safe", 0.5, 0.3, score_hint=4.8),
    ]
    trip = _trip(assets)
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


def test_sync_trip_covers_respects_lock() -> None:
    assets = [
        _asset("a1", 0.5, 0.3, score_hint=2),
        _asset("a2", 0.5, 0.4, score_hint=1),
    ]
    trip = _trip(assets)
    sync_trip_covers(trip, export_layout="auto", force=True)
    assert trip["curation"].get("coverJointLocked") is True
    style = trip["meta"]["coverOpeningStyle"]
    web = trip["curation"]["coverByLayout"]["web"]

    # Mutate assets order / scores would change pick; lock must freeze web
    trip["assets"].append(_asset("a3", 0.5, 0.45, score_hint=9))
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
    assets = [
        _asset("center", 0.5, 0.45, score_hint=2),
        _asset("edge", 0.1, 0.2, score_hint=2),
    ]
    trip = _trip(assets)
    explain = repick_cover_for_style(trip, "cameo-aperture", layout="web")
    assert explain.style_id == "cameo-aperture"
    assert explain.source == "manual"
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["meta"]["coverOpeningStyle"] == "cameo-aperture"
    assert trip["curation"]["coverByLayout"]["web"] == explain.asset_id


def test_apply_style_keep_cover() -> None:
    assets = [_asset("keep-me", 0.5, 0.3)]
    trip = _trip(assets)
    trip["curation"] = {"coverByLayout": {"web": "keep-me", "mobile": "keep-me"}}
    explain = apply_style_keep_cover(trip, "folio-overlap")
    assert explain.asset_id == "keep-me"
    assert trip["meta"]["coverOpeningStyle"] == "folio-overlap"
    assert trip["curation"]["coverJointLocked"] is True


def test_hash_fallback_pick_source() -> None:
    trip = _trip([_asset("a1", 0.5, 0.4)])
    explain = hash_fallback_pick(trip, layout="web")
    assert explain.source == "hash-fallback"
    assert explain.style_id
    assert explain.asset_id == "a1"
