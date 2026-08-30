"""Output Recipe V1 · resolve / kept_n / flag（AC-OR-01～06、10、13、11a）."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.export.output_recipe import (
    BandThresholds,
    OutputRecipeError,
    apply_recipe_layout_to_segment_mode,
    classify_band,
    count_kept_n,
    resolve_output_recipe,
)
from travelogue.export.output_recipe.config_loader import clear_output_recipe_config_cache
from travelogue.export.output_recipe.resolve import ambiguous_intent_options

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    clear_output_recipe_config_cache()
    yield
    clear_output_recipe_config_cache()


def test_ac_or_01_band_boundaries() -> None:
    t = BandThresholds(sparse_max=9, ambiguous_max=30)
    assert classify_band(9, t) == "sparse"
    assert classify_band(10, t) == "ambiguous"
    assert classify_band(30, t) == "ambiguous"
    assert classify_band(31, t) == "narrative"
    # 可配阈值
    t2 = BandThresholds(sparse_max=5, ambiguous_max=20)
    assert classify_band(5, t2) == "sparse"
    assert classify_band(6, t2) == "ambiguous"
    assert classify_band(21, t2) == "narrative"


def test_ac_or_02_sparse_default_chat_not_grid() -> None:
    r = resolve_output_recipe(kept_n=5, entrypoint="preview", enabled=True)
    assert r.band == "sparse"
    assert r.intent == "chat_longshot"
    assert r.platform == "wechat_chat"
    assert r.layout == "single"
    assert r.engine == "chapter_capture"
    assert r.needs_intent is False
    assert r.intent != "moments_grid"
    assert "九宫格" not in r.cta_label
    assert "发微信群" not in r.cta_label
    assert r.cta_label == "导出长图 · 导出到：微信群"


def test_ac_or_03_ambiguous_preview_needs_intent() -> None:
    r = resolve_output_recipe(kept_n=18, entrypoint="preview", enabled=True)
    assert r.band == "ambiguous"
    assert r.needs_intent is True
    assert r.platform == ""
    assert r.intent == ""


def test_ac_or_03b_ambiguous_shelf_fallback() -> None:
    r = resolve_output_recipe(kept_n=18, entrypoint="shelf", enabled=True)
    assert r.needs_intent is False
    assert r.intent == "chat_longshot"
    assert r.platform == "wechat_chat"
    assert any("预览" in h for h in r.user_hints)


def test_ac_or_03c_ambiguous_cli_requires_intent() -> None:
    with pytest.raises(OutputRecipeError) as ei:
        resolve_output_recipe(kept_n=18, entrypoint="cli", enabled=True)
    assert ei.value.code == "E_OR_INTENT_REQUIRED"


def test_ac_or_04_narrative_by_chapter_and_deep_hint() -> None:
    r = resolve_output_recipe(kept_n=40, entrypoint="preview", enabled=True)
    assert r.band == "narrative"
    assert r.layout == "by_chapter"
    assert r.intent == "chat_longshot"
    assert "按章" in r.cta_label
    assert "发微信群" not in r.cta_label
    assert r.cta_label == "按章导出长图 · 导出到：微信群"

    deep = resolve_output_recipe(kept_n=55, entrypoint="preview", enabled=True)
    assert any("按章" in h or "章节" in h for h in deep.user_hints)


def test_ac_or_05_schema_and_illegal() -> None:
    r = resolve_output_recipe(kept_n=3, enabled=True, intent="moments_scroll")
    d = r.to_dict()
    for key in (
        "recipe_id",
        "preset_id",
        "intent",
        "engine",
        "band",
        "kept_n",
        "platform",
        "layout",
        "needs_intent",
        "source",
    ):
        assert key in d

    with pytest.raises(OutputRecipeError) as ei:
        resolve_output_recipe(kept_n=3, enabled=True, intent="not_an_intent")
    assert ei.value.code == "E_OR_INVALID_INTENT"

    with pytest.raises(OutputRecipeError) as ei2:
        resolve_output_recipe(kept_n=3, enabled=True, platform="not_a_platform")
    assert ei2.value.code == "E_OR_UNKNOWN_PLATFORM"

    grid = resolve_output_recipe(kept_n=12, enabled=True, intent="moments_grid")
    assert grid.platform == "moments_grid"
    assert grid.engine == "photo_grid"


def test_ac_or_06_trip_intent_and_session_override() -> None:
    trip = {"output": {"intent": "moments_scroll"}}
    r = resolve_output_recipe(kept_n=20, trip=trip, entrypoint="preview", enabled=True)
    assert r.needs_intent is False
    assert r.intent == "moments_scroll"
    assert r.platform == "wechat_moments"
    assert r.source == "trip_override"

    # session 覆盖仅本次
    r2 = resolve_output_recipe(
        kept_n=20,
        trip=trip,
        entrypoint="preview",
        enabled=True,
        session_override={"intent": "chat_longshot"},
    )
    assert r2.intent == "chat_longshot"
    assert r2.source == "session_override"


def test_ac_or_07a_chat_and_scroll_resolve() -> None:
    chat = resolve_output_recipe(kept_n=8, enabled=True, intent="chat_longshot")
    assert chat.platform == "wechat_chat"
    scroll = resolve_output_recipe(kept_n=20, enabled=True, intent="moments_scroll")
    assert scroll.platform == "wechat_moments"
    assert scroll.engine == "platform_segment"
    assert "九宫格" not in scroll.product_label
    assert "长图连读" in scroll.product_label


def test_ac_or_10_zh_not_rewritten_by_ig_hook() -> None:
    r = resolve_output_recipe(kept_n=40, locale="zh", entrypoint="preview", enabled=True)
    assert r.intent == "chat_longshot"
    assert r.platform == "wechat_chat"
    assert r.instagram_preset_state is None

    # 显式 IG → hook_only 状态；不得作为 zh band 默认
    ig = resolve_output_recipe(
        kept_n=40,
        locale="zh",
        enabled=True,
        intent="instagram_carousel",
    )
    assert ig.instagram_preset_state == "hook_only"
    assert ig.source == "intent_choice"


def test_ac_or_13_flag_disabled_fallback() -> None:
    for n in (5, 18, 40):
        r = resolve_output_recipe(kept_n=n, entrypoint="preview", enabled=False)
        assert r.intent == "chat_longshot"
        assert r.platform == "wechat_chat"
        assert r.needs_intent is False
        assert r.source == "flag_disabled"


def test_ac_or_11a_no_jiugongge_bound_to_moments_scroll() -> None:
    """文案扫描护栏：moments_scroll / wechat_moments 不得绑「九宫格」."""
    opts = ambiguous_intent_options(phase="A")
    assert len(opts) == 2
    assert {o["intent"] for o in opts} == {"chat_longshot", "moments_scroll"}
    for o in opts:
        assert "九宫格" not in o["label"]

    scroll = resolve_output_recipe(kept_n=15, enabled=True, intent="moments_scroll")
    assert scroll.platform == "wechat_moments"
    assert "九宫格" not in scroll.product_label
    assert "九宫格" not in scroll.cta_label
    assert "长图连读" in scroll.product_label

    presets = (ROOT / "config" / "output_recipe_presets.yaml").read_text(encoding="utf-8")
    # moments_scroll preset 本体（到 packing 行为字段）不得声明九宫格
    scroll_head = presets.split("preset.moments_scroll:")[1].split("preset.moments_grid:")[0]
    scroll_fields = scroll_head.split("# Phase B")[0]
    assert "九宫格" not in scroll_fields
    assert 'label.moments_scroll: "朋友圈 · 长图连读"' in presets
    assert "九宫格" not in copy_text_for("label.moments_scroll")


def copy_text_for(key: str) -> str:
    from travelogue.export.output_recipe.config_loader import copy_text

    return copy_text(key)


def test_intent_platform_conflict() -> None:
    with pytest.raises(OutputRecipeError) as ei:
        resolve_output_recipe(
            kept_n=10,
            enabled=True,
            intent="chat_longshot",
            platform="wechat_moments",
        )
    assert ei.value.code == "E_OR_INTENT_PLATFORM_CONFLICT"


def test_count_kept_n_single_source() -> None:
    trip = {
        "curation": {"cullSummary": {"layoutEligibleCount": 12, "finalLayoutEligibleCount": 11}},
        "assets": [{"type": "image"}] * 50,
    }
    assert count_kept_n(trip) == 11
    trip2 = {"curation": {"cullSummary": {"layoutEligibleCount": 7}}}
    assert count_kept_n(trip2) == 7
    assert count_kept_n(None, fallback=4) == 4


def test_r03_unknown_platform_is_or_error() -> None:
    with pytest.raises(OutputRecipeError) as ei:
        resolve_output_recipe(kept_n=5, enabled=True, platform="totally_bogus")
    assert ei.value.code == "E_OR_UNKNOWN_PLATFORM"


def test_explicit_segment_mode_wins_over_recipe_layout() -> None:
    """User-visible full/chapter must not be overwritten by recipe.layout=single."""
    assert (
        apply_recipe_layout_to_segment_mode(
            "chapter",
            recipe_layout="single",
            platform_id="wechat_chat",
        )
        == "chapter"
    )
    assert (
        apply_recipe_layout_to_segment_mode(
            "full",
            recipe_layout="by_chapter",
            platform_id="wechat_chat",
        )
        == "full"
    )
    assert (
        apply_recipe_layout_to_segment_mode(
            "auto",
            recipe_layout="single",
            platform_id="wechat_chat",
        )
        == "full"
    )
    assert (
        apply_recipe_layout_to_segment_mode(
            "auto",
            recipe_layout="by_chapter",
            platform_id="wechat_chat",
        )
        == "chapter"
    )
    assert (
        apply_recipe_layout_to_segment_mode(
            None,
            recipe_layout="chapter",
            platform_id="wechat_chat",
        )
        == "chapter"
    )
    assert (
        apply_recipe_layout_to_segment_mode(
            "auto",
            recipe_layout="single",
            platform_id="wechat_moments",
        )
        == "auto"
    )
