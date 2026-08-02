"""ALG-V3 W3-C3 · prune no-op beam variants when preferred_hero_id is absent."""

from __future__ import annotations

from travelogue.layout_engine.planner.layout_candidates import generate_day_bucket_candidates


def _fake_plan_factory(calls: list[dict]):
    def _fake_plan(_bucket, **kwargs):
        calls.append(dict(kwargs))
        # Distinct-ish plans so signature de-dupe does not collapse all variants.
        hero = kwargs.get("preferred_hero_id")
        include = kwargs.get("include_chapter_hero", True)
        mosaic = kwargs.get("enable_mosaic", True)
        tag = f"{include}-{hero}-{mosaic}-{len(calls)}"
        return [{"patternId": f"screen-solo-{tag}", "slots": [{"assetId": "a1"}]}]

    return _fake_plan


def test_c3_no_preferred_hero_skips_hero_variants(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.plan_screens_for_chapter",
        _fake_plan_factory(calls),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.bucket_has_mosaic_window",
        lambda *_a, **_k: False,
    )
    generate_day_bucket_candidates(
        ["a1", "a2", "a3"],
        {"a1": "landscape", "a2": "landscape", "a3": "landscape"},
        assets_by_id={
            "a1": {"id": "a1"},
            "a2": {"id": "a2"},
            "a3": {"id": "a3"},
        },
        orientation_summary={"landscape": 3},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        beam_width=5,
    )
    assert len(calls) == 1
    assert calls[0].get("include_chapter_hero") is True
    assert calls[0].get("preferred_hero_id") is None


def test_c3_with_preferred_hero_keeps_hero_variants(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.plan_screens_for_chapter",
        _fake_plan_factory(calls),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.bucket_has_mosaic_window",
        lambda *_a, **_k: True,
    )
    generate_day_bucket_candidates(
        ["a1", "a2", "a3", "a4", "a5"],
        {f"a{i}": "landscape" for i in range(1, 6)},
        assets_by_id={f"a{i}": {"id": f"a{i}"} for i in range(1, 6)},
        orientation_summary={"landscape": 5},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id="a1",
        layout_state=None,
        beam_width=8,
    )
    # with_hero, no_mosaic, no_hero, hero_no_pref, no_hero_no_mosaic
    assert len(calls) == 5
    flags = [
        (
            c.get("include_chapter_hero"),
            c.get("preferred_hero_id"),
            c.get("enable_mosaic", True),
        )
        for c in calls
    ]
    assert (True, "a1", True) in flags  # with_hero
    assert (True, "a1", False) in flags  # no_mosaic
    assert (False, "a1", True) in flags  # no_hero
    assert (True, None, True) in flags  # hero_no_pref
    assert (False, "a1", False) in flags  # no_hero_no_mosaic


def test_c3_no_preferred_with_mosaic_only_adds_no_mosaic(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.plan_screens_for_chapter",
        _fake_plan_factory(calls),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_candidates.bucket_has_mosaic_window",
        lambda *_a, **_k: True,
    )
    generate_day_bucket_candidates(
        ["a1", "a2", "a3", "a4", "a5"],
        {f"a{i}": "landscape" for i in range(1, 6)},
        assets_by_id={f"a{i}": {"id": f"a{i}"} for i in range(1, 6)},
        orientation_summary={"landscape": 5},
        skip_screen_asset_ids=set(),
        mixed_proximity_seconds=12,
        trip_photo_total=40,
        preferred_hero_id=None,
        layout_state=None,
        beam_width=5,
    )
    assert len(calls) == 2
    assert any(c.get("enable_mosaic") is False for c in calls)
    assert all(c.get("preferred_hero_id") is None for c in calls)
    assert all(c.get("include_chapter_hero") is True for c in calls)
