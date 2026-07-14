"""Bookends Engine · B1 resolve_opening facade (AC-BE-01..05)."""

from __future__ import annotations

import pytest

from travelogue.config.bookends import BookendsConfig, bookends_config_from_dict
from travelogue.cover_engine.api import (
    ClosingPendingError,
    resolve_bookends,
    resolve_closing,
    resolve_opening,
)
from travelogue.cover_engine.opening.title_safe import mark_title_safe
from travelogue.curation.curate import sync_trip_covers


def _asset(aid: str, fx: float, fy: float, *, score_hint: float = 1.0) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": 1600,
        "height": 1200,
        "focalPoint": {"x": fx, "y": fy},
        "userTier": "featured",
        "sharpness": 0.7 + 0.05 * score_hint,
        "aesthetic": {"overall": 0.6 + 0.05 * score_hint},
    }


def _trip(assets: list[dict], *, locked: bool = False) -> dict:
    return {
        "tripId": "bookends-b1",
        "exportLayout": "auto",
        "meta": {"coverOpeningStyle": "veil-footer", "title": "测试"},
        "assets": assets,
        "coverAssetId": assets[0]["id"] if assets else "",
        "curation": {"coverJointLocked": locked} if locked else {},
        "chapters": [],
    }


def test_resolve_opening_returns_legal_decision() -> None:
    assets = [
        _asset("upper", 0.5, 0.3, score_hint=2),
        _asset("band-hit", 0.5, 0.72, score_hint=3),
        _asset("center", 0.5, 0.45, score_hint=1.5),
    ]
    trip = _trip(assets)
    decision = resolve_opening(trip, layout="auto", force=True)
    assert decision.cover_asset_id
    assert decision.closing_pending is True
    assert decision.closing_asset_id is None
    assert decision.cover_opening_style
    assert "web" in decision.cover_by_layout or decision.cover_by_layout
    assert decision.lock.opening is True
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["curation"]["bookendsLock"]["opening"] is True
    assert decision.telemetry.get("resolveOpeningMs") is not None


def test_resolve_bookends_pending_without_screens() -> None:
    trip = _trip([_asset("a1", 0.5, 0.3)])
    decision = resolve_bookends(trip, layout="auto", force=True)
    assert decision.closing_pending is True
    assert "closingAssetId" not in trip.get("curation", {})


def test_resolve_closing_without_screens_errors() -> None:
    trip = _trip([_asset("a1", 0.5, 0.3)])
    with pytest.raises(ClosingPendingError):
        resolve_closing(trip)


def test_opening_respects_lock_without_force() -> None:
    assets = [
        _asset("a1", 0.5, 0.3, score_hint=2),
        _asset("a2", 0.55, 0.4, score_hint=1),
    ]
    trip = _trip(assets)
    first = resolve_opening(trip, layout="auto", force=True)
    style = trip["meta"]["coverOpeningStyle"]
    web = trip["curation"]["coverByLayout"]["web"]

    trip["assets"].append(_asset("a3", 0.52, 0.44, score_hint=9))
    trip["assets"][-1]["faceCount"] = 1
    second = resolve_opening(trip, layout="auto", force=False)
    assert second.cover_asset_id == first.cover_asset_id
    assert trip["meta"]["coverOpeningStyle"] == style
    assert trip["curation"]["coverByLayout"]["web"] == web


def test_sync_trip_covers_delegates_to_resolve_opening() -> None:
    assets = [_asset("a1", 0.5, 0.3), _asset("a2", 0.55, 0.4)]
    trip = _trip(assets)
    cover_id = sync_trip_covers(trip, export_layout="auto", force=True)
    assert cover_id == trip["coverAssetId"]
    assert trip["curation"]["bookendsLock"]["opening"] is True
    assert trip["curation"].get("bookendsTelemetry", {}).get("resolveOpeningMs") is not None


def test_title_safe_marks_without_changing_top1_when_gate_off() -> None:
    """When hard gate off — mark only; selection stays deterministic."""
    from travelogue.config import get_config
    from travelogue.config.runtime import config_override

    asset = _asset("strip", 0.5, 0.72)
    mark = mark_title_safe(asset, "band-cut", hard_gate=False)
    assert mark["titleUnsafe"] is True
    assert mark["hardGateApplied"] is False

    assets = [
        _asset("strip", 0.5, 0.72, score_hint=5),
        _asset("safe", 0.5, 0.3, score_hint=4.8),
    ]
    cfg = get_config()
    with config_override(cfg):
        cfg.bookends.title_safe.opening_hard_gate = False
        trip = _trip(assets)
        before = resolve_opening(trip, layout="web", force=True)
        trip2 = _trip(assets)
        after = resolve_opening(trip2, layout="web", force=True)
        assert before.cover_by_layout.get("web") == after.cover_by_layout.get("web") or (
            before.cover_asset_id == after.cover_asset_id
        )


def test_bookends_config_defaults_hard_gate_true() -> None:
    cfg = BookendsConfig()
    assert cfg.title_safe.opening_hard_gate is True
    loaded = bookends_config_from_dict({})
    assert loaded.title_safe.opening_hard_gate is True
    loaded2 = bookends_config_from_dict({"title_safe": {"opening_hard_gate": False}})
    assert loaded2.title_safe.opening_hard_gate is False


def test_package_reexport_resolve_opening() -> None:
    import travelogue.cover_engine as ce
    from travelogue.cover_engine import api

    assert ce.resolve_opening is api.resolve_opening
    trip = _trip([_asset("a1", 0.5, 0.3)])
    d1 = ce.resolve_opening(trip, layout="auto", force=True)
    trip2 = _trip([_asset("a1", 0.5, 0.3)])
    d2 = api.resolve_opening(trip2, layout="auto", force=True)
    assert d1.cover_opening_style == d2.cover_opening_style
    assert d1.lock.opening == d2.lock.opening
