"""AC-CAL-01 / AC-CAL-02 / AC-CAL-10 · titleArt 渲染表面验收单测。"""

from __future__ import annotations

import io
import re

import pytest
from PIL import Image

from travelogue.cover_engine.title_art.attribution import (
    ATTR_BASE,
    ATTR_ROUTE_B,
    ATTR_ROUTE_C,
    title_art_attribution_line,
)
from travelogue.cover_engine.title_art.phash import average_hash, hamming_distance
from travelogue.cover_engine.title_art.render_b import render_title_art
from travelogue.paths import ROOT
from travelogue.render.assemble import _resolve_title_art_src

pytestmark = pytest.mark.unit

_GOLDEN = ROOT / "tests/fixtures/title_art/ac02_clean_pipeline_golden.png"
#: 256-bit aHash；允许抗锯齿/字体 hinting 轻微漂移（约 6%）。
_AC02_MAX_HAMMING = 16


def _minimal_trip(*, title_art: dict | None, opening: str = "veil-footer") -> dict:
    meta: dict = {"title": "拾光", "coverOpeningStyle": opening}
    if title_art is not None:
        meta["titleArt"] = title_art
    return {
        "tripId": "ac-title-art",
        "meta": meta,
        "coverAssetId": "a1",
        "assets": [{"id": "a1", "role": "photo"}],
    }


def test_ac_cal_01_disabled_or_missing_title_art_omits_overlay() -> None:
    """AC-CAL-01 · enabled=false / 无字段 → 不叠加贴纸。"""
    for trip in (
        _minimal_trip(title_art=None),
        _minimal_trip(title_art={"version": 1, "enabled": False, "stale": False}),
        _minimal_trip(
            title_art={
                "enabled": True,
                "stale": True,
                "openingStyleId": "veil-footer",
                "assetPath": "trip-derived/title-art/x.png",
                "position": {"x": 0.5, "y": 0.25},
            }
        ),
    ):
        src, has, *_rest = _resolve_title_art_src(trip, "veil-footer")
        assert has is False
        assert src is None


def test_ac_cal_01_enabled_whitelisted_title_art_overlays() -> None:
    trip = _minimal_trip(
        title_art={
            "enabled": True,
            "stale": False,
            "engine": "clean-pipeline-v1",
            "openingStyleId": "veil-footer",
            "coverAssetId": "a1",
            "assetPath": "trip-derived/title-art/demo.png",
            "position": {"x": 0.5, "y": 0.25},
        }
    )
    src, has, x, y, attr = _resolve_title_art_src(trip, "veil-footer")
    assert has is True
    assert src == "trip-derived/title-art/demo.png"
    assert x == "50.00%"
    assert y == "25.00%"
    assert ATTR_BASE in attr
    assert ATTR_ROUTE_B in attr


def test_resolve_title_art_src_hides_when_cover_asset_mismatches() -> None:
    """换封面后旧贴纸不叠加（coverAssetId 指纹比对）。"""
    trip = _minimal_trip(
        title_art={
            "enabled": True,
            "stale": False,
            "openingStyleId": "veil-footer",
            "coverAssetId": "old-cover",
            "assetPath": "trip-derived/title-art/x.png",
            "position": {"x": 0.5, "y": 0.25},
        }
    )
    # _minimal_trip 的 coverAssetId 是 a1，与 old-cover 不一致
    src, has, *_ = _resolve_title_art_src(trip, "veil-footer")
    assert has is False
    assert src is None


def test_resolve_title_art_src_legacy_without_cover_fingerprint_still_shows() -> None:
    """缺 coverAssetId 的历史数据兼容放行。"""
    trip = _minimal_trip(
        title_art={
            "enabled": True,
            "stale": False,
            "openingStyleId": "veil-footer",
            "assetPath": "trip-derived/title-art/legacy.png",
            "position": {"x": 0.5, "y": 0.25},
        }
    )
    src, has, *_ = _resolve_title_art_src(trip, "veil-footer")
    assert has is True
    assert src == "trip-derived/title-art/legacy.png"


def test_ac_cal_02_clean_pipeline_matches_golden_fixture() -> None:
    """AC-CAL-02 / SHD-CAL-01 · 固定 fixture + 感知哈希容差。"""
    assert _GOLDEN.is_file(), f"missing golden fixture: {_GOLDEN}"
    rendered = render_title_art("拾光")
    current = Image.open(io.BytesIO(rendered.png_bytes))
    golden = Image.open(_GOLDEN)
    dist = hamming_distance(average_hash(current), average_hash(golden))
    assert dist <= _AC02_MAX_HAMMING, f"aHash Hamming {dist} > {_AC02_MAX_HAMMING}"


def test_ac_cal_10_web_and_longshot_share_same_asset_path_contract() -> None:
    """AC-CAL-10 · 预览与长图走同一 assetPath 解析（§7 单一来源）。

    index.html / index-longshot.html 都经 ``build_render_context`` →
    ``_resolve_title_art_src``；本测钉死解析结果本身，避免两套路径漂移。
    """
    asset = "trip-derived/title-art/shared-ac10.png"
    trip = _minimal_trip(
        title_art={
            "enabled": True,
            "stale": False,
            "engine": "clean-pipeline-v1",
            "openingStyleId": "veil-footer",
            "assetPath": asset,
            "position": {"x": 0.4, "y": 0.3},
        }
    )
    src_a, has_a, *_ = _resolve_title_art_src(trip, "veil-footer")
    src_b, has_b, *_ = _resolve_title_art_src(trip, "veil-footer")
    assert has_a and has_b
    assert src_a == src_b == asset


def test_title_art_attribution_distinguishes_route_c() -> None:
    assert ATTR_ROUTE_C in title_art_attribution_line("diffusion-fixed-prompt-v1")
    assert ATTR_ROUTE_B not in title_art_attribution_line("diffusion-fixed-prompt-v1")
    assert ATTR_ROUTE_B in title_art_attribution_line("clean-pipeline-v1")


def test_cover_closing_partial_wires_title_art_attribution() -> None:
    text = (ROOT / "templates/visual-journal/partials/cover-closing.hbs").read_text(
        encoding="utf-8"
    )
    assert "titleArtAttribution" in text
    assert 'data-block="title-art-attribution"' in text


def test_studio_panel_wires_title_art_attribution_copy() -> None:
    text = (ROOT / "templates/studio/preview-toolbar/features.js").read_text(encoding="utf-8")
    assert "data-title-art-attr" in text
    assert "用你的杂志名生成封面字体 · 不生成风景图" in text
    assert "字库合成，非 AI 绘图" in text
    assert "字迹由 AI 手写体生成" in text
    assert re.search(r"setTitleArtAttribution\(", text)
