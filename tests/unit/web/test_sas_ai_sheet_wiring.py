"""Studio AI Surface W1 · 前端接线与埋点白名单（PRD-STUDIO-AI-SURFACE-V1）。

不跑 JS，只做字符串级校验，防止 Dock/Sheet/allowlist 漂移。
"""

from __future__ import annotations

from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS
from travelogue.paths import ROOT

_AI_SHEET = ROOT / "templates/studio/preview-toolbar/ai-sheet.js"
_INIT = ROOT / "templates/studio/preview-toolbar/init-v3.js"
_ANALYTICS = ROOT / "templates/studio/js/analytics.js"
_DOCK = ROOT / "templates/studio/preview-toolbar/dock.js"
_CSS = ROOT / "templates/studio/preview-toolbar.css"


def test_ai_sheet_module_exists_and_exports_mount() -> None:
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "export function mountAiSurface" in text
    assert "TITLE_ART_ROUTE_C_PREF_KEY" in text
    assert 'travelogue.studio.titleArtRouteC' in text
    assert "/title-art/resolve" in text
    assert "startLlmNarrate" in text
    assert 'source: "ai_sheet"' in text
    assert "allowWhenSurfaceOff" in text
    assert "优先 AI 手写体" in text
    assert "不自动消耗额度" in text


def test_init_v3_mounts_ai_before_export_divider() -> None:
    text = _INIT.read_text(encoding="utf-8")
    assert 'from "./ai-sheet.js"' in text
    assert "mountAiSurface(root, tripId" in text
    assert "insertBefore: exportDivider" in text


def test_dock_has_ai_icon() -> None:
    text = _DOCK.read_text(encoding="utf-8")
    assert 'case "ai":' in text


def test_ai_sheet_css_imported() -> None:
    text = _CSS.read_text(encoding="utf-8")
    assert 'preview-toolbar/ai-sheet.css' in text


def test_sas_telemetry_allowlisted() -> None:
    analytics = _ANALYTICS.read_text(encoding="utf-8")
    for ev in (
        "ai_sheet_open",
        "ai_sheet_close",
        "ai_sheet_action_click",
        "ai_sheet_action_result",
        "ai_sheet_gate_view",
    ):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS, ev
        assert f'"{ev}"' in analytics, ev
