"""Landscape-2 editorial picker (PRD-LANDSCAPE-2-EDITORIAL-V1)."""

from __future__ import annotations

from travelogue.config.layout import Landscape2EditorialConfig, LayoutConfig
from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.planner.landscape_2_picker import (
    PATTERN_LANDSCAPE_2_ASYM_LEFT,
    PATTERN_LANDSCAPE_2_FILL,
    PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
    PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
    experimental_members_visible,
    pick_landscape_2_variant,
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
            PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
            PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
            PATTERN_LANDSCAPE_2_ASYM_LEFT,
        ),
        cohort: tuple[str, ...] = ("trip-dogfood",),
    ) -> None:
        self.layout = type(
            "L",
            (),
            {
                "landscape_2_editorial": Landscape2EditorialConfig(enabled=enabled),
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
    pick = pick_landscape_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(), "b": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_2_FILL
    assert pick.reason == "default_off"


def test_empty_cohort_fallback_fill() -> None:
    cfg = _Cfg(cohort=())
    assert experimental_members_visible(mosaic_cfg=cfg.mosaic, trip_id="x") == []
    pick = pick_landscape_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(), "b": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_2_FILL
    assert pick.reason == "fallback_fill"


def test_left_strength_prefers_asym() -> None:
    cfg = _Cfg()
    pick = pick_landscape_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.95), "b": _asset(aesthetic=0.2)},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_2_ASYM_LEFT


def test_tie_falls_back_fill_while_overlap_parked() -> None:
    """Overlap diagonals are parked repo-wide; tie must not emit them."""
    cfg = _Cfg()
    pick = pick_landscape_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.5), "b": _asset(aesthetic=0.52)},
        cfg=cfg,
        trip_id="trip-dogfood",
        recent_pattern_ids=[],
    )
    assert pick.pattern_id == PATTERN_LANDSCAPE_2_FILL
    assert pick.pattern_id not in (
        PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
        PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
    )


def test_overlap_ids_stay_invisible_even_when_allowlisted() -> None:
    from travelogue.layout_engine.planner.landscape_2_picker import (
        experimental_members_visible,
    )

    cfg = _Cfg(
        allowlist=(
            PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
            PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
            PATTERN_LANDSCAPE_2_ASYM_LEFT,
        )
    )
    visible = experimental_members_visible(
        mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood"
    )
    assert PATTERN_LANDSCAPE_2_OVERLAP_TLBR not in visible
    assert PATTERN_LANDSCAPE_2_OVERLAP_BLTR not in visible
    assert PATTERN_LANDSCAPE_2_ASYM_LEFT in visible


def test_landscape_pair_family_streak() -> None:
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    st.note_screen(PATTERN_LANDSCAPE_2_FILL)
    st.note_screen(PATTERN_LANDSCAPE_2_OVERLAP_TLBR)
    assert st.current_landscape_pair_streak() == 2
    assert not st.can_emit_pattern(PATTERN_LANDSCAPE_2_ASYM_LEFT)
    st.note_screen("screen-landscape-1")
    assert st.current_landscape_pair_streak() == 0
    assert st.can_emit_pattern(PATTERN_LANDSCAPE_2_FILL)


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
                landscape_2_editorial=Landscape2EditorialConfig(enabled=editorial_on)
            ),
            "mosaic": MosaicConfig(
                template_experiments=TemplateExperimentsConfig(
                    enabled=True,
                    allowlist=(
                        PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
                        PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
                        PATTERN_LANDSCAPE_2_ASYM_LEFT,
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


def test_ac_m2_01_family_off_short_run_stays_landscape_1() -> None:
    """AC-M2-01: editorial OFF → 短横游程仍为 landscape-1 单图。"""
    ctx = _landscape_ctx(editorial_on=False, ids=["a", "b"])
    consumed = try_landscape_run(ctx)
    assert consumed == 2
    assert len(ctx.screens) == 2
    assert all(sc.get("patternId") == "screen-landscape-1" for sc in ctx.screens)


def test_family_on_short_run_emits_landscape_2_pair() -> None:
    ctx = _landscape_ctx(editorial_on=True, ids=["a", "b"])
    consumed = try_landscape_run(ctx)
    assert consumed == 2
    assert len(ctx.screens) == 1
    assert ctx.screens[0]["patternId"] in (
        PATTERN_LANDSCAPE_2_FILL,
        PATTERN_LANDSCAPE_2_ASYM_LEFT,
    )
    assert "overlap" not in ctx.screens[0]["patternId"]
