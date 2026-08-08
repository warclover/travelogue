"""前端 title-art 面板与后端接口的接线一致性
(PRD-COVER-CALLIGRAPHY-TITLE-V1 §8 · Studio 高级面板触发入口)。

不跑 JS，只做字符串级接线校验：防止端点路径 / config 字段名两端漂移。
"""

from __future__ import annotations

from travelogue.paths import ROOT


def _features_js() -> str:
    return (ROOT / "templates/studio/preview-toolbar/features.js").read_text(encoding="utf-8")


def test_title_art_panel_calls_the_registered_endpoint() -> None:
    text = _features_js()
    assert "/title-art/resolve" in text
    # mountCoverStyleControls 是唯一挂载点（bookends 面板会复用它）
    start = text.find("export function mountCoverStyleControls")
    assert start != -1
    next_export = text.find("\nexport function", start + 1)
    chunk = text[start : next_export if next_export > 0 else start + 20000]
    assert "data-title-art" in chunk
    assert "data-title-art-btn" in chunk
    assert "data-title-art-routec-check" in chunk
    assert "/title-art/resolve" in chunk
    assert "routeC" in chunk


def test_title_art_panel_gates_on_server_config() -> None:
    """服务端总闸关闭时不能展示按钮/勾选框（OQ-CAL-06）。"""
    text = _features_js()
    start = text.find("export function mountCoverStyleControls")
    next_export = text.find("\nexport function", start + 1)
    chunk = text[start:next_export]
    assert "titleArtCfg.enabled" in chunk
    assert "titleArtCfg.routeCEnabled" in chunk
    assert '"/__travelogue/config"' in chunk


def test_title_art_panel_uses_existing_toast_and_reload_helpers() -> None:
    """复用既有 showToolbarToast/reloadPreviewAfterLayout，不要另起一套刷新逻辑。"""
    text = _features_js()
    start = text.find("function requestTitleArt")
    assert start != -1
    end = text.find("\n    if (titleArtBtn)", start)
    chunk = text[start:end]
    assert "reloadPreviewAfterLayout()" in chunk
    assert "showToolbarToast(" in chunk
    assert "trackStudioEvent(" in chunk
