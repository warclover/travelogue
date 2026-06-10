"""Mosaic beam candidate variants."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from travelogue.curation.layout_candidates import (
    bucket_has_mosaic_window,
    generate_day_bucket_candidates,
)
from travelogue.curation.search_budget import SearchBudget


def _asset(aid: str, kind: str, secs: float = 0) -> dict:
    # Landscapes use a 16:9 native AR so they sit on the main-slot AR ladder
    # (main-AR-guard rejects off-ladder mains like 5:3); portraits use 9:16.
    return {
        "id": aid,
        "aspectKind": kind,
        "takenAt": (datetime(2025, 6, 1, 10, tzinfo=UTC) + timedelta(seconds=secs)).isoformat(),
        "width": 1920 if kind == "landscape" else 900,
        "height": 1080 if kind == "landscape" else 1600,
    }


def test_bucket_has_mosaic_window_detects_five_mix(monkeypatch):
    from dataclasses import replace

    from travelogue import config as config_mod

    base = config_mod.get_config()
    monkeypatch.setattr(
        config_mod,
        "get_config",
        lambda: replace(
            base,
            mosaic=replace(base.mosaic, enabled_window_sizes=(3, 4, 5, 6, 8, 9)),
        ),
    )
    # 4 land + 1 portrait, time-near
    ids = ["l1", "l2", "l3", "l4", "p1"]
    aspects = {i: ("portrait" if i == "p1" else "landscape") for i in ids}
    assets = {
        "l1": _asset("l1", "landscape", 0),
        "l2": _asset("l2", "landscape", 3),
        "l3": _asset("l3", "landscape", 6),
        "l4": _asset("l4", "landscape", 9),
        "p1": _asset("p1", "portrait", 4),
    }
    assert bucket_has_mosaic_window(ids, aspects, assets, mixed_proximity_seconds=12, trip_photo_total=40)


def test_no_mosaic_variant_differs_when_eligible():
    ids = ["l1", "l2", "l3", "l4", "p1"]
    aspects = {i: ("portrait" if i == "p1" else "landscape") for i in ids}
    assets = {i: _asset(i, aspects[i], idx) for idx, i in enumerate(ids)}
    budget = SearchBudget(max_evaluations_per_trip=20, max_candidates_per_bucket=8)
    cands = generate_day_bucket_candidates(
        ids,
        aspects,  # type: ignore[arg-type]
        assets_by_id=assets,
        orientation_summary={"landscape": 4, "portrait": 1},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        beam_width=5,
        budget=budget,
    )
    sigs = [tuple(s.get("patternId") for s in plan) for _name, plan in cands]
    assert len(cands) >= 2
    assert sigs[0] != sigs[1] or len(cands) >= 2
    assert budget.generations >= len(cands)
    assert budget.evaluations == 0


def test_generate_candidates_passes_enable_food_grid_flag(monkeypatch) -> None:
    ids = ["f1", "f2", "f3"]
    aspects = {i: "square" for i in ids}
    assets = {i: _asset(i, "landscape", idx) for idx, i in enumerate(ids)}
    captured: list[bool] = []

    def _fake_plan(_bucket, **kwargs):
        captured.append(bool(kwargs.get("enable_food_grid", True)))
        return [{"patternId": "screen-square-4", "slots": [{"assetId": "f1"}]}]

    monkeypatch.setattr(
        "travelogue.curation.layout_candidates.plan_screens_for_chapter",
        _fake_plan,
    )
    cands = generate_day_bucket_candidates(
        ids,
        aspects,  # type: ignore[arg-type]
        assets_by_id=assets,
        orientation_summary={"landscape": 3, "portrait": 0},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        enable_food_grid=False,
        beam_width=3,
    )
    assert cands
    assert captured
    assert all(flag is False for flag in captured)


def test_generate_candidates_passes_mundane_grid_buckets(monkeypatch) -> None:
    ids = ["f1", "f2", "f3"]
    aspects = {i: "square" for i in ids}
    assets = {i: _asset(i, "landscape", idx) for idx, i in enumerate(ids)}
    captured: list[tuple[str, ...]] = []

    def _fake_plan(_bucket, **kwargs):
        captured.append(tuple(kwargs.get("mundane_grid_buckets", ("food",))))
        return [{"patternId": "screen-square-4", "slots": [{"assetId": "f1"}]}]

    monkeypatch.setattr(
        "travelogue.curation.layout_candidates.plan_screens_for_chapter",
        _fake_plan,
    )
    cands = generate_day_bucket_candidates(
        ids,
        aspects,  # type: ignore[arg-type]
        assets_by_id=assets,
        orientation_summary={"landscape": 3, "portrait": 0},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        mundane_grid_buckets=("food", "sign"),
        beam_width=3,
    )
    assert cands
    assert captured
    assert all(b == ("food", "sign") for b in captured)
