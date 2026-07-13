"""Bookends Engine · B2a closing + pairing (AC-BE-10..14)."""

from __future__ import annotations

import pytest

from travelogue.config.bookends import BookendsConfig, bookends_config_from_dict
from travelogue.config.runtime import config_override
from travelogue.cover_engine.api import (
    ClosingPendingError,
    maybe_resolve_closing_after_layout,
    resolve_closing,
    resolve_opening,
)
from travelogue.cover_engine.joint import pick_cover_style_and_asset
from travelogue.cover_engine.pairing.policy import pairing_hard_violations
from travelogue.domain.closing_view import resolve_closing_asset_id


def _img(aid: str, *, w: int = 1600, h: int = 900, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": w,
        "height": h,
        "userTier": "featured",
        "sharpness": 0.8,
        "aesthetic": {"overall": 0.65},
    }
    base.update(extra)
    return base


def test_pair_h1_cover_not_equal_closing() -> None:
    trip = {
        "tripId": "pair-h1",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "assets": [
            _img("cover"),
            _img("body", dominantTone="#334455"),
            _img("spare", dominantTone="#8899aa"),
        ],
        "chapters": [
            {"screens": [{"slots": [{"assetId": "cover"}, {"assetId": "body"}]}]},
        ],
        "curation": {},
    }
    decision = resolve_closing(trip, layout="web", force=True)
    assert decision.closing_asset_id is not None
    assert decision.closing_asset_id != "cover"
    assert trip["curation"]["closingAssetId"] == decision.closing_asset_id


def test_no_candidate_degraded_no_cover_reuse() -> None:
    trip = {
        "tripId": "tiny",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "assets": [_img("cover")],
        "chapters": [{"screens": [{"slots": [{"assetId": "cover"}]}]}],
        "curation": {},
    }
    decision = resolve_closing(trip, layout="web", force=True)
    assert decision.closing_asset_id is None
    assert decision.degraded is True
    assert trip["curation"]["closingAssetId"] is None
    assert trip["curation"].get("bookendsDegraded") is True
    assert "封面" in (decision.explain.get("userOneLiner") or "") or "省略" in (
        decision.explain.get("userOneLiner") or ""
    )


def test_prefers_unused_over_screen() -> None:
    trip = {
        "tripId": "unused",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "assets": [
            _img("cover"),
            _img("on-screen", dominantTone="#aabbcc"),
            _img("unused", dominantTone="#445566"),
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "on-screen"}]}]}],
        "curation": {},
    }
    decision = resolve_closing(trip, layout="web", force=True)
    assert decision.closing_asset_id == "unused"


def test_pair_h3_blocks_second_large_face() -> None:
    cover = _img(
        "face-cover",
        w=1200,
        h=1600,
        faceCount=1,
        faces=[{"bbox": {"x": 0.3, "y": 0.2, "w": 0.5, "h": 0.5}}],
        focalPoint={"x": 0.5, "y": 0.4},
    )
    near = _img(
        "face-near",
        w=1200,
        h=1600,
        faceCount=1,
        faces=[{"bbox": {"x": 0.25, "y": 0.2, "w": 0.55, "h": 0.55}}],
        focalPoint={"x": 0.5, "y": 0.42},
    )
    scenic = _img("scenic", dominantTone="#223344")
    assert "PAIR-H3" in pairing_hard_violations(cover, near)
    trip = {
        "tripId": "h3",
        "exportLayout": "web",
        "coverAssetId": "face-cover",
        "assets": [cover, near, scenic],
        "chapters": [{"screens": [{"slots": [{"assetId": "near"}]}]}],
        "curation": {},
    }
    decision = resolve_closing(trip, layout="web", force=True)
    assert decision.closing_asset_id == "scenic"


def test_maybe_resolve_skips_explicit_null() -> None:
    trip = {
        "tripId": "null-skip",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "assets": [_img("cover"), _img("spare")],
        "chapters": [{"screens": [{"slots": [{"assetId": "spare"}]}]}],
        "curation": {"closingAssetId": None},
    }
    assert maybe_resolve_closing_after_layout(trip) is None
    assert "closingAssetId" in trip["curation"]
    assert trip["curation"]["closingAssetId"] is None


def test_resolve_closing_requires_screens() -> None:
    trip = {
        "tripId": "no-screens",
        "coverAssetId": "cover",
        "assets": [_img("cover"), _img("spare")],
        "chapters": [],
        "curation": {},
    }
    with pytest.raises(ClosingPendingError):
        resolve_closing(trip)


def test_opening_hard_gate_default_true() -> None:
    cfg = BookendsConfig()
    assert cfg.title_safe.opening_hard_gate is True
    loaded = bookends_config_from_dict({})
    assert loaded.title_safe.opening_hard_gate is True


def test_opening_hard_gate_blocks_title_unsafe_top1() -> None:
    """AC-BE-14 · focal in band-cut strip must not win as band-cut Top1 when gated."""
    from travelogue.config import get_config

    strip = _img(
        "strip",
        focalPoint={"x": 0.5, "y": 0.72},
        sharpness=0.95,
        aesthetic={"overall": 0.9},
    )
    safe = _img(
        "safe",
        focalPoint={"x": 0.5, "y": 0.3},
        sharpness=0.9,
        aesthetic={"overall": 0.85},
    )
    trip = {
        "tripId": "hard-gate",
        "exportLayout": "web",
        "meta": {"coverOpeningStyle": "band-cut"},
        "assets": [strip, safe],
        "coverAssetId": "strip",
        "curation": {},
        "chapters": [],
    }
    cfg = get_config()
    with config_override(cfg):
        # ensure hard gate on
        cfg.bookends.title_safe.opening_hard_gate = True
        explain = pick_cover_style_and_asset(trip, layout="web", k=5)
        if explain.style_id == "band-cut":
            assert explain.asset_id != "strip"


def test_excluded_by_moment_in_closing_explain() -> None:
    trip = {
        "tripId": "moment-x",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "momentAssetId": "peak",
        "assets": [
            _img("cover"),
            _img("peak", dominantTone="#223344"),
            _img("spare", dominantTone="#556677"),
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "spare"}]}]}],
        "curation": {},
    }
    decision = resolve_closing(trip, force=True)
    assert decision.closing_asset_id != "peak"
    assert "peak" in (decision.explain or {}).get("excludedByMoment", [])
