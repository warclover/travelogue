"""L0 Hardening · FE 静态合同（NAS 默认面翻转 · FE-NAS-14）。"""

from __future__ import annotations

from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3] / "templates" / "studio"
DARK_COPY_JS = STUDIO / "js" / "ai-surface-dark-copy.js"


def test_import_failed_auth_recoverable_contract() -> None:
    """NAS · AC-NAS-M7/M8：默认失败面无「去配置写作引擎」；auth 分支门控。"""
    failed = (STUDIO / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
    home = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    errors = (STUDIO / "js" / "errors.js").read_text(encoding="utf-8")
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    css = (STUDIO / "homepage-v2" / "css" / "overlays.css").read_text(encoding="utf-8")

    assert "isLlmAuthRecoverable" in failed
    assert "isLlmAuthRecoverable" in errors
    assert "isAiSurfaceEnabled" in failed
    assert "isAiSurfaceEnabled() && isLlmAuthRecoverable" in failed
    # 默认面 CTA =「继续生成画册」（非本机/配置引擎话术）
    assert "继续生成画册" in failed
    assert "继续生成画册" in home
    assert "v2-failure-continue-stub" in home
    assert "v2-failure-open-settings" in home
    assert "v2-failure-open-recent" in home
    assert "去配置写作引擎" not in home
    assert "去配置写作引擎" not in failed
    assert "查看设置" in home
    assert "杂志感文案暂不可用" not in failed
    assert "import_continue_stub" in failed
    assert "forceStub: true" in failed
    assert "export function continueWithStub" in failed
    assert "v2-failure__panel--auth" in css
    # 旧 L0G constants 串已废止（auth 文案内联且仅 dark 可达）
    assert "可以继续生成本机游记" not in constants


def test_import_run_retains_pending_on_failure() -> None:
    """AC-L0G-05：失败时不得先删 activePending，否则续跑空转。"""
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    # Success/cancel clear pending; failure path must not remove before throw
    assert "sessionStorage.removeItem(SS.activePending)" in run
    assert "L0 resume: only clear pending on success/cancel" in run
    # The shared clear-before-branch pattern must be gone
    succeeded_idx = run.find('job.status === "succeeded"')
    assert succeeded_idx > 0
    pre = run[succeeded_idx - 400 : succeeded_idx]
    assert "removeItem(SS.activePending)" not in pre or "activeJobId" in pre
    # Immediately before succeeded branch we only clear job id
    block_start = run.find("L0 resume: only clear pending on success/cancel")
    assert block_start > 0
    assert 'job.status === "succeeded"' in run[block_start : block_start + 800]


def test_capability_card_l0g_copy() -> None:
    """NAS · AC-NAS-01：能力卡永不 show；无 AI 升级 CTA 串。"""
    cap = (STUDIO / "js" / "capability-card.js").read_text(encoding="utf-8")
    assert "照片留在本机，也能做成可发的画册" in cap
    assert "开始制作" in cap
    assert "以后再升级 AI 文案" not in cap
    assert "向导里可一键试用示例" in cap
    assert "开始导入" not in cap
    assert "不必先配置任何接口" not in cap
    assert "export function maybeShowCapabilityCard" in cap
    show_fn = cap.split("export function showCapabilityCard", 1)[1][:240]
    assert "return false" in show_fn


def test_import_run_passes_recoverable_flag() -> None:
    run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "recoverableWithStub" in run
    assert 'form.append("forceStub"' in run


def test_home_stub_banner_t_cap_06() -> None:
    """NAS · AC-NAS-16：home stub banner 默认可达面永不展示。"""
    banner = (STUDIO / "js" / "home-stub-banner.js").read_text(encoding="utf-8")
    boot = (STUDIO / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    assert "不配置 API 也可正常使用" not in banner
    assert "升级 AI 文案" not in banner
    assert "isAiSurfaceEnabled" in banner
    assert "export function syncHomeStubBanner" in banner
    assert "export function maybeShowHomeStubBanner" in banner
    sync_fn = banner.split("export function syncHomeStubBanner", 1)[1][:320]
    assert "isAiSurfaceEnabled" in sync_fn
    assert "hideBanner" in sync_fn
    assert "maybeShowHomeStubBanner" in boot
    assert "homeStubBanner.v1" in help_js
    assert "HELP_LS" in help_js
    assert "HELP_KEYS" not in help_js
    assert "isCapabilityCardVisible" in banner
    assert "home_stub_banner_click" in banner
    assert "clearHomeStubBannerDismissed" in help_js


def test_stub_narrate_tip_t_cap_05() -> None:
    """NAS · FE-NAS-02：stub narrate tip 永久 no-op；失败文案在 dark-copy。"""
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    dark = DARK_COPY_JS.read_text(encoding="utf-8")

    assert "stubHint.v1" in help_js
    assert "export function maybeShowStubNarrateTip" in help_js
    tip_fn = help_js.split("export function maybeShowStubNarrateTip", 1)[1][:200]
    assert "return false" in tip_fn
    assert "当前为本机文案（可随时在设置中升级）" not in help_js
    assert "maybeShowStubNarrateTip" in init
    # 默认面不调度 tip（init early-return）
    assert "if (!isAiSurfaceEnabled())" in init
    # ai_surface_dark：narrate 失败 body
    assert "仍保留本机文案" in dark
    assert "DARK_COPY.narrateFailBody" in core or "narrateFailBody" in dark
    assert "去检查配置" in core
    assert "preview_narrate_fail" in core
    assert "clearStubHintSeen" in help_js


def test_llm_settings_resume_cta_contract() -> None:
    llm = (STUDIO / "js" / "llm-settings.js").read_text(encoding="utf-8")
    analytics = (STUDIO / "js" / "analytics.js").read_text(encoding="utf-8")
    assert "studio-llm-resume" in llm
    assert "继续生成本机画册" in llm
    assert "开始导入" in llm
    assert "showResumeAfterSave" in llm
    assert "runResumeAfterLlmSettings" in llm
    assert 'source === "import_fail"' in llm
    assert 'source === "card"' in llm
    assert 'source === "home_banner"' in llm
    assert "API 用于预览里升级杂志感文案" in llm
    assert "llm_settings_resume" in analytics
    assert "import_fail_open_recent" in analytics
    # NAS：openLlmSettings 门控
    assert "if (!isAiSurfaceEnabled()) return" in llm


def test_w21_gap_copy_and_busy_banner() -> None:
    """NAS · AC-NAS-04：FirstSuccess 精确句；sheet llm 串迁 dark-copy。"""
    llm = (STUDIO / "js" / "llm-settings.js").read_text(encoding="utf-8")
    sheet = (STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    cap = (STUDIO / "js" / "capability-card.js").read_text(encoding="utf-8")
    import_run = (STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    failed = (STUDIO / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
    first = (STUDIO / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    boot = (STUDIO / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    constants = (STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    help_js = (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")
    dark = DARK_COPY_JS.read_text(encoding="utf-8")
    pipeline = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "web"
        / "studio_pipeline.py"
    ).read_text(encoding="utf-8")

    # llm modal 文案仍属 dark 可达底座（openLlmSettings 门控）
    assert "不配置也可以正常导入、排版和导出长图。配置后可在预览中生成杂志感文案。" in llm
    assert "本机文案 · 点此生成杂志感（不会自动重写）" not in sheet
    assert "sheetLlmExpect" in dark or "llmExpectReady" in dark
    assert "action:" in cap and "capability_card_cta" in cap
    assert "syncHomeStubBanner" in import_run
    assert "syncHomeStubBanner" in first
    assert "syncHomeStubBanner" in boot
    assert "forceStubNextUpload" in constants
    assert "forceStubNextUpload" in failed
    assert "forceStub: forceStub" in import_run
    assert "degrading to stub" in pipeline
    # COPY-NAS-FS-01
    assert "画册已做好，可预览与导出长图。" in first
    assert "画册已做好，可预览与导出长图。" in help_js
    assert "重新选择同一批照片" in failed
