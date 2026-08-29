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
    assert "一把通义百炼 Key，用于文案和封面字体" in text
    assert "连接通义百炼后可生成杂志文案" in text
    assert "本环境未开启智能能力" in text
    assert 'confirmTitle: "生成杂志感文案"' in text
    assert "将生成杂志感文案；照片仍留在本机。" in text
    assert "写作引擎" not in text
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
    css = _AI_CSS.read_text(encoding="utf-8")
    assert ".has-badge::after" in css


def test_sas_api_config_ia_and_no_advanced() -> None:
    """模型API 配置两态位置；就绪跟 connectionOk，禁止 llmAvailable 点亮封面字体。"""
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "模型API 配置" in text
    assert "模型API 配置 · 已连接" in text
    assert "本机连接" not in text
    assert "data-ai-advanced" not in text
    assert "showAdvancedSection" not in text
    assert "aiOpsAdminEnabled" not in text
    assert "connectionOk" in text
    assert "copyReady" in text
    assert "已保存未验证" in text
    assert "封面手写体需要通义百炼；未连接时使用本机字库" in text
    assert "封面字体暂时改用本机字库，不影响文案和导出" in text
    assert "imageReady" in text
    assert "连接通义百炼后可生成杂志文案" in text
    assert "去连接" in text
    assert 'data-ai-title-art-connect' in text
    # 未测通置顶、已就绪沉底
    assert "connReady ? actionsHtml + connHtml : connHtml + actionsHtml" in text
    # 未就绪默认展开
    assert '(ready ? "" : " open")' in text or "(ready ? '' : ' open')" in text
    # 禁止单一 llmAvailable 点亮封面字体
    assert "llmAvailable = copyReady" in text
    assert "st.llmAvailable === true || st.lastPingOk === true" not in text


def test_sas_w2_old_entry_deeplink() -> None:
    text = _SHEET.read_text(encoding="utf-8")
    assert 'data-action="open-ai-narrate"' in text
    assert "打开写作辅助" in text
    assert 'focus: "narrate"' in text
    # 权威入口不再直接挂 data-action=llm 开始生成
    assert 'data-action="llm"' not in text


def test_sas_w2_gate_help_inline() -> None:
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "了解如何开启" in text
    assert "TRAVELOGUE_AI_SURFACE" in text
    assert "ai_surface_enabled" in text
    assert "不会</strong>自动开启" in text or "不会自动开启" in text


def test_sas_w3_refine_cross_link_copy() -> None:
    """精修侧仍保留指向 AI 的互链；AI Sheet 内交叉提示已去掉。"""
    text = _AI_SHEET.read_text(encoding="utf-8")
    assert "preview-ai-sheet__crosshint" not in text
    assert "尝试AI文案" in text
    assert "优先尝试AI字体，耗时约几十秒" in text
    sheet = _SHEET.read_text(encoding="utf-8")
    assert "在精修里写一句" in sheet
    assert "请用顶栏「AI」" not in sheet


def test_sas_w2_entry_exposes_intent_brief_ui() -> None:
    text = _ENTRY.read_text(encoding="utf-8")
    assert "def build_intent_brief_ui" in text
    assert '"intentBriefUi"' in text or "'intentBriefUi'" in text
