"""MEGC PR-B2 · legacy/planner equal-grid finalize self-heal (C-06)."""

from __future__ import annotations

from travelogue.config.mosaic import mosaic_from_dict
from travelogue.layout_engine.mosaic.legacy import build_legacy_screen
from travelogue.layout_engine.mosaic.megc_gate import (
    evaluate_megc_gate,
    should_block_legacy_equal_grid,
)


def _land(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "aspectKind": "landscape",
        "quality": {"sharpness": 0.9},
    }


def _cfg(*, enabled: bool, mode: str = "soft_penalty", ega_enabled: bool = True):
    return mosaic_from_dict(
        {
            "equal_grid_contract": {
                "enabled": enabled,
                "selection_gate": {
                    "enabled": enabled,
                    "mode": mode,
                    "allow_peaks": ["sixteen_nine"],
                    "score_mul": 0.62,
                },
            },
            "equal_grid_admission": {
                "enabled": ega_enabled,
            },
        }
    )


class _App:
    def __init__(self, mosaic) -> None:
        self.mosaic = mosaic


def test_should_block_legacy_on_soft_penalize() -> None:
    ids = [f"a{i}" for i in range(4)]
    assets = [_land(aid, w=3000, h=2000) for aid in ids]
    decision = evaluate_megc_gate("screen-landscape-4", assets, _cfg(enabled=True))
    assert decision.outcome == "gate_penalize"
    assert should_block_legacy_equal_grid(decision) is True


def test_should_not_block_legacy_on_cinema_allow() -> None:
    ids = [f"w{i}" for i in range(4)]
    assets = [_land(aid, w=3840, h=2160) for aid in ids]
    decision = evaluate_megc_gate("screen-landscape-4", assets, _cfg(enabled=True))
    assert decision.outcome == "gate_allow"
    assert should_block_legacy_equal_grid(decision) is False


def test_legacy_build_refuses_3x2_landscape4_when_megc_on() -> None:
    ids = [f"a{i}" for i in range(4)]
    assets_map = {aid: _land(aid, w=3000, h=2000) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    screen = build_legacy_screen(
        ids,
        4,
        aspects,
        assets_map,
        app_cfg=_App(_cfg(enabled=True, mode="soft_penalty")),
    )
    assert screen is None


def test_legacy_build_allows_16x9_landscape4_when_megc_on() -> None:
    ids = [f"w{i}" for i in range(4)]
    assets_map = {aid: _land(aid, w=3840, h=2160) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    screen = build_legacy_screen(
        ids,
        4,
        aspects,
        assets_map,
        app_cfg=_App(_cfg(enabled=True)),
    )
    assert screen is not None
    assert screen.get("patternId") == "screen-landscape-4"
    assert screen.get("megcOutcome") == "gate_allow"
    assert screen.get("megcLandPeak") == "sixteen_nine"


def test_legacy_build_unchanged_when_megc_off() -> None:
    ids = [f"a{i}" for i in range(4)]
    assets_map = {aid: _land(aid, w=3000, h=2000) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    screen = build_legacy_screen(
        ids,
        4,
        aspects,
        assets_map,
        app_cfg=_App(_cfg(enabled=False)),
    )
    assert screen is not None
    assert screen.get("patternId") == "screen-landscape-4"
    assert screen.get("megcEnabled") is False


def test_classic_planner_demotes_3x2_landscape4_when_megc_on() -> None:
    """Classic ``_plan_one_screen`` path (not build_legacy_screen) must also demote."""
    from travelogue.layout_engine.planner.screen_planner import _plan_one_screen

    ids = [f"a{i}" for i in range(4)]
    assets_map = {aid: _land(aid, w=3000, h=2000) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    screen, consumed = _plan_one_screen(
        ids,
        aspects,
        assets_map=assets_map,
        # GOLDEN-BUMP-JUSTIFICATION: EGA D-EGA-06 / AC-EGA-06 · 默认 on 时 6L 会直接命中
        # equal-grid six；这里收窄为四横输入，精确覆盖 classic landscape-4 的 MEGC demote。
        cfg=_App(_cfg(enabled=True, ega_enabled=False)),  # type: ignore[arg-type]
    )
    assert screen is not None
    assert screen.get("patternId") != "screen-landscape-4"
    assert consumed in (1, 2, 3)
    assert screen.get("patternId") in {
        "screen-landscape-1",
        "screen-landscape-2",
        "screen-landscape-3",
    }


def test_classic_planner_keeps_16x9_landscape4_when_megc_on() -> None:
    from travelogue.layout_engine.planner.screen_planner import _plan_one_screen

    ids = [f"w{i}" for i in range(4)]
    assets_map = {aid: _land(aid, w=3840, h=2160) for aid in ids}
    aspects = {aid: "landscape" for aid in ids}
    screen, consumed = _plan_one_screen(
        ids,
        aspects,
        assets_map=assets_map,
        # GOLDEN-BUMP-JUSTIFICATION: EGA D-EGA-06 / AC-EGA-06 · 收窄为四横输入，
        # 避免 default-on landscape-6 抢占，从而只验证 classic landscape-4 的 cinema allow。
        cfg=_App(_cfg(enabled=True, ega_enabled=False)),  # type: ignore[arg-type]
    )
    assert screen is not None
    assert screen.get("patternId") == "screen-landscape-4"
    assert consumed == 4
    assert screen.get("megcOutcome") == "gate_allow"
