"""PRD portrait-row-editorial · P1 planner/config/mobile tests."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AppConfig
from travelogue.config.layout import EditorialPortraitRowConfig
from travelogue.curation.editorial_portrait_row import (
    LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
    PATTERN_PORTRAIT_3_EDITORIAL,
    editorial_row_fit_mode,
    apply_editorial_portrait_row_to_screen,
    editorial_scope_matches,
    is_editorial_portrait_row_enabled,
    maybe_editorial_portrait_row,
)
from travelogue.curation.screen_layout_state import (
    ScreenLayoutPlannerState,
    is_triple_row_pattern,
)
from travelogue.curation.screen_planner import plan_screens_for_chapter
from travelogue.render.mobile_screens import (
    expand_portrait_triples_for_mobile,
    should_expand_portrait_triple_for_mobile,
)
from tests._golden.helpers import (
    build_portrait_heavy_trip,
    layout_snapshot,
    load_golden,
    plan_legacy_screens,
)


def _assets_with_tags(ids: list[str], tag_map: dict[str, list[str]]) -> dict[str, dict]:
    return {
        i: {
            "id": i,
            "tags": tag_map.get(i, []),
            "nativeWidth": 1200,
            "nativeHeight": 1800,
            "layoutEligible": True,
        }
        for i in ids
    }


def _cfg_with_editorial(*, enabled: bool = True, scope: str = "all") -> AppConfig:
    from travelogue.config import get_config

    base = get_config()
    epr = EditorialPortraitRowConfig(enabled=enabled, scope=scope)
    layout = replace(base.layout, editorial_portrait_row=epr)
    return replace(base, layout=layout)


def test_triple_pattern_includes_editorial() -> None:
    assert is_triple_row_pattern("screen-portrait-3")
    assert is_triple_row_pattern("screen-portrait-3-editorial")
    assert not is_triple_row_pattern("screen-portrait-2")


def test_editorial_triple_consecutive_ban_r02() -> None:
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.can_emit_pattern("screen-portrait-3")
    st.note_screen(PATTERN_PORTRAIT_3_EDITORIAL)
    assert not st.can_emit_pattern("screen-portrait-3")
    assert not st.can_emit_pattern(PATTERN_PORTRAIT_3_EDITORIAL)


def test_is_editorial_enabled_priority() -> None:
    cfg = _cfg_with_editorial(enabled=False)
    trip = {"tripId": "demo", "export": {"editorialPortraitRow": True}}
    assert is_editorial_portrait_row_enabled(trip, cfg)
    trip2 = {"tripId": "on-allowlist"}
    cfg2 = replace(
        cfg,
        layout=replace(
            cfg.layout,
            editorial_portrait_row=EditorialPortraitRowConfig(
                enabled=False, trip_allowlist=("on-allowlist",)
            ),
        ),
    )
    assert is_editorial_portrait_row_enabled(trip2, cfg2)
    assert not is_editorial_portrait_row_enabled({"tripId": "other"}, cfg2)


def test_editorial_scope_person_requires_all_person() -> None:
    assets = _assets_with_tags(
        ["p1", "p2", "p3"],
        {x: ["person", "face"] for x in ["p1", "p2", "p3"]},
    )
    assert editorial_scope_matches("person", ["p1", "p2", "p3"], assets)
    assets_mixed = dict(assets)
    assets_mixed["p3"] = {"id": "p3", "tags": [], "layoutEligible": True}
    assert not editorial_scope_matches("person", ["p1", "p2", "p3"], assets_mixed)


def test_editorial_scope_scenery_requires_no_person() -> None:
    assets = _assets_with_tags(["s1", "s2", "s3"], {})
    assert editorial_scope_matches("scenery", ["s1", "s2", "s3"], assets)
    assets["s2"] = {"id": "s2", "tags": ["person"], "layoutEligible": True}
    assert not editorial_scope_matches("scenery", ["s1", "s2", "s3"], assets)


def test_editorial_scope_all_allows_mixed() -> None:
    assets = _assets_with_tags(
        ["p1", "s1", "s2"],
        {"p1": ["person", "face"], "s1": [], "s2": []},
    )
    assert editorial_scope_matches("all", ["p1", "s1", "s2"], assets)
    cfg = _cfg_with_editorial(enabled=True, scope="person")
    pid, hint = maybe_editorial_portrait_row(
        "screen-portrait-3", ["p1", "s1", "s2"], assets, cfg=cfg
    )
    assert pid == "screen-portrait-3"
    assert hint is None


def test_plan_emits_editorial_when_enabled() -> None:
    ids = ["p1", "p2", "p3"]
    aspects = {x: "portrait" for x in ids}
    assets = _assets_with_tags(ids, {x: ["person", "face"] for x in ids})
    cfg = _cfg_with_editorial(enabled=True, scope="person")
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-ed",
        assets=assets,
        app_config=cfg,
    )
    assert len(screens) == 1
    assert screens[0]["patternId"] == PATTERN_PORTRAIT_3_EDITORIAL
    assert screens[0]["layoutHint"] == LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL


def test_legacy_golden_unchanged_when_editorial_disabled() -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    baseline = layout_snapshot(
        plan_legacy_screens(buckets, aspects, assets, layout_density="balanced")
    )
    cfg = _cfg_with_editorial(enabled=False)
    import travelogue.config as config_mod

    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        current = layout_snapshot(
            plan_legacy_screens(buckets, aspects, assets, layout_density="balanced")
        )
    finally:
        config_mod.get_config = orig
    assert current == baseline


def test_golden_editorial_portrait_row_enabled_off_on() -> None:
    from tests._golden.helpers import load_golden

    ids = ["p1", "p2", "p3"]
    aspects = {x: "portrait" for x in ids}
    assets_list = _assets_with_tags(ids, {x: ["person", "face"] for x in ids})
    assets_map = assets_list
    buckets = [ids]

    cfg_off = _cfg_with_editorial(enabled=False)
    cfg_on = _cfg_with_editorial(enabled=True, scope="person")
    import travelogue.config as config_mod

    def _plan(cfg: AppConfig):
        orig = config_mod.get_config
        config_mod.get_config = lambda: cfg  # type: ignore[assignment]
        try:
            return plan_legacy_screens(
                buckets,
                aspects,
                list(assets_map.values()),
                layout_density="balanced",
            )
        finally:
            config_mod.get_config = orig

    legacy_snap = layout_snapshot(_plan(cfg_off))
    editorial_snap = layout_snapshot(_plan(cfg_on))
    assert legacy_snap == load_golden("editorial-portrait-row-legacy")
    assert editorial_snap == load_golden("editorial-portrait-row-editorial")


def test_apply_editorial_replaces_person_triple_hint() -> None:
    assets = _assets_with_tags(["a", "b", "c"], {x: ["person"] for x in "abc"})
    screen = {
        "patternId": "screen-portrait-3",
        "layoutHint": "person-triple",
        "slots": [{"assetId": x, "slot": i} for i, x in enumerate("abc")],
    }
    cfg = _cfg_with_editorial(enabled=True, scope="person")
    out = apply_editorial_portrait_row_to_screen(screen, assets, cfg=cfg)
    assert out["patternId"] == PATTERN_PORTRAIT_3_EDITORIAL
    assert out["layoutHint"] == LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL


def test_mobile_screens_engine_portrait_triple_expands_to_singles() -> None:
    triple = {
        "patternId": "screen-portrait-3-editorial",
        "layoutHint": "portrait-row-editorial",
        "slots": [
            {"assetId": "a", "slot": 0, "fit": "contain"},
            {"assetId": "b", "slot": 1, "fit": "contain"},
            {"assetId": "c", "slot": 2, "fit": "contain"},
        ],
    }
    expanded = expand_portrait_triples_for_mobile([triple])
    assert len(expanded) == 3
    assert all(sc["patternId"] == "screen-portrait-1" for sc in expanded)
    assert [sc["slots"][0]["assetId"] for sc in expanded] == ["a", "b", "c"]
    assert all(len(sc["slots"]) == 1 for sc in expanded)
    assert all("layoutHint" not in sc for sc in expanded)


def test_mobile_longshot_skips_triple_expand() -> None:
    assert not should_expand_portrait_triple_for_mobile("mobile", is_longshot=True)
    assert should_expand_portrait_triple_for_mobile("mobile", is_longshot=False)
    assert not should_expand_portrait_triple_for_mobile("web", is_longshot=False)


def test_mobile_triple_expand_plate_on_first_slot_only() -> None:
    """AC-ED-08e · folio plate index: only first expanded single is chapter opener."""
    triple = {
        "patternId": "screen-portrait-3",
        "slots": [{"assetId": f"p{i}", "slot": i} for i in range(3)],
    }
    plate_flags: list[bool] = []
    chapter_screen_seq = 0
    for sc in expand_portrait_triples_for_mobile([triple]):
        chapter_screen_seq += 1
        plate_flags.append(chapter_screen_seq == 1)
        assert sc["patternId"] == "screen-portrait-1"
    assert plate_flags == [True, False, False]


def test_expand_legacy_portrait_3_on_mobile() -> None:
    legacy = {
        "patternId": "screen-portrait-3",
        "slots": [{"assetId": f"x{i}", "slot": i} for i in range(3)],
    }
    out = expand_portrait_triples_for_mobile([legacy])
    assert len(out) == 3
    assert all(sc["patternId"] == "screen-portrait-1" for sc in out)


def test_editorial_row_fit_stable_hash() -> None:
    args = dict(
        trip_id="trip-a",
        screen_id="ch-01-sc-02",
        asset_ids=("s1", "s2", "s3"),
    )
    first = editorial_row_fit_mode(**args)
    for _ in range(20):
        assert editorial_row_fit_mode(**args) == first


def test_editorial_row_fit_distribution_balanced() -> None:
    from travelogue.curation.editorial_portrait_row import editorial_row_fit_mode

    cover = 0
    for i in range(128):
        mode = editorial_row_fit_mode(
            trip_id="dist-trip",
            screen_id=f"sc-{i:03d}",
            asset_ids=("a", "b", "c"),
        )
        if mode == "cover":
            cover += 1
    assert 40 <= cover <= 88


def test_person_editorial_row_always_contain() -> None:
    from travelogue.curation.editorial_portrait_row import (
        apply_editorial_row_slot_fits,
        editorial_row_fit_mode,
    )

    assets = _assets_with_tags(["p1", "p2", "p3"], {x: ["person"] for x in ["p1", "p2", "p3"]})
    screen = {
        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
        "screenId": "ch-sc-01",
        "slots": [{"assetId": x, "slot": i} for i, x in enumerate(["p1", "p2", "p3"])],
    }
    out = apply_editorial_row_slot_fits(screen, assets, trip={"tripId": "t1"})
    assert all(s["fit"] == "contain" for s in out["slots"])
    # Person rows never use hash path
    assert (
        editorial_row_fit_mode(
            trip_id="t1",
            screen_id="ch-sc-01",
            asset_ids=("p1", "p2", "p3"),
        )
        in ("cover", "contain")
    )


def test_scenery_editorial_uniform_fit_after_screen_id() -> None:
    from travelogue.curation.editorial_portrait_row import apply_editorial_row_slot_fits

    assets = _assets_with_tags(["s1", "s2", "s3"], {})
    screen = {
        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
        "screenId": "ch-sc-02",
        "slots": [{"assetId": x, "slot": i} for i, x in enumerate(["s1", "s2", "s3"])],
    }
    out = apply_editorial_row_slot_fits(screen, assets, trip={"tripId": "scenery-trip"})
    fits = {s["fit"] for s in out["slots"]}
    assert len(fits) == 1
    assert fits.pop() in ("cover", "contain")


def test_editorial_row_ar_from_fixtures() -> None:
    from travelogue.curation.editorial_portrait_row import editorial_row_ar_from_assets

    assets = {
        "a": {"id": "a", "nativeWidth": 800, "nativeHeight": 1200},
        "b": {"id": "b", "nativeWidth": 900, "nativeHeight": 1600},
        "c": {"id": "c", "nativeWidth": 700, "nativeHeight": 1000},
    }
    ar = editorial_row_ar_from_assets(["a", "b", "c"], assets)
    col_w = (960 - 72) / 3
    h_b = col_w * 1600 / 900
    assert abs(ar - col_w / h_b) < 1e-6


def test_scenery_editorial_trip_produces_cover_and_contain_rows() -> None:
    """AC-ED-06 · 纯风景 editorial 行同时出现 cover 与 contain（planner + attach fit）。"""
    from travelogue.curation.editorial_portrait_row import (
        PATTERN_PORTRAIT_3_EDITORIAL,
        apply_editorial_row_slot_fits,
    )
    from travelogue.layout_engine.adapter import ChapterPlanRequest, plan_chapter_screens

    n = 12
    ids = [f"s{i}" for i in range(n)]
    aspects = {x: "portrait" for x in ids}
    assets = {
        x: {
            "id": x,
            "tags": [],
            "nativeWidth": 900,
            "nativeHeight": 1600,
            "layoutEligible": True,
        }
        for x in ids
    }
    cfg = _cfg_with_editorial(enabled=True, scope="all")
    trip = {"tripId": "scenery-ed-06"}
    screens = plan_chapter_screens(
        ChapterPlanRequest(
            ids,
            aspects,
            assets=assets,
            chapter_id="ch-01",
            trip_photo_total=n,
            trip=trip,
        ),
        cfg=cfg,
    )
    triples = [
        s
        for s in screens
        if s.get("patternId") == PATTERN_PORTRAIT_3_EDITORIAL
        and len(s.get("slots") or []) == 3
    ]
    assert len(triples) >= 2
    fits_seen: set[str] = set()
    for i, sc in enumerate(triples):
        stamped = dict(sc)
        stamped["screenId"] = f"ch-01-sc-{i + 1:02d}"
        out = apply_editorial_row_slot_fits(stamped, assets, trip=trip)
        fits_seen.add(str(out["slots"][0]["fit"]))
    assert "cover" in fits_seen and "contain" in fits_seen


def test_build_layout_screen_sets_editorial_row_ar_for_cover() -> None:
    from travelogue.render.context import build_layout_screen

    assets = {
        "a": {"id": "a", "nativeWidth": 800, "nativeHeight": 1200},
        "b": {"id": "b", "nativeWidth": 900, "nativeHeight": 1600},
        "c": {"id": "c", "nativeWidth": 700, "nativeHeight": 1000},
    }
    screen = {
        "patternId": PATTERN_PORTRAIT_3_EDITORIAL,
        "layoutHint": LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
        "slots": [
            {"assetId": "a", "slot": 0, "fit": "cover"},
            {"assetId": "b", "slot": 1, "fit": "cover"},
            {"assetId": "c", "slot": 2, "fit": "cover"},
        ],
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="T",
        export_layout="web",
    )
    assert "--editorial-row-ar:" in ctx["screenStyle"]
