"""Landscape-3 editorial picker (PRD-LANDSCAPE-3-EDITORIAL-V1)."""

from __future__ import annotations

from travelogue.config.layout import Landscape3EditorialConfig, LayoutConfig
from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.rhythm import is_triple_row_pattern, layout_kind_from_pattern
from travelogue.layout_engine.planner.landscape_3_picker import (
    PATTERN_LANDSCAPE_3_ASYM_LEFT,
    PATTERN_LANDSCAPE_3_ASYM_RIGHT,
    PATTERN_LANDSCAPE_3_FILL,
    experimental_members_visible,
    pick_landscape_3_variant,
)
from travelogue.layout_engine.planner.screen_planner_stages import (
    ChapterPlanContext,
    try_landscape_run,
)


class _Cfg:
    def __init__(
        self,
        *,
        enabled: bool = True,
        allowlist: tuple[str, ...] = (
            PATTERN_LANDSCAPE_3_ASYM_LEFT,
            PATTERN_LANDSCAPE_3_ASYM_RIGHT,
        ),
        cohort: tuple[str, ...] = ("trip-dogfood",),
    ) -> None:
        self.layout = type(
            "L",
            (),
            {
                "landscape_3_editorial": Landscape3EditorialConfig(enabled=enabled),
                "mixed_proximity_seconds": 1800.0,
                "template_engine": type("TE", (), {"overrides_disable": ()})(),
            },
        )()
        self.mosaic = MosaicConfig(
            template_experiments=TemplateExperimentsConfig(
                enabled=True,
                allowlist=allowlist,
                cohort_trip_ids=cohort,
            )
        )


def _asset(*, aesthetic: float = 0.5, sharpness: float = 50.0) -> dict:
    return {"quality": {"sharpness": sharpness, "aesthetic": {"overall": aesthetic}}}


def test_picker_off_returns_fill() -> None:
    cfg = _Cfg(enabled=False)
    pick = pick_landscape_3_variant(
        ["a", "b", "c"],
        assets_map={"a": _asset(), "b": _asset(), "c": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_3_FILL
    assert pick.reason == "default_off"


def test_empty_cohort_fallback_fill() -> None:
    cfg = _Cfg(cohort=())
    assert experimental_members_visible(mosaic_cfg=cfg.mosaic, trip_id="x") == []
    pick = pick_landscape_3_variant(
        ["a", "b", "c"],
        assets_map={"a": _asset(), "b": _asset(), "c": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_3_FILL
    assert pick.reason == "fallback_fill"


def test_c02_archived_asym_invisible_even_on_star_cohort() -> None:
    cfg = _Cfg(cohort=("*",))
    visible = experimental_members_visible(
        mosaic_cfg=cfg.mosaic, trip_id="any-trip-id"
    )
    assert PATTERN_LANDSCAPE_3_ASYM_LEFT not in visible
    assert PATTERN_LANDSCAPE_3_ASYM_RIGHT not in visible


def test_c02_archived_asym_falls_back_fill() -> None:
    cfg = _Cfg()
    for assets in (
        {
            "a": _asset(aesthetic=0.95),
            "b": _asset(),
            "c": _asset(aesthetic=0.2),
        },
        {
            "a": _asset(aesthetic=0.2),
            "b": _asset(),
            "c": _asset(aesthetic=0.95),
        },
        {
            "a": _asset(aesthetic=0.5),
            "b": _asset(),
            "c": _asset(aesthetic=0.52),
        },
    ):
        pick = pick_landscape_3_variant(
            ["a", "b", "c"],
            assets_map=assets,
            cfg=cfg,
            trip_id="trip-dogfood",
        )
        assert pick.pattern_id == PATTERN_LANDSCAPE_3_FILL
        assert pick.reason == "fallback_fill"
        assert pick.variant_role == "fill"


def test_preferred_side_missing_falls_back_to_fill() -> None:
    """Left-strong but only right asym allowlisted → fill (not opposite asym)."""
    cfg = _Cfg(allowlist=(PATTERN_LANDSCAPE_3_ASYM_RIGHT,))
    pick = pick_landscape_3_variant(
        ["a", "b", "c"],
        assets_map={
            "a": _asset(aesthetic=0.95),
            "b": _asset(),
            "c": _asset(aesthetic=0.2),
        },
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_3_FILL
    assert pick.variant_role == "fill"


def test_c02_archived_tie_cannot_rotate_asym() -> None:
    cfg = _Cfg()
    first = pick_landscape_3_variant(
        ["a", "b", "c"],
        assets_map={
            "a": _asset(aesthetic=0.5),
            "b": _asset(),
            "c": _asset(aesthetic=0.5),
        },
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    second = pick_landscape_3_variant(
        ["a", "b", "c"],
        assets_map={
            "a": _asset(aesthetic=0.5),
            "b": _asset(),
            "c": _asset(aesthetic=0.5),
        },
        cfg=cfg,
        trip_id="trip-dogfood",
        recent_pattern_ids=[first.pattern_id],
    )
    assert first.pattern_id == second.pattern_id == PATTERN_LANDSCAPE_3_FILL


def test_landscape_triple_family_is_triple_kind() -> None:
    for pid in (
        PATTERN_LANDSCAPE_3_FILL,
        PATTERN_LANDSCAPE_3_ASYM_LEFT,
        PATTERN_LANDSCAPE_3_ASYM_RIGHT,
    ):
        assert is_triple_row_pattern(pid)
        assert layout_kind_from_pattern(pid) == "triple"
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    st.note_screen(PATTERN_LANDSCAPE_3_ASYM_LEFT)
    assert not st.can_emit_pattern(PATTERN_LANDSCAPE_3_ASYM_RIGHT)
    st.note_screen("screen-landscape-1")
    assert st.can_emit_pattern(PATTERN_LANDSCAPE_3_FILL)


def _landscape_ctx(*, editorial_on: bool, ids: list[str]) -> ChapterPlanContext:
    aspects: dict[str, AspectKind] = {aid: "landscape" for aid in ids}
    assets = {
        aid: {
            "aspectRatio": 1.5,
            "takenAt": f"2025-04-20T10:0{i}:00Z",
            "quality": {"sharpness": 50, "aesthetic": {"overall": 0.5}},
        }
        for i, aid in enumerate(ids)
    }
    cfg = type(
        "App",
        (),
        {
            "layout": LayoutConfig(
                landscape_3_editorial=Landscape3EditorialConfig(enabled=editorial_on)
            ),
            "mosaic": MosaicConfig(
                template_experiments=TemplateExperimentsConfig(
                    enabled=True,
                    allowlist=(
                        PATTERN_LANDSCAPE_3_ASYM_LEFT,
                        PATTERN_LANDSCAPE_3_ASYM_RIGHT,
                    ),
                    cohort_trip_ids=("trip-dogfood",),
                )
            ),
        },
    )()
    return ChapterPlanContext(
        chapter_id="ch-01",
        aspects=aspects,
        assets_map=assets,
        mix_gap=1800.0,
        med_sharp=0.5,
        trip_total=40,
        burst_seconds=12.0,
        burst_groups={},
        layout_state=ScreenLayoutPlannerState(nine_min=0, nine_max=1),
        enable_mosaic=False,
        enable_portrait_grid8=False,
        enable_food_grid=False,
        mundane_grid_buckets=(),
        use_portrait_grid8=False,
        max_per_screen=9,
        portrait_heavy=False,
        ids=list(ids),
        i=0,
        pending_portraits=[],
        screens=[],
        trip={"tripId": "trip-dogfood"},
        app_config=cfg,
    )


def test_ac_l3e_01_family_off_short_run_stays_landscape_1() -> None:
    """AC-L3E-01: editorial OFF → 三横游程仍为 landscape-1 单图，不出 asym。"""
    ctx = _landscape_ctx(editorial_on=False, ids=["a", "b", "c"])
    consumed = try_landscape_run(ctx)
    assert consumed == 3
    assert len(ctx.screens) == 3
    assert all(sc.get("patternId") == "screen-landscape-1" for sc in ctx.screens)


def test_family_on_triple_run_emits_landscape_3() -> None:
    ctx = _landscape_ctx(editorial_on=True, ids=["a", "b", "c"])
    consumed = try_landscape_run(ctx)
    assert consumed == 3
    assert len(ctx.screens) == 1
    assert ctx.screens[0]["patternId"] == PATTERN_LANDSCAPE_3_FILL
    assert "landscape3Picker" in ctx.screens[0]
