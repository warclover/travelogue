"""Desktop LLM Setup V1 · W2 能力卡 / H7 静态门禁。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
HELP_JS = STUDIO / "js" / "help-onboarding.js"
CAP_JS = STUDIO / "js" / "capability-card.js"
BOOT = STUDIO / "homepage-v2" / "bootstrap.js"
LLM_JS = STUDIO / "js" / "llm-settings.js"


def test_capability_card_contract() -> None:
    cap = CAP_JS.read_text(encoding="utf-8")
    help_js = HELP_JS.read_text(encoding="utf-8")
    boot = BOOT.read_text(encoding="utf-8")
    settings = (STUDIO / "homepage-v2" / "settings-panel.js").read_text(encoding="utf-8")
    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert "travelogue.desktop.capabilityCard.v1" in help_js
    # FTUE v1.1 §4.2 supersedes L0G capability-card copy
    assert "照片留在本机，也能做成可发的游记" in cap
    assert "开始制作" in cap
    assert "以后再升级 AI 文案" in cap
    assert "开始导入" not in cap
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
    assert 'id="v2-settings-zone-ai"' in home
    assert 'id="studio-llm-settings-entry"' in home
    assert "配置写作引擎" in home


def test_help_h7_writing_engine_and_replay() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    llm = LLM_JS.read_text(encoding="utf-8")
    assert 'id: "H7"' in help_js
    assert "要不要配置 AI 文案" in help_js
    assert "不配置也可以导入" in help_js
    assert "点官方链接按其指引创建 Key" in help_js
    assert "保存并测试" in help_js
    assert "中国站或国际站" in help_js
    assert "连接失败可自助" in help_js
    assert "clearCapabilityCardSeen" in help_js
    assert "首页能力卡与轻状态也会再出现" in help_js
    assert "导入等待时也会再显示小提示" in help_js
    assert "clearStubHintSeen" in help_js
    assert 'itemId: "H7"' in llm


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
    sheet = (STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert "preview-sheet__llm-expect" in sheet
    assert "本机文案 · 点此生成杂志感（不会自动重写）" in sheet
    assert "llmExpect.hidden = false" in init
    assert "if (llmSetup) llmSetup.hidden = !!ok;" in init


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
