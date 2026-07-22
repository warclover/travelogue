"""Desktop LLM Setup V1 · W2 能力卡 / H7 静态门禁（NAS 默认面翻转 · FE-NAS-14）。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
HELP_JS = STUDIO / "js" / "help-onboarding.js"
CAP_JS = STUDIO / "js" / "capability-card.js"
BOOT = STUDIO / "homepage-v2" / "bootstrap.js"
LLM_JS = STUDIO / "js" / "llm-settings.js"
DARK_COPY_JS = STUDIO / "js" / "ai-surface-dark-copy.js"


def test_capability_card_contract() -> None:
    """NAS · AC-NAS-01：默认可达面无能力卡 show 路径；DOM/CSS 底座可留。"""
    cap = CAP_JS.read_text(encoding="utf-8")
    help_js = HELP_JS.read_text(encoding="utf-8")
    boot = BOOT.read_text(encoding="utf-8")
    settings = (STUDIO / "homepage-v2" / "settings-panel.js").read_text(encoding="utf-8")
    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    dark = DARK_COPY_JS.read_text(encoding="utf-8")

    assert "travelogue.desktop.capabilityCard.v1" in help_js
    # 中性标题/主 CTA 可留在 DOM 工厂；AI 升级串不得出现在默认可达面
    assert "照片留在本机，也能做成可发的游记" in cap
    assert "开始制作" in cap
    assert "以后再升级 AI 文案" not in cap
    assert "开始导入" not in cap
    # NAS：show / maybeShow 为永久 no-op（dark 亦不恢复 · D-NAS-20）
    assert "export function maybeShowCapabilityCard" in cap
    assert "export function showCapabilityCard" in cap
    assert "return false;" in cap.split("export function showCapabilityCard", 1)[1][:200]
    assert "maybeShowCapabilityCard" in boot
    assert "markCapabilityCardSuppressHelpL1" in cap
    assert "shouldDeferHomeHelpL1ForCapabilityCard" in help_js
    assert "studio-capability-card-root" in help_js
    assert "travelogue:capability-card-done" in cap
    assert "travelogue:capability-card-done" in settings
    assert "trapFocus" in cap
    assert "SHEET_FOCUSABLE" in cap
    assert 'aria-modal", "true"' in cap or "aria-modal" in cap
    assert "isCapabilityCardSeen" in settings
    assert ">设置<" in home
    assert 'aria-label="设置"' in home
    assert "导入与分析" in home
    # AI zone 默认 hidden + nas-allow；禁词「配置写作引擎」不在默认 HTML
    assert 'id="v2-settings-zone-ai"' in home
    assert 'data-nas-allow="1"' in home
    assert "hidden" in home.split('id="v2-settings-zone-ai"', 1)[1][:120]
    assert 'id="studio-llm-settings-entry"' in home
    assert "配置写作引擎" not in home
    # ai_surface_dark：写作引擎 CTA 文案冻结在 dark-copy
    assert "配置写作引擎" in dark
    assert "settingsConfigure" in dark
    # UI Detail Wave5 · styles live in CSS, not JS-injected forest palette
    assert "studio-capability-card-style" not in cap
    assert "#2f6b55" not in cap
    home_css = (STUDIO / "studio-home-v2.css").read_text(encoding="utf-8")
    assert "capability-card.css" in home_css
    cap_css = (STUDIO / "capability-card.css").read_text(encoding="utf-8")
    assert "--studio-panel-ink" in cap_css
    assert "--studio-panel-title-size" in cap_css


def test_help_h7_writing_engine_and_replay() -> None:
    """NAS · AC-NAS-03/16：默认帮助无 H7；重播不唤醒能力卡/stub。"""
    help_js = HELP_JS.read_text(encoding="utf-8")
    llm = LLM_JS.read_text(encoding="utf-8")
    assert 'id: "H7"' not in help_js
    assert "要不要配置 AI 文案" not in help_js
    assert "不配置也可以导入" not in help_js
    assert "H7 已移除" in help_js or "NAS" in help_js
    # 重播不得 clear 能力卡 / stub seen（M9）
    replay = help_js.split("export function replayHelpHints", 1)[1].split(
        "export function", 1
    )[0]
    assert "clearCapabilityCardSeen" not in replay
    assert "clearStubHintSeen" not in replay
    assert "clearHomeStubBannerDismissed" not in replay
    # 底座仍导出 clear*（供 dark / 测试），但默认 replay 不用
    assert "export function clearCapabilityCardSeen" in help_js
    assert "export function clearStubHintSeen" in help_js
    # ai_surface_dark：llm modal 仍可深链 H7（门控后才可达）
    assert 'itemId: "H7"' in llm
    assert "isAiSurfaceEnabled" in llm
    assert "if (!isAiSurfaceEnabled()) return" in llm


def test_llm_key_official_links_simplified() -> None:
    """简化设计：只链官方申请入口，不在应用内复述注册教程。"""
    llm = LLM_JS.read_text(encoding="utf-8")
    assert "platform.deepseek.com/api_keys" in llm
    assert "bailian.console.aliyun.com" in llm
    assert "help.aliyun.com/zh/model-studio/get-api-key" in llm
    assert "按其页面指引创建并复制" in llm
    assert "LLM_KEY_LINKS" in llm
    assert "LLM_DEFAULT_BASE" in llm
    assert "clearForeignBaseUrl" in llm
    assert "dashscope.aliyuncs.com/compatible-mode/v1" in llm
    # 旧 DashScope 控制台域名不再作为主入口
    assert "dashscope.console.aliyun.com" not in llm


def test_wea_w1_save_and_ping_region_footnote_markers() -> None:
    """WEA W1 FE 契约：保存并测试 · 地域 · 脚注 · 四态。"""
    llm = LLM_JS.read_text(encoding="utf-8")
    settings = (STUDIO / "homepage-v2" / "settings-panel.js").read_text(encoding="utf-8")
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    assert "保存并测试" in llm
    assert 'id="studio-llm-save-ping"' in llm
    assert "仅测试连接" in llm
    assert 'name="studio-llm-region"' in llm
    assert "中国站" in llm and "国际站" in llm
    assert "dashscope-intl.aliyuncs.com" in llm
    assert "API Key 只保存在你的电脑" in llm
    assert "费用由该账户结算" in llm
    assert "导入仍用本机文案" in llm
    assert "已保存未验证" in llm
    assert "is-warn" in llm
    assert "已保存未验证" in settings
    assert "llm_save_and_ping" in analytics
    assert "llm_provider_change" in analytics
    assert "llm_switch_confirm" in analytics
    assert 'trackStudioEvent("llm_save_and_ping"' in llm
    assert "body.persist = false" in llm


def test_wea_w2_model_switch_confirm_markers() -> None:
    """WEA W2：模型下拉 · 切换覆盖确认。"""
    llm = LLM_JS.read_text(encoding="utf-8")
    assert 'id="studio-llm-model"' in llm
    assert "LLM_MODELS" in llm
    assert "qwen-turbo" in llm
    assert "deepseek-reasoner" in llm
    assert 'id="studio-llm-model-custom"' in llm
    assert "confirmProviderSwitchIfNeeded" in llm
    assert "覆盖并继续" in llm
    assert 'trackStudioEvent("llm_switch_confirm"' in llm
    assert "persist: true" in llm


def test_mf06_llm_expect_visible_when_available() -> None:
    """NAS · AC-NAS-05：默认面不渲染 llm-expect；dark 文案在 ai-surface-dark-copy。"""
    sheet = (STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    dark = DARK_COPY_JS.read_text(encoding="utf-8")

    assert "bookCopyRefreshHtml" in sheet
    assert "isAiSurfaceEnabled" in sheet
    assert 'if (!isAiSurfaceEnabled()) return ""' in sheet
    # 旧默认串已迁出默认可达面
    assert "本机文案 · 点此生成杂志感（不会自动重写）" not in sheet
    assert "配置写作引擎" not in sheet
    # ai_surface_dark：expect / setup 冻结串
    assert "preview-sheet__llm-expect" in sheet
    assert "DARK_COPY.sheetLlmExpect" in sheet or "sheetLlmExpect" in dark
    assert "AI 文案已就绪；重新生成不会自动覆盖你的手动修改。" in dark
    assert "当前为本机文案 · 配置写作引擎后可升级" in dark
    # 默认面 early-return，不跑 llm 状态机
    assert "if (!isAiSurfaceEnabled())" in init
    assert 'copy_branch: "nas_hidden"' in init


def test_llm_settings_shows_trips_dir() -> None:
    llm = LLM_JS.read_text(encoding="utf-8")
    assert "tripsDir" in llm
    assert "相册位置" in llm
    assert "studioModal" in llm


def test_llm_narrate_click_analytics() -> None:
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    assert 'trackStudioEvent("llm_narrate_click"' in core
    assert "llm_narrate_click" in analytics
