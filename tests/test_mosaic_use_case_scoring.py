"""Phase 20 · UC AR 选版加分."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutAssetAspectConfig, LayoutConfig
from travelogue.config.runtime import config_override
from travelogue.curation.mosaic.constants import PATTERN_LANDSCAPE_2, PATTERN_LANDSCAPE_3
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.curation.mosaic.use_case_scoring import (
    PATTERN_LANDSCAPE_3_SQUARE_LEFT_2,
    PATTERN_LANDSCAPE_3_WIDE_TOP_2,
    is_panorama_asset,
    is_square_asset,
    use_case_layout_multiplier,
)
from travelogue.config.mosaic import MosaicConfig


def _asset(w: int, h: int, kind: str | None = None) -> dict:
    out: dict = {"width": w, "height": h}
    if kind:
        out["aspectKind"] = kind
    return out


def test_panorama_threshold_2_5() -> None:
    cfg = LayoutAssetAspectConfig(panorama_min=2.5)
    assert is_panorama_asset(_asset(2500, 1000), cfg)
    assert not is_panorama_asset(_asset(2000, 1000), cfg)
    assert is_square_asset(_asset(1000, 1000), cfg)
    assert is_square_asset(_asset(1080, 1000), cfg)
    assert not is_square_asset(_asset(1200, 1000), cfg)


def test_use_case_all_panorama_prefers_stack_3() -> None:
    cfg = LayoutAssetAspectConfig()
    aids = ["a", "b", "c"]
    assets = {a: _asset(3000, 1000) for a in aids}
    aspects = {a: "panorama" for a in aids}
    stack_screen = {
        "patternId": PATTERN_LANDSCAPE_3,
        "slots": [
            {"slot": 0, "assetId": "a"},
            {"slot": 1, "assetId": "b"},
            {"slot": 2, "assetId": "c"},
        ],
    }
    mul, reasons = use_case_layout_multiplier(stack_screen, aids, assets, aspects)
    assert mul >= 1.10
    assert "R_UC_PANO_STACK_3" in reasons

    wide_screen = {**stack_screen, "patternId": PATTERN_LANDSCAPE_3_WIDE_TOP_2}
    mul_w, _ = use_case_layout_multiplier(wide_screen, aids, assets, aspects)
    assert mul_w < 1.0


def test_use_case_square_left_match() -> None:
    aids = ["sq", "l1", "l2"]
    assets = {
        "sq": _asset(1000, 1000, "square"),
        "l1": _asset(1600, 900, "landscape"),
        "l2": _asset(1500, 1000, "landscape"),
    }
    aspects = {"sq": "square", "l1": "landscape", "l2": "landscape"}
    screen = {
        "patternId": PATTERN_LANDSCAPE_3_SQUARE_LEFT_2,
        "slots": [
            {"slot": 0, "assetId": "sq"},
            {"slot": 1, "assetId": "l1"},
            {"slot": 2, "assetId": "l2"},
        ],
    }
    mul, reasons = use_case_layout_multiplier(screen, aids, assets, aspects)
    assert mul >= 1.06
    assert "R_UC_SQUARE_LEFT_MATCH" in reasons


def test_scorer_applies_use_case_bonus() -> None:
    app = AppConfig(
        layout=LayoutConfig(
            asset_aspect=LayoutAssetAspectConfig(use_case_scoring_enabled=True)
        )
    )
    mosaic_cfg = MosaicConfig()
    aids = ["a", "b", "c"]
    assets = {a: _asset(3000, 1000, "panorama") for a in aids}
    aspects = {a: "panorama" for a in aids}
    screen = {
        "patternId": PATTERN_LANDSCAPE_3,
        "slots": [
            {"slot": i, "assetId": aids[i], "role": "landscape", "fit": "cover"}
            for i in range(3)
        ],
    }
    with config_override(app):
        sr = score_candidate(
            screen,
            aspects=aspects,
            assets_by_id=assets,
            cfg=mosaic_cfg,
        )
    assert any(r.startswith("R_UC_") for r in sr.reason_codes)


def test_pano_stack_2_landscape() -> None:
    aids = ["a", "b"]
    assets = {a: _asset(2800, 1000, "panorama") for a in aids}
    aspects = {a: "panorama" for a in aids}
    screen = {
        "patternId": PATTERN_LANDSCAPE_2,
        "slots": [{"slot": 0, "assetId": "a"}, {"slot": 1, "assetId": "b"}],
    }
    mul, reasons = use_case_layout_multiplier(screen, aids, assets, aspects)
    assert mul >= 1.10
    assert "R_UC_PANO_STACK_2" in reasons
