"""L0 Hardening · FE 静态合同（T-FAIL-01 · 能力卡 · W2 轻状态 / stub tip）。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"


def test_import_failed_auth_recoverable_contract() -> None:
    failed = (STUDIO / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    errors = (STUDIO / "js" / "errors.js").read_text(encoding="utf-8")
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    css = (STUDIO / "homepage-v2" / "css" / "overlays.css").read_text(encoding="utf-8")

    assert "isLlmAuthRecoverable" in failed
    assert "isLlmAuthRecoverable" in errors
    assert "用本机文案继续" in failed
    assert "用本机文案继续" in home
    assert "v2-failure-continue-stub" in home
    assert "v2-failure-open-settings" in home
    assert "去配置写作引擎" in home
    assert "杂志感文案暂不可用" in failed
    assert "import_continue_stub" in failed
    assert "forceStub: true" in failed
    assert "v2-failure__panel--auth" in css
    assert "可以改用本机文案继续生成游记" in constants


def test_capability_card_l0g_copy() -> None:
    cap = (STUDIO / "js" / "capability-card.js").read_text(encoding="utf-8")
    assert "本机即可生成杂志卷轴与长图" in cap
    assert "不必先配置任何接口，也能导入、预览和导出长图" in cap
    assert "升级 AI 文案（可选）" in cap
    assert "开始导入" in cap


def test_import_run_passes_recoverable_flag() -> None:
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "recoverableWithStub" in run
    assert 'form.append("forceStub"' in run


def test_home_stub_banner_t_cap_06() -> None:
    banner = (STUDIO / "js" / "home-stub-banner.js").read_text(encoding="utf-8")
    boot = (STUDIO / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    assert "不配置 API 也可正常使用" in banner
    assert "升级 AI 文案 →" in banner
    assert "maybeShowHomeStubBanner" in boot
    assert "homeStubBanner.v1" in help_js
    assert "isCapabilityCardVisible" in banner
    assert "home_stub_banner_click" in banner
    assert "clearHomeStubBannerDismissed" in help_js


def test_stub_narrate_tip_t_cap_05() -> None:
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    assert "stubHint.v1" in help_js
    assert "maybeShowStubNarrateTip" in help_js
    assert "当前为本机文案（可随时在设置中升级）" in help_js
    assert "maybeShowStubNarrateTip" in init
    assert "仍保留本机文案" in core
    assert "去检查配置" in core
    assert "preview_narrate_fail" in core
    assert "clearStubHintSeen" in help_js


def test_w21_gap_copy_and_busy_banner() -> None:
    llm = (STUDIO / "js" / "llm-settings.js").read_text(encoding="utf-8")
    sheet = (STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    cap = (STUDIO / "js" / "capability-card.js").read_text(encoding="utf-8")
    import_run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    failed = (STUDIO / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
    first = (STUDIO / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    boot = (STUDIO / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    pipeline = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "web"
        / "studio_pipeline.py"
    ).read_text(encoding="utf-8")

    assert "不配置也可以正常导入、排版和导出长图。配置后可在预览中生成杂志感文案。" in llm
    assert "本机文案 · 点此生成杂志感（不会自动重写）" in sheet
    assert "action:" in cap and "capability_card_cta" in cap
    assert "syncHomeStubBanner" in import_run
    assert "syncHomeStubBanner" in first
    assert "syncHomeStubBanner" in boot
    assert "forceStubNextUpload" in constants
    assert "forceStubNextUpload" in failed
    assert "forceStub: forceStub" in import_run
    assert "degrading to stub" in pipeline
