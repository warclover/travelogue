"""AC-OR-08 / 11a / R01–R03 · Output Recipe Phase A 回归护栏."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.export.output_recipe import resolve_output_recipe
from travelogue.export.platform_profiles import PlatformProfileError, resolve_profile

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_ac_or_08_c1_path_preserved_in_start_longshot() -> None:
    """Sparse/Narrative 无 pending 时仍走 maybeCopyGateThenExport（一键）."""
    src = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "_getLayoutPending" in src
    assert "showAmbiguousIntentCard" in src
    assert "maybeCopyGateThenExport(root, tripId)" in src
    # startLongshot 内：pending 拦截块须出现在意图卡调用之前
    start = src.find("export function startLongshot")
    assert start > 0
    body = src[start : start + 12000]
    pending_idx = body.find("if (_getLayoutPending())")
    intent_idx = body.find("showAmbiguousIntentCard")
    assert pending_idx > 0 and intent_idx > pending_idx


def test_ac_or_11a_studio_copy_scan() -> None:
    """用户可见「九宫格」不得绑定 wechat_moments / moments_scroll 为可点主路径."""
    client = (STUDIO / "js" / "longshot-client.js").read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    # scroll 成功态诚实声明；CTA 为长图连读
    assert 'platform === "wechat_moments"' in client
    assert "这不是九宫格" in client
    assert "长图连读已就绪" in client
    moments_block = panel.split("wechat_moments:")[1].split("moments_grid:")[0]
    assert "九宫格" not in moments_block
    assert "长图连读" in moments_block

    recipe_js = (STUDIO / "js" / "output-recipe.js").read_text(encoding="utf-8")
    assert "朋友圈 · 长图连读" in recipe_js
    assert 'intent: "moments_grid"' in recipe_js
    assert "朋友圈 · 九宫格" in recipe_js
    # scroll 选项文案不含九宫格冒充
    assert "最多 9 段，滑动连读" in recipe_js
    # preview toolbar 仍走意图卡，不把 scroll 标成九宫格
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "showAmbiguousIntentCard" in longshot
    assert "导出朋友圈 · 九宫格" not in longshot or "moments_grid" in longshot


def test_ac_or_11b_grid_bound_in_recipe_and_panel() -> None:
    """AC-OR-11b · 九宫格仅绑定 moments_grid."""
    recipe_js = (STUDIO / "js" / "output-recipe.js").read_text(encoding="utf-8")
    client = (STUDIO / "js" / "longshot-client.js").read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    assert 'intent: "moments_grid"' in recipe_js
    assert 'platform === "moments_grid"' in client
    assert "九宫格已就绪" in client
    assert 'id: "moments_grid"' in panel
    assert "这不是九宫格" in client  # scroll 诚实声明
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    assert 'result.platform === "moments_grid"' in dock
    assert "九宫格已就绪" in dock
    scroll = resolve_output_recipe(kept_n=15, enabled=True, intent="moments_scroll")
    assert scroll.platform == "wechat_moments"
    assert "九宫格" not in scroll.product_label


def test_ac_or_r01_moments_profile_still_scroll() -> None:
    moments = resolve_profile("wechat_moments")
    assert moments.segment == "content_balanced"
    assert moments.id == "wechat_moments"
    r = resolve_output_recipe(kept_n=20, enabled=True, intent="moments_scroll")
    assert r.platform == "wechat_moments"
    assert r.engine == "platform_segment"


def test_ac_or_r02_shelf_fallback_chat() -> None:
    r = resolve_output_recipe(kept_n=22, entrypoint="shelf", enabled=True)
    assert r.platform == "wechat_chat"
    assert r.intent == "chat_longshot"


def test_ac_or_r03_illegal_platform_still_400() -> None:
    with pytest.raises(PlatformProfileError) as ei:
        resolve_profile("not_a_platform")
    assert ei.value.code == "E_LNG2_INVALID_PLATFORM"


def test_phase_a_must_fix_ui_guards() -> None:
    """H-A-07/09 实现护栏：整卷确认 + 换种分享方式 + ≥50 副文."""
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    recipe = (STUDIO / "js" / "output-recipe.js").read_text(encoding="utf-8")
    dock = (STUDIO / "preview-toolbar-v3-task-dock.js").read_text(encoding="utf-8")
    assert "needsFullExportConfirm" in recipe
    assert "maybeConfirmFullExportThen" in longshot
    assert "仍导出整卷" in longshot
    assert "改用按章导出" in longshot
    assert "换种分享方式" in longshot
    assert "offerSwitchShareMethod" in longshot
    assert "actionText" in dock
    # FE-SR-08 / USR-03 · 成功面也挂换种分享（非仅 failed）
    assert 'data-share-ready-switch' in dock
    assert "正在生成可发微信的长图" in longshot
    assert "humanExportProgress" in longshot
    shelf_ls = (STUDIO / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    assert "换种分享方式" in shelf_ls
    assert 'data-share-ready-switch' in shelf_ls
    assert "offerShelfSwitchShare" in shelf_ls
    # SFH W0b · 叙事深提示文案已下沉 output-recipe-logic.js（行为等价）
    recipe_logic = (STUDIO / "js" / "output-recipe-logic.js").read_text(encoding="utf-8")
    assert "照片较多，已按章节拆成多张" in recipe_logic  # ASH-CONTRACT
    assert "output-recipe-logic.js" in recipe
    # subtitle 须被 CTA sync 消费
    assert "tipRecipe.subtitle" in longshot or "deepHint.subtitle" in longshot
    from travelogue.config.app import AppConfig
    from travelogue.config.studio import (
        OutputRecipeConfig,
        StudioConfig,
        studio_config_expose,
    )

    cfg = AppConfig()
    cfg.studio = StudioConfig(output_recipe=OutputRecipeConfig(enabled=True))
    exposed = studio_config_expose(cfg)
    assert exposed["studio"]["outputRecipe"]["enabled"] is True
    assert exposed["studio"]["outputRecipe"]["bands"]["sparseMax"] == 9
