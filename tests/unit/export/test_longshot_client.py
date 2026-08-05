"""Longshot 2.0 · longshot-client + export-panel static contracts (AC-LNG2-07*)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"
CLIENT = STUDIO / "js" / "longshot-client.js"
PANEL = STUDIO / "js" / "longshot-export-panel.js"


def test_panel_module_exists_and_exports() -> None:
    """FE-LNG2-01 / D-LNG2-28."""
    assert PANEL.is_file()
    src = PANEL.read_text(encoding="utf-8")
    for token in (
        "export function buildPanelHtml",
        "export function bindPanelDraft",
        "export function enabledPlatformsFromConfig",
        "export function ctaLabelForPlatform",
        "export function shortCtaLabelForPlatform",
        "export function confirmedExportSummary",
        "export function shouldHintSparseMoments",
        "wechat_moments",
        "xiaohongshu",
        "poster_bric",
        "album_spread",
        "clampXhsSlideCount",
        'data-studio-xhs-count="custom"',
        "长图连读",
        "导出单张海报",
        "画册印刷",
        "竖版拼贴海报",
        'if (id === "moments_grid") return;',
        "scaleHintForPlatform",
        "输出尺寸随导出目标变化",
        "data-export-confirmed-summary",
    ):
        assert token in src, f"missing: {token}"


def test_preview_toolbar_wires_export_popover_caret() -> None:
    """AC-LNG2-07 · preview dock exposes settings caret → Popover."""
    init_v3 = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    panel = PANEL.read_text(encoding="utf-8")
    assert "preview-toolbar__longshot-caret" in init_v3
    assert "preview-toolbar__longshot-split" in init_v3
    assert "openLongshotExportOptions(root)" in init_v3
    assert "startLongshot(root, tripId)" in init_v3
    assert "export function openStudioLongshotExportPanel" in longshot
    assert "ensureStudioExportPopover" in longshot
    assert "syncLongshotCtaLabel" in longshot
    assert "assertConfirmedPlatformPayload" in longshot
    assert "export_platform_mismatch" in longshot
    assert "shortCtaLabelForPlatform" in longshot
    assert "preview-toolbar__export-popover--sheet" in longshot
    # Dev default platforms include compose exits
    assert "wechat_moments" in panel and "xiaohongshu" in panel
    assert "poster_bric" in panel and "album_spread" in panel


def test_studio_panel_excludes_phase_c_platforms() -> None:
    """H-C-04 · Studio UI must not list Ins/微博/抖音/custom (Phase C backend only)."""
    src = PANEL.read_text(encoding="utf-8")
    # Studio filters out moments_grid; compose platforms allowed
    assert 'if (id === "moments_grid") return;' in src
    assert "wechat_moments" in src and "xiaohongshu" in src
    assert 'id === "album_spread"' in src or "album_spread" in src
    for banned in ("instagram", "weibo", "douyin_cover"):
        assert f'id: "{banned}"' not in src
    assert 'id: "custom"' not in src
    # xhs custom slide-count control remains allowed
    assert 'data-studio-xhs-count="custom"' in src


def test_build_longshot_request_platform_contract() -> None:
    """AC-LNG2-07b · request carries platform when opted in."""
    src = CLIENT.read_text(encoding="utf-8")
    assert "body.platform = p.platform" in src
    assert "slideCount" in src
    assert "padMode" in src


def test_format_longshot_result_moments_title() -> None:
    src = CLIENT.read_text(encoding="utf-8")
    assert "wechat_moments" in src
    assert "张长图连读已就绪" in src
    assert "这不是九宫格" in src
    assert "竖版拼贴海报已就绪" in src
    assert "publishGuide" in src
    assert "xiaohongshu" in src
    assert 'entrypoint: "shelf"' in src


def test_longshot2_analytics_events_registered() -> None:
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in (
        "longshot_export_start",
        "longshot_export_success",
        "longshot_export_fail",
        "longshot_platform_change",
    ):
        assert ev in analytics
