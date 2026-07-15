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
    assert "本机即可生成杂志卷轴与长图" in cap
    assert "升级 AI 文案（可选）" in cap
    assert "开始导入" in cap
    assert "maybeShowCapabilityCard" in boot
    assert "markCapabilityCardSuppressHelpL1" in cap
    assert "shouldDeferHomeHelpL1ForCapabilityCard" in help_js
    assert "studio-capability-card-root" in help_js
    assert "travelogue:capability-card-done" in cap
    assert "travelogue:capability-card-done" in settings
    assert "isCapabilityCardSeen" in settings
    assert ">设置<" in home
    assert 'aria-label="设置"' in home
    assert 'v2-settings-popover__section-label">导入偏好</p>' in home


def test_help_h7_writing_engine_and_replay() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    llm = LLM_JS.read_text(encoding="utf-8")
    assert 'id: "H7"' in help_js
    assert "要不要配置 AI 文案" in help_js
    assert "不配置也可以导入" in help_js
    assert "clearCapabilityCardSeen" in help_js
    assert "首页能力卡与轻状态也会再出现" in help_js
    assert "clearStubHintSeen" in help_js
    assert 'itemId: "H7"' in llm


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
