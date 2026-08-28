"""Mixed 1P2L · p1l2 fill vs L2|P mirror (PRD-MIXED-1P2L-V1)."""

from __future__ import annotations

from travelogue.config.layout import Mixed1p2lConfig
from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_engine.planner.mixed_1p2l_picker import (
    PATTERN_MIXED_1P2L_FILL,
    PATTERN_MIXED_L2P1,
    experimental_members_visible,
    pick_mixed_1p2l_variant,
)
from travelogue.layout_engine.planner.screen_planner import (
    _can_mixed_p1_l2,
    _make_mixed_portrait_landscape_screen,
)


class _Cfg:
    def __init__(
        self,
        *,
        enabled: bool = True,
        allowlist: tuple[str, ...] = (PATTERN_MIXED_L2P1,),
        cohort: tuple[str, ...] = ("trip-dogfood",),
        tie_eps: float = 0.08,
    ) -> None:
        self.layout = type(
            "L",
            (),
            {
                "mixed_1p2l": Mixed1p2lConfig(
                    enabled=enabled,
                    strength_tie_epsilon=tie_eps,
                ),
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
    pick = pick_mixed_1p2l_variant(
        portrait_id="p",
        landscape_ids=["l1", "l2"],
        assets_map={"p": _asset(), "l1": _asset(), "l2": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_MIXED_1P2L_FILL
    assert pick.reason == "default_off"


def test_empty_cohort_fallback_fill() -> None:
    cfg = _Cfg(cohort=())
    assert experimental_members_visible(mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood") == []
    pick = pick_mixed_1p2l_variant(
        portrait_id="p",
        landscape_ids=["l1", "l2"],
        assets_map={"p": _asset(), "l1": _asset(), "l2": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_MIXED_1P2L_FILL
    assert pick.reason == "fallback_fill"


def test_strong_portrait_prefers_fill() -> None:
    cfg = _Cfg()
    pick = pick_mixed_1p2l_variant(
        portrait_id="p",
        landscape_ids=["l1", "l2"],
        assets_map={
            "p": _asset(aesthetic=0.95),
            "l1": _asset(aesthetic=0.2),
            "l2": _asset(),
        },
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_MIXED_1P2L_FILL
    assert pick.reason == "fallback_fill"


def test_c02_archived_mirror_stays_on_fill() -> None:
    cfg = _Cfg()
    assert experimental_members_visible(
        mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood"
    ) == []
    pick = pick_mixed_1p2l_variant(
        portrait_id="p",
        landscape_ids=["l1", "l2"],
        assets_map={
            "p": _asset(aesthetic=0.2),
            "l1": _asset(aesthetic=0.95),
            "l2": _asset(),
        },
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_MIXED_1P2L_FILL
    assert pick.reason == "fallback_fill"
    assert pick.pattern_id != PATTERN_MIXED_L2P1


def test_emit_off_stays_p1l2() -> None:
    """AC-M1P2L-01: OFF → still screen-portrait-1-landscape-2."""
    cfg = _Cfg(enabled=False)
    screen = _make_mixed_portrait_landscape_screen(
        "p",
        ["l1", "l2"],
        assets_map={"p": _asset(), "l1": _asset(), "l2": _asset()},
        trip={"tripId": "trip-dogfood"},
        cfg=cfg,
    )
    assert screen["patternId"] == PATTERN_MIXED_1P2L_FILL
    assert "mixed1p2lPicker" not in screen
    assert [s["assetId"] for s in screen["slots"]] == ["p", "l1", "l2"]


def test_c02_emit_on_archived_mirror_stays_p1l2() -> None:
    """C-02: archived L2|P cannot emit even when experiments are ON."""
    cfg = _Cfg()
    screen = _make_mixed_portrait_landscape_screen(
        "p",
        ["l1", "l2"],
        assets_map={
            "p": _asset(aesthetic=0.2),
            "l1": _asset(aesthetic=0.95),
            "l2": _asset(aesthetic=0.5),
        },
        trip={"tripId": "trip-dogfood"},
        cfg=cfg,
    )
    assert screen["patternId"] == PATTERN_MIXED_1P2L_FILL
    assert [s["assetId"] for s in screen["slots"]] == ["p", "l1", "l2"]


def test_hard_gate_blocks_person_portrait() -> None:
    """AC-M1P2L-04: portrait with person still rejected before picker."""
    aspects = {"p": "portrait", "l1": "landscape", "l2": "landscape"}
    assets = {
        "p": {"tags": ["person", "face"], **_asset()},
        "l1": _asset(),
        "l2": _asset(),
    }
    assert not _can_mixed_p1_l2(
        "p", ["l1", "l2"], aspects, assets, burst_seconds=12.0
    )


def test_dogfood_window_try_mixed_stays_fill_after_c02() -> None:
    """Synthetic 1P2L window · archived mirror cannot emit."""
    from travelogue.config.layout import LayoutConfig
    from travelogue.layout_contract.orientations import AspectKind
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
    from travelogue.layout_engine.planner.screen_planner_stages import (
        ChapterPlanContext,
        try_mixed_portrait_landscape,
    )

    aspects: dict[str, AspectKind] = {
        "p": "portrait",
        "l1": "landscape",
        "l2": "landscape",
    }
    assets = {
        "p": {
            "aspectRatio": 0.67,
            "takenAt": "2025-04-20T10:00:00Z",
            "quality": {"sharpness": 50, "aesthetic": {"overall": 0.2}},
        },
        "l1": {
            "aspectRatio": 1.5,
            "takenAt": "2025-04-20T10:00:05Z",
            "quality": {"sharpness": 50, "aesthetic": {"overall": 0.95}},
        },
        "l2": {
            "aspectRatio": 1.5,
            "takenAt": "2025-04-20T10:00:10Z",
            "quality": {"sharpness": 50, "aesthetic": {"overall": 0.5}},
        },
    }
    cfg = type(
        "App",
        (),
        {
            "layout": LayoutConfig(mixed_1p2l=Mixed1p2lConfig(enabled=True)),
            "mosaic": MosaicConfig(
                template_experiments=TemplateExperimentsConfig(
                    enabled=True,
                    allowlist=(PATTERN_MIXED_L2P1,),
                    cohort_trip_ids=("trip-dogfood",),
                )
            ),
        },
    )()
    ctx = ChapterPlanContext(
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
        ids=["p", "l1", "l2"],
        i=0,
        pending_portraits=[],
        screens=[],
        trip={"tripId": "trip-dogfood"},
        app_config=cfg,
    )
    assert try_mixed_portrait_landscape(ctx, "p", "l1", "l2")
    assert len(ctx.screens) == 1
    assert ctx.screens[0]["patternId"] == PATTERN_MIXED_1P2L_FILL
    assert [s["assetId"] for s in ctx.screens[0]["slots"]] == ["p", "l1", "l2"]
