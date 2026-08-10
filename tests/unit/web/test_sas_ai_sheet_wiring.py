"""Studio AI Surface · 前端接线与埋点白名单（PRD-STUDIO-AI-SURFACE-V1）。

不跑 JS，只做字符串级校验，防止 Dock/Sheet/allowlist 漂移。
W1：壳 / 杂志 / 装帧 · W2：意图 / 建议 / 徽标 / 旧入口深链
"""

from __future__ import annotations

from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS
from travelogue.paths import ROOT

_AI_SHEET = ROOT / "templates/studio/preview-toolbar/ai-sheet.js"
_AI_CSS = ROOT / "templates/studio/preview-toolbar/ai-sheet.css"
_INIT = ROOT / "templates/studio/preview-toolbar/init-v3.js"
_ANALYTICS = ROOT / "templates/studio/js/analytics.js"
_DOCK = ROOT / "templates/studio/preview-toolbar/dock.js"
_CSS = ROOT / "templates/studio/preview-toolbar.css"
_SHEET = ROOT / "templates/studio/preview-toolbar-v3-sheet.js"
_ENTRY = ROOT / "travelogue/web/studio_entry.py"


def test_ai_sheet_module_exists_and_exports_mount() -> None:
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "export function mountAiSurface" in text
    assert "TITLE_ART_ROUTE_C_PREF_KEY" in text
    assert "travelogue.studio.titleArtRouteC" in text
    assert "/title-art/resolve" in text
    assert "startLlmNarrate" in text
    assert 'source: "ai_sheet"' in text
    assert "allowWhenSurfaceOff" in text
    assert "优先 AI 手写体" in text
    assert "不自动消耗额度" in text
    assert "titleArtUi" in text
    assert "已生成 · " in text


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
    assert "preview-toolbar/ai-sheet.css" in text


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


def test_sas_w2_intent_suggestions_badge() -> None:
    text = _AI_SHEET.read_text(encoding="utf-8")
    # AI 路由必须走 canonical /__travelogue/trips/{id}/…（非 legacy /{id}/__travelogue）
    assert "tripRestBase(tripId)" in text
    assert "/ai/intent-brief" in text
    assert "/ai/layout-critic/accept" in text
    assert "/ai/layout-feedback" in text
    assert 'tripApiBase(tripId) + "/ai/' not in text
    assert 'trackAction("intent"' in text
    assert 'trackAction("suggestion_accept"' in text
    assert 'trackAction("suggestion_dismiss"' in text
    assert "has-badge" in text
    assert "请先在分章确认" in text
    assert "了解如何开启" in text
    assert "pollJobUntilDone" in text
    assert "已按建议更新该章版面" in text
    assert "aiOpsAdminEnabled" in text
    css = _AI_CSS.read_text(encoding="utf-8")
    assert ".has-badge::after" in css


def test_sas_oq_02_advanced_follows_server_flag() -> None:
    """OQ-SAS-02 · 高级区跟 capabilities.aiOpsAdminEnabled，非 hostname 猜测。"""
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "aiOpsAdminEnabled" in text
    assert "showAdvancedSection(aiOpsAdminEnabled)" in text
    assert 'get("aiOps")' in text or "aiOps" in text


def test_sas_w2_old_entry_deeplink() -> None:
    text = _SHEET.read_text(encoding="utf-8")
    assert 'data-action="open-ai-narrate"' in text
    assert "在 AI 中打开" in text
    assert 'focus: "narrate"' in text
    # 权威入口不再直接挂 data-action=llm 开始生成
    assert 'data-action="llm"' not in text


def test_sas_w2_gate_help_inline() -> None:
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "了解如何开启" in text
    assert "TRAVELOGUE_AI_SURFACE" in text


def test_sas_w3_refine_cross_link_copy() -> None:
    """COPY-SAS-08 · W3 精修互链文案。"""
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "版式与书衣请用「精修」" in text
    assert "智能生成请用「AI」" in text
    sheet = _SHEET.read_text(encoding="utf-8")
    assert "智能生成请用顶栏「AI」" in sheet


def test_sas_w2_entry_exposes_intent_brief_ui() -> None:
    text = _ENTRY.read_text(encoding="utf-8")
    assert "def build_intent_brief_ui" in text
    assert '"intentBriefUi"' in text or "'intentBriefUi'" in text
