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
    assert "travelogue.desktop.capabilityCard.v1" in help_js
    assert "本机即可生成杂志卷轴与长图" in cap
    assert "升级 AI 文案（可选）" in cap
    assert "开始导入" in cap
    # MF-01：无第三主按钮「配置写作引擎」并排
    assert "配置写作引擎" not in cap or "升级 AI 文案" in cap
    assert 'cta: "configure"' in cap or 'dismissCapabilityCard("configure")' in cap
    assert "maybeShowCapabilityCard" in boot
    assert "markCapabilityCardSuppressHelpL1" in cap
    assert "shouldDeferHomeHelpL1ForCapabilityCard" in help_js


def test_help_h7_writing_engine_and_replay() -> None:
    help_js = HELP_JS.read_text(encoding="utf-8")
    llm = LLM_JS.read_text(encoding="utf-8")
    assert 'id: "H7"' in help_js
    assert "要不要配置 AI 文案" in help_js
    assert "不配置也可以导入" in help_js
    assert "clearCapabilityCardSeen" in help_js
    assert "首页能力卡也会再出现一次" in help_js
    assert 'itemId: "H7"' in llm
