"""Mixed 1L1P · L|P / P|L picker (PRD-MIXED-1L1P-V1)."""

from __future__ import annotations

from travelogue.config.layout import Mixed1l1pConfig
from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_engine.planner.mixed_1l1p_picker import (
    PATTERN_MIXED_LP,
    PATTERN_MIXED_PL,
    experimental_members_visible,
    pick_mixed_1l1p_variant,
)


class _Cfg:
    def __init__(
        self,
        *,
        enabled: bool = True,
        allowlist: tuple[str, ...] = (PATTERN_MIXED_LP, PATTERN_MIXED_PL),
        cohort: tuple[str, ...] = ("trip-dogfood",),
        tie_eps: float = 0.08,
    ) -> None:
        self.layout = type(
            "L",
            (),
            {
                "mixed_1l1p": Mixed1l1pConfig(
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


def test_picker_off_returns_none() -> None:
    cfg = _Cfg(enabled=False)
    pick = pick_mixed_1l1p_variant(
        portrait_id="p",
        landscape_id="l",
        assets_map={"p": _asset(), "l": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id is None
    assert pick.reason == "default_off"


def test_empty_cohort_invisible() -> None:
    cfg = _Cfg(cohort=())
    assert experimental_members_visible(mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood") == []
    pick = pick_mixed_1l1p_variant(
        portrait_id="p",
        landscape_id="l",
        assets_map={"p": _asset(), "l": _asset()},
        cfg=cfg,
        trip_id="trip-dogfood",
    )
    assert pick.pattern_id is None
    assert pick.reason == "fallback_split"


def test_missing_trip_id_invisible() -> None:
    cfg = _Cfg()
    pick = pick_mixed_1l1p_variant(
        portrait_id="p",
        landscape_id="l",
        assets_map={"p": _asset(), "l": _asset()},
        cfg=cfg,
        trip_id=None,
    )
    assert pick.pattern_id is None


def test_c02_archived_mirrors_split_even_when_allowlisted() -> None:
    cfg = _Cfg()
    assert experimental_members_visible(
        mosaic_cfg=cfg.mosaic, trip_id="trip-dogfood"
    ) == []
    for aesthetic_p, aesthetic_l in ((0.95, 0.2), (0.2, 0.95), (0.5, 0.5)):
        pick = pick_mixed_1l1p_variant(
            portrait_id="p",
            landscape_id="l",
            assets_map={
                "p": _asset(aesthetic=aesthetic_p),
                "l": _asset(aesthetic=aesthetic_l),
            },
            cfg=cfg,
            trip_id="trip-dogfood",
        )
        assert pick.pattern_id is None
        assert pick.reason == "fallback_split"
        assert pick.pattern_id not in (PATTERN_MIXED_LP, PATTERN_MIXED_PL)
