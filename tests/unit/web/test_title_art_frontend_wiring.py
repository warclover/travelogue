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
    """服务端总闸关闭时不能展示按钮/勾选框；展示时默认优先 AI（可取消）。"""
    text = _features_js()
    start = text.find("export function mountCoverStyleControls")
    next_export = text.find("\nexport function", start + 1)
    chunk = text[start:next_export]
    assert "titleArtCfg.enabled" in chunk
    assert "titleArtCfg.routeCEnabled" in chunk
    assert "未通过自动用字库" in chunk
    assert "优先 AI 手写体" in chunk
    assert '"/__travelogue/config"' in chunk
    assert "TITLE_ART_ROUTE_C_PREF_KEY" in text
    assert 'pref !== "0"' in chunk
    assert "routeCChecked" in chunk
    assert "localStorage.setItem" in chunk
    assert "localStorage.getItem(TITLE_ART_ROUTE_C_PREF_KEY)" in chunk


def test_title_art_panel_uses_existing_toast_and_reload_helpers() -> None:
    """复用既有 showToolbarToast/reloadPreviewAfterLayout，不要另起一套刷新逻辑。"""
    text = _features_js()
    start = text.find("function requestTitleArt")
    assert start != -1
    end = text.find("\n    if (titleArtBtn)", start)
    chunk = text[start:end]
    assert "reloadPreviewAfterLayout()" in chunk
    assert "showToolbarToast(" in chunk
    assert "emitTitleArtResolve(" in chunk
    assert "trackStudioEvent(" in text  # 经 emitTitleArtResolve 间接调用，仍走既有通道


def test_title_art_telemetry_covers_funnel_outcomes() -> None:
    """D-CAL-27：title_art 漏斗埋点——曝光 + 全 outcome 收口，不再只在成功路径发一次。

    历史缺口：features.js 早就调了 trackStudioEvent("title_art_resolve")，但
    analytics.js / studio_events.py 白名单都没收录，事件被静默丢弃；且失败 /
    disabled / network 路径完全不发。本条锁住接线与 outcome 覆盖面。
    """
    from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS

    analytics = (ROOT / "templates/studio/js/analytics.js").read_text(encoding="utf-8")
    for ev in ("title_art_impression", "title_art_resolve"):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev

    text = _features_js()
    start = text.find("export function mountCoverStyleControls")
    next_export = text.find("\nexport function", start + 1)
    chunk = text[start : next_export if next_export > 0 else start + 30000]

    assert 'trackStudioEvent("title_art_impression"' in chunk
    assert "routeCShown" in chunk
    assert "emitTitleArtResolve" in chunk
    assert 'outcome: "success"' in chunk
    assert 'outcome: "disabled"' in chunk
    assert 'outcome: "error"' in chunk
    assert 'outcome: "network"' in chunk
    assert "routeCRequested" in chunk
    assert "fallback" in chunk
    assert "ocrVerified" in chunk
