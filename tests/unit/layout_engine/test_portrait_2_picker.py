"""P2VF · portrait-2 variant picker + family streak (PRD v0.2)."""

from __future__ import annotations

from travelogue.config.layout import Portrait2VariantsConfig
from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.rhythm import (
    PORTRAIT_PAIR_PATTERN,
    is_portrait_pair_pattern,
)
from travelogue.layout_engine.planner.portrait_2_picker import (
    PATTERN_PORTRAIT_2_ASYM_LEFT,
    PATTERN_PORTRAIT_2_ASYM_RIGHT,
    PATTERN_PORTRAIT_2_FILL,
    PATTERN_PORTRAIT_2_GALLERY,
    experimental_members_visible,
    pick_portrait_2_variant,
    strength_side,
)
from travelogue.render.mobile_screens import expand_screens_for_mobile


class _Cfg:
    def __init__(
        self,
        *,
        enabled: bool = True,
        allowlist: tuple[str, ...] = (
            PATTERN_PORTRAIT_2_GALLERY,
            PATTERN_PORTRAIT_2_ASYM_LEFT,
            PATTERN_PORTRAIT_2_ASYM_RIGHT,
        ),
        cohort: tuple[str, ...] = ("trip-dogfood",),
        tie_eps: float = 0.08,
    ) -> None:
        self.layout = type(
            "L",
            (),
            {
                "portrait_2_variants": Portrait2VariantsConfig(
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


def _asset(
    *,
    aesthetic: float | None = 0.5,
    sharpness: float = 50.0,
    person: bool = False,
    featured: bool = False,
) -> dict:
    q: dict = {"sharpness": sharpness}
    if aesthetic is not None:
        q["aesthetic"] = {"overall": aesthetic}
    tags = ["person"] if person else []
    out: dict = {"quality": q, "tags": tags}
    if featured:
        out["userTier"] = "featured"
    return out


def test_picker_off_returns_fill() -> None:
    cfg = _Cfg(enabled=False)
    pick = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(), "b": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_PORTRAIT_2_FILL
    assert pick.reason == "default_off"


def test_picker_person_any_side_fill() -> None:
    cfg = _Cfg()
    pick = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(person=True), "b": _asset(aesthetic=0.9)},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_PORTRAIT_2_FILL
    assert pick.reason == "person_fill"


def test_strength_side_left_right_tie() -> None:
    assert (
        strength_side(_asset(aesthetic=0.9), _asset(aesthetic=0.2), tie_epsilon=0.08)
        == "left"
    )
    assert (
        strength_side(_asset(aesthetic=0.2), _asset(aesthetic=0.9), tie_epsilon=0.08)
        == "right"
    )
    assert (
        strength_side(_asset(aesthetic=0.5), _asset(aesthetic=0.52), tie_epsilon=0.08)
        == "tie"
    )


def test_c02_archived_variants_stay_on_fill() -> None:
    cfg = _Cfg()
    recent = [PATTERN_PORTRAIT_2_FILL, PATTERN_PORTRAIT_2_GALLERY]
    left = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.95), "b": _asset(aesthetic=0.2)},
        cfg=cfg,
        trip_id="trip-dogfood",
        recent_pattern_ids=recent,
    )
    assert left.pattern_id == PATTERN_PORTRAIT_2_FILL
    assert left.reason == "fallback_fill"

    right = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.2), "b": _asset(aesthetic=0.95)},
        cfg=cfg,
        trip_id="trip-dogfood",
        recent_pattern_ids=recent,
    )
    assert right.pattern_id == PATTERN_PORTRAIT_2_FILL
    assert right.reason == "fallback_fill"


def test_picker_tie_skips_asym() -> None:
    cfg = _Cfg()
    pick = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.5), "b": _asset(aesthetic=0.51)},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.strength_side == "tie"
    assert pick.pattern_id != PATTERN_PORTRAIT_2_ASYM_LEFT
    assert pick.pattern_id != PATTERN_PORTRAIT_2_ASYM_RIGHT


def test_picker_rotates_after_gallery() -> None:
    cfg = _Cfg()
    pick = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(aesthetic=0.5), "b": _asset(aesthetic=0.5)},
        cfg=cfg,
        trip_id="trip-dogfood",
        recent_pattern_ids=[PATTERN_PORTRAIT_2_GALLERY],
    )
    # tie → no asym; gallery recently used → prefer fill over gallery
    assert pick.pattern_id == PATTERN_PORTRAIT_2_FILL


def test_empty_cohort_hides_experiments() -> None:
    cfg = _Cfg(cohort=())
    visible = experimental_members_visible(
        mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood"
    )
    assert visible == []
    pick = pick_portrait_2_variant(
        ["a", "b"],
        assets_map={"a": _asset(), "b": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id == PATTERN_PORTRAIT_2_FILL


def test_family_streak_survives_variant_swap() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(80)
    st.note_screen(PATTERN_PORTRAIT_2_FILL)
    st.note_screen(PATTERN_PORTRAIT_2_GALLERY)
    assert st.current_portrait_pair_streak() == 2
    assert not st.can_emit_pattern(PATTERN_PORTRAIT_2_FILL)
    assert not st.can_emit_pattern(PATTERN_PORTRAIT_2_GALLERY)
    assert is_portrait_pair_pattern(PATTERN_PORTRAIT_2_ASYM_LEFT)


def test_orientation_streak_counts_variants() -> None:
    st = ScreenLayoutPlannerState.from_trip_total(80)
    st.note_screen(PATTERN_PORTRAIT_2_GALLERY)
    assert st.portrait_orientation_streak == 1
    st.note_screen(PATTERN_PORTRAIT_2_ASYM_LEFT)
    assert st.portrait_orientation_streak == 2


def test_mobile_expands_portrait_2_family() -> None:
    for pid in (
        PORTRAIT_PAIR_PATTERN,
        PATTERN_PORTRAIT_2_GALLERY,
        PATTERN_PORTRAIT_2_ASYM_LEFT,
    ):
        screens = expand_screens_for_mobile(
            [
                {
                    "patternId": pid,
                    "slots": [
                        {"assetId": "a", "role": "portrait"},
                        {"assetId": "b", "role": "portrait"},
                    ],
                    "portrait2Picker": {"reason": "rotate"},
                }
            ]
        )
        assert len(screens) == 2
        assert all(s["patternId"] == "screen-portrait-1" for s in screens)
        assert "portrait2Picker" not in screens[0]
