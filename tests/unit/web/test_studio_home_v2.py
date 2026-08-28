"""Studio 首页 v2（GET /）路由 + 冒烟测试（Phase 0 / M20-a · M21-c）。

覆盖：
- GET / 返回 200 且含 v2 Bento 标记
- GET /classic 应急 classic 冻结页
- v2 CSS / JS 模块存在且含关键符号
- demo-showcase manifest.json 结构合法
"""



from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

import pytest
import yaml

from tests._repo_root import repo_root
from tests.integration.studio.test_studio_server import _free_port, _post_json, _start_studio_server
from tests.unit.web._ash_source_contracts import (
    assert_exported_array_members,
    assert_exported_const,
    assert_exported_string_const,
)
from tests.unit.web._studio_home_v2_css import read_studio_home_v2_css_bundle
from travelogue.web.studio_handlers.paths import STUDIO_EVENT_PATH
from travelogue.web.studio_jobs import reset_job_store

REPO_ROOT = repo_root(__file__)
STUDIO_DIR = REPO_ROOT / "templates" / "studio"
V2_CSS_BUNDLE = read_studio_home_v2_css_bundle(STUDIO_DIR)


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


V2_HOME_MARKERS = (
    'data-homepage-variant="v2"',
    "studio-home-v2.css",
    "studio-modal.css",
    "homepage-v2/bootstrap.js",
    "v2-bento",
    "v2-carousel",
    "v2-phone",
    "v2-bench",
    "v2-demo-flag",
    "每一个瞬间",
    "都值得再次相遇",
    "选择照片文件夹",
    "试用示例",
    "示例作品",
    "v2-unsupported",
    "v2-unsupported-copy",
    # M20-d · Import Wizard（唯一入口）
    "v2-import-wizard",
    'role="dialog"',
    'aria-modal="true"',
    "选择照片文件夹",
    "一本画册一个文件夹，无需上传照片，隐私无忧",
    "v2-wizard-album-path",
    "v2-wizard-album-upload",
    "上传小文件夹（建议 ≤200MB）",
    "试用《斯里兰卡见闻录》",
    "v2-wizard-demo-album",
    'id="v2-bench-quick-actions"',
    "v2-wizard-close-pick",
    # M20-c · Lightbox
    "v2-lightbox",
    "v2-lightbox-scroll",
    "v2-lightbox-close",
    # FirstSuccess overlay（§9.3）
    "v2-first-success",
    "v2-success-open",
    "v2-success-stay",
    "v2-success-details",
    "v2-wizard-photo-mode-recommended",
    "v2-wizard-photo-mode-keep-all",
    "打开画册预览",
    # M20 · 设置 Popover（手风琴五区 · 导入与分析 · D-DLLM-03 AI zone）
    "v2-bench-layout-lab",
    "v2-settings-toggle",
    "v2-settings-popover",
    "v2-settings-close",
    "设置",
    "导入与分析",
    "导入偏好",
    'id="studio-cfg-clustering"',
    'id="studio-cfg-vision"',
    'id="v2-settings-zone-ai"',
    'id="studio-llm-settings-entry"',
    "选择照片文件夹",
    "无需上传照片 · 个人隐私无忧 · 智能拼图排版 · 一键多种输出",
    # Import Failed overlay
    "v2-failure",
    "v2-failure-retry",
    "v2-failure-stay",
)

CLASSIC_FREEZE_MARKERS = (
    'data-studio-v="4"',
    "studio-hero",
    "studio-hero-empty",
    "Classic 首页（Deprecated）",
)


@pytest.mark.e2e
def test_studio_home_v2_route(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v2", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        for marker in V2_HOME_MARKERS:
            assert marker in html, marker
        # token 占位符已被替换（test server token=None → "")
        assert "__STUDIO_TOKEN__" not in html
        assert "\ufffd" not in html
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/__studio/studio-modal.css", timeout=10
        ) as css_resp:
            css = css_resp.read().decode("utf-8")
            assert css_resp.status == 200
            assert ".studio__modal-backdrop" in css
            assert "position: fixed" in css
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_v2_route_redirects_to_root(tmp_path: Path) -> None:
    """M21-c · GET /v2 收敛到 /（302）。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v2", method="GET")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            opener.open(req, timeout=10)
        assert excinfo.value.code == 302
        assert excinfo.value.headers.get("Location") == "/"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_v2_head_redirects_to_root(tmp_path: Path) -> None:
    """PMX BE-PMX-22 · HEAD /v2 与 GET 同为 302 → /。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v2", method="HEAD")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            opener.open(req, timeout=10)
        assert excinfo.value.code == 302
        assert excinfo.value.headers.get("Location") == "/"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_classic_unchanged_on_gate_off(tmp_path: Path, monkeypatch) -> None:
    """gate off 时 GET / 仍为 classic 冻结页，且不加载 v2 bundle。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        for marker in CLASSIC_FREEZE_MARKERS:
            assert marker in html, marker
        assert "studio-home-v2.css" not in html
        assert "homepage-v2/bootstrap.js" not in html
    finally:
        server.shutdown()
        server.server_close()


def test_studio_home_v2_css_split_modules() -> None:
    entry = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
    assert '@import url("homepage-v2/css/tokens.css")' in entry
    assert '@import url("homepage-v2/css/dev-panel.css")' in entry
    for name in ("tokens.css", "bento.css", "import-wizard.css", "chrome.css"):
        assert (STUDIO_DIR / "homepage-v2" / "css" / name).is_file(), name
    assert "--v2-ink:" in V2_CSS_BUNDLE
    assert "prefers-reduced-motion: reduce" in V2_CSS_BUNDLE


def test_studio_home_v2_css_present() -> None:
    css = V2_CSS_BUNDLE
    for sel in (
        ".v2-bento",
        ".v2-carousel",
        ".v2-phone",
        ".v2-bench",
        ".v2-demo-flag",
        ".v2-shared__bg",
        ".v2-unsupported",
    ):
        assert sel in css, sel
    assert "--v2-create-card-bg-image:" in css
    assert "--v2-create-card-bg-image-hover:" in css
    assert "--v2-cta-bg-image:" in css
    create_card = css.split(".v2-bench__create-card {", 1)[1].split("}", 1)[0]
    assert "backdrop-filter" not in create_card
    assert "var(--v2-create-card-bg-image)" in create_card
    cta_primary = css.split(".v2-bench__cta-primary {", 1)[1].split("}", 1)[0]
    assert "var(--v2-cta-bg-image)" in cta_primary
    assert "#c9920f" not in cta_primary


def test_studio_home_v2_theme_palette_options() -> None:
    """新增 mist / folio / atelier 三套中国传统色主题。"""
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    css = V2_CSS_BUNDLE
    store = (STUDIO_DIR / "homepage-v2" / "store.js").read_text(encoding="utf-8")
    theme_js = (STUDIO_DIR / "homepage-v2" / "theme.js").read_text(encoding="utf-8")
    boot = (STUDIO_DIR / "homepage-v2" / "theme-boot.js").read_text(encoding="utf-8")

    assert 'src="/__studio/homepage-v2/theme-boot.js"' in html

    for theme_id, label in (
        ("mist", "雾蓝纸本"),
        ("folio", "纸墨装帧"),
        ("atelier", "木紫文艺"),
    ):
        assert f'<option value="{theme_id}">{label}</option>' in html, theme_id
        assert f':root[data-v2-theme="{theme_id}"]' in css, theme_id
        assert '--v2-primary: #' in css.split(f':root[data-v2-theme="{theme_id}"]', 1)[1].split("}", 1)[0], theme_id
        assert f"{theme_id}:" in store, theme_id
        assert f"{theme_id}: 1" in boot, theme_id

    # ASH-CONTRACT: theme registry — field-level (not exact array formatting)
    assert_exported_array_members(
        store,
        "V2_THEME_IDS",
        ("classic", "dawn", "mist", "folio", "atelier"),
        where="store.js",
    )
    assert_exported_string_const(store, "V2_THEME_DEFAULT", "mist", where="store.js")
    assert_exported_array_members(
        store,
        "V2_THEME_FEATURED",
        ("mist", "folio", "dawn", "classic"),
        where="store.js",
    )
    assert_exported_array_members(
        store,
        "V2_THEME_MORE",
        ("atelier", "sky"),
        where="store.js",
    )
    assert_exported_const(store, "V2_THEME_LABELS", where="store.js")
    assert "V2_THEME_LABELS" in theme_js, "theme.js should reference V2_THEME_LABELS"
    assert '<optgroup label="精选">' in html
    assert '<optgroup label="更多">' in html
    assert 'DEFAULT_THEME = "mist"' in boot
    assert ':root[data-v2-theme="folio"] .v2-bento__veil' in css
    assert ':root[data-v2-theme="atelier"] .v2-bento__veil' in css
    assert ':root[data-v2-theme="mist"] .v2-shelf' in css
    # classic：书架浅色纸本须覆盖全局暗底 token，避免续看卡标题深色叠深色
    assert ':root[data-v2-theme="classic"] .v2-shelf' in css
    classic_shelf = css.split(':root[data-v2-theme="classic"] .v2-shelf {', 1)[1].split("}", 1)[0]
    assert "--v2-surface: #fffdf8" in classic_shelf
    assert "--v2-ink: #14110d" in classic_shelf
    assert ".v2-shelf__resume-text strong" in css
    # UI Detail Wave7 · sky 显式主题，不再靠 removeAttribute
    assert ':root[data-v2-theme="sky"]' in css
    assert 'setAttribute("data-v2-theme", "sky")' in boot
    assert 'removeAttribute("data-v2-theme")' not in boot
    assert 'removeAttribute("data-v2-theme")' not in store


def test_studio_home_v2_js_modules_present() -> None:
    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    bento = (STUDIO_DIR / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    manifest_js = (STUDIO_DIR / "homepage-v2" / "manifest.js").read_text(encoding="utf-8")
    store = (STUDIO_DIR / "homepage-v2" / "store.js").read_text(encoding="utf-8")

    for js in (bootstrap, bento, manifest_js, store):
        assert "\ufffd" not in js

    # 状态路由 + 视口闸
    assert "routeFinalState" in bootstrap
    assert "IdleEmpty" in bootstrap and "IdleReturning" in bootstrap
    assert "Importing" in bootstrap
    assert "initViewportWatch" in bootstrap  # 视口闸（M20-f 抽到 viewport-logic）
    assert "initAdvancedOptionsPanel" in bootstrap
    assert "initSettingsPanel" in bootstrap
    settings = (STUDIO_DIR / "homepage-v2" / "settings-panel.js").read_text(encoding="utf-8")
    assert "bindAdvancedConfigControls" in settings
    assert "syncCtaPlacement" in bento
    assert "initHomepageCta" in bento
    assert "syncHomepageCta" in bento
    cta = (STUDIO_DIR / "homepage-v2" / "homepage-cta.js").read_text(encoding="utf-8")
    assert "resolveHomepageCta" in cta
    assert "renderBentoEmpty" in bento
    assert "renderBackground" in bento
    assert "initCarousel" in bento  # M20-b：carousel 由独立模块渲染
    assert "initPhoneStrip" in bento
    assert "initPhoneStrip" in (STUDIO_DIR / "homepage-v2" / "phone-strip.js").read_text(encoding="utf-8")
    assert "longshotPages" in manifest_js
    # 复用 v3 共享模块（最小 diff）
    assert "../js/constants.js" in bootstrap
    assert "isDemoTrip" in bootstrap
    # 加法 sessionStorage 键，不改既有键
    assert "homepageVariant" in store


def test_trip_preview_prefers_latest_trip_not_export_flag() -> None:
    """最近一本应按最新画册，而不是优先旧 longshot 导出。"""
    trip_preview = (STUDIO_DIR / "homepage-v2" / "trip-preview.js").read_text(encoding="utf-8")
    assert "return userTrips[0];" in trip_preview
    assert "withExport" not in trip_preview


def test_studio_home_v2_import_sheet_modules() -> None:
    """M20-d · Import entry/Wizard + 导入编排，复用 v3 共享原语（非复制视图）。"""
    entry = (STUDIO_DIR / "homepage-v2" / "import-entry.js").read_text(encoding="utf-8")
    wizard = (STUDIO_DIR / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    wizard_logic = (STUDIO_DIR / "homepage-v2" / "import-wizard-logic.js").read_text(
        encoding="utf-8"
    )
    run = (STUDIO_DIR / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "refreshTripsForImportSuccess" in run
    assert not (STUDIO_DIR / "homepage-v2" / "import-sheet.js").is_file()
    assert not (STUDIO_DIR / "homepage-v2" / "import-flags.js").is_file()

    for js in (entry, wizard, wizard_logic, run):
        assert "\ufffd" not in js

    # 薄编排层（RET-3 · Wizard 唯一入口）
    assert "openImportSheet" in entry and "initImportSheet" in entry
    assert "import-wizard.js" in entry and "openImportWizard" in entry
    assert "import-sheet.js" not in entry

    # 开始制作后清草稿；书架「新建」强制回选夹
    assert 'persistDraft: false' in wizard
    assert "removeItem(IMPORT_DRAFT_KEY)" in wizard
    assert 'forceStep: "pick"' in (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")

    # Wizard v3（PRD v3.0.1）+ A.1
    assert "openImportWizard" in wizard and "startV2Import" in wizard
    assert "wizard_step_view" in wizard
    assert "填写细节 →" in wizard_logic
    assert "requestCloseWizard" in wizard
    assert "photo_count_hint_show" in wizard
    assert "resetPrefillableFieldsForNewFolder" in wizard
    assert "syncFineSnapshotAfterPrefill" in wizard
    assert "_countHintTrackedKey" in wizard
    assert "照片处理：全部保留（已跳过挑选 / 连拍去重 / 低清过滤）" in wizard
    assert "照片处理：智能挑选已开启 · 连拍自动择优" in wizard
    assert "已关闭智能挑选 · 连拍自动择优" not in wizard
    assert "advanced_fields_toggle" in wizard
    assert "close_confirm" in wizard
    assert "updateTemplateModeHint" in wizard
    assert "wireTemplateSelect" in wizard
    assert "导入向导加载失败" in entry

    # Sheet a11y / pick / upload 已迁到 Wizard
    assert "trapFocus" in wizard
    assert "Escape" in wizard
    assert "SHEET_FOCUSABLE" in wizard
    assert "/__travelogue/pick-folder" in wizard
    assert "submitWithPath" in wizard
    assert "v2-wizard-album-upload" in wizard or "handleUploadInput" in wizard
    assert "confirmLargeUpload" in wizard
    assert "UPLOAD_BYTES_SOFT_LIMIT" in wizard
    assert "仍要上传" in wizard
    assert "建议总量≤200MB" in wizard
    assert "startV2UploadImport" in wizard

    # 导入编排复用共享原语
    assert "startV2Import" in run and "resumeV2ImportIfAny" in run
    assert "startV2UploadImport" in run
    assert "postMultipartImportV2" in run
    assert "来源 · 浏览器上传" in run or "浏览器上传" in run
    assert "../js/job-poll.js" in run
    assert "../js/http.js" in run
    assert "pollJobUntilDone" in run
    # P2 · source 路径用 textContent，不用 innerHTML 拼接
    assert "textContent" in run
    assert "v2-import-panel__source" in run
    assert "replaceChildren" in run
    # sessionStorage 形状对齐 v3（跨页续跑）
    assert "SS.activeJobId" in run and "SS.activePending" in run
    assert "studioModal" in run
    assert "showFirstSuccess" in run
    assert "showImportFailed" in run
    # in-product 禁用「AI」字样（§3.2 / §15）
    assert "AI 自动生成" not in wizard and "AI 自动生成" not in run


def test_studio_home_v2_import_wizard_a1_dom_smoke() -> None:
    """A.1 · Wizard DOM：无重新选择、信任行、进阶折叠、张数 hint。"""
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    assert "v2-wizard-back-confirm" not in html
    assert 'id="v2-wizard-trust"' in html
    assert 'id="v2-wizard-trust-fine"' in html
    assert 'id="v2-wizard-count-hint"' in html
    assert 'id="v2-wizard-advanced"' in html
    assert "按这些偏好开始 →" in html
    assert "优先出微信长图，适合马上分享" in html
    assert "输入画册相关信息，定制更多细节" in html
    assert "设置智能选片规则" in html
    assert "根据不同照片数量（上限250张），生成画册耗时不同，通常需要1-8分钟" in html
    assert "不会把原片再复制进 Travelogue" not in html
    assert "不会覆盖已有画册" not in html
    assert 'id="v2-wizard-cover-note"' not in html
    assert 'id="v2-wizard-storage-ref-note"' not in html
    assert 'id="v2-wizard-change-storage"' not in html
    assert "更改存储设置" not in html
    assert "#v2-wizard-title-confirm" in V2_CSS_BUNDLE
    assert 'font-size: 13px' in (
        (STUDIO_DIR / "homepage-v2" / "css" / "import-wizard.css").read_text(encoding="utf-8")
    )
    assert 'aria-label="换文件夹，返回选择步骤"' in html
    assert "换文件夹" in html
    assert "v2-wizard__change-folder" in html
    assert "换文件夹可再做一篇" in html
    assert "请为您的影像画册起一个优雅的名称" in html
    assert "请描述您这本画册的主题风格" in html
    assert "照片怎么组织？" in html
    assert "设置画册智能排版策略" in html
    assert "画册的主要活动地点或标志性地名（可选）" in html
    assert "照片活动中的趣事和感悟（可选），想要分享的情绪和观点" in html
    assert "根据天数、地点自动匹配模板" in html
    assert "这趟旅行叫什么？" not in html
    assert "想强调什么感觉？" not in html
    assert "版面气质怎样？" not in html
    assert "主要地点（可选）" not in html
    assert "旅途见闻与感悟（可选）" not in html
    assert "视频占比" not in html
    assert 'id="v2-wizard-first-tip"' in html
    assert 'id="v2-wizard-dup-note"' in html
    assert "风光为主，少写攻略" in html
    assert "人物与故事感优先" in html
    # 精细字段仍在 DOM（进阶内）
    assert 'id="v2-wizard-date-start"' in html
    assert 'id="v2-wizard-travel-notes"' in html
    assert 'name="v2-wizard-layout-density"' in html
    assert 'id="v2-wizard-template-mode"' in html

    wizard = (STUDIO_DIR / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    wizard_logic = (STUDIO_DIR / "homepage-v2" / "import-wizard-logic.js").read_text(
        encoding="utf-8"
    )
    assert "定制画册细节 →" in wizard_logic
    assert "定制作品集细节 →" in wizard_logic
    assert "FIRST_TIP_KEY" in wizard
    assert "updateDuplicateTitleNote" in wizard
    assert "syncChipPressedState" in wizard

    from travelogue.web.studio_homepage_telemetry import ALLOWED_STUDIO_HOMEPAGE_EVENTS

    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    for event in (
        "photo_count_hint_show",
        "advanced_fields_toggle",
        "close_confirm",
    ):
        assert event in ALLOWED_STUDIO_HOMEPAGE_EVENTS
        assert f'"{event}"' in analytics


def test_m21_0_browser_upload_contract() -> None:
    """M21-0 · AC-M21-0 静态契约：upload 接线 + 软上限 + sessionStorage 续跑。"""
    wizard = (STUDIO_DIR / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    run = (STUDIO_DIR / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")

    assert 'id="v2-wizard-album-upload"' in html
    assert "webkitdirectory" in html
    assert "handleUploadInput" in wizard
    assert "_uploadInFlight" in wizard
    assert "startV2UploadImport" in run
    assert "postMultipartImportV2" in run
    assert "SS.activeJobId" in run and "resumeV2ImportIfAny" in run
    assert "200" in wizard or "UPLOAD_BYTES_SOFT_LIMIT" in wizard


def test_studio_home_v2_phase14_dual_mode_smoke() -> None:
    """Phase 14 最小前端冒烟：双模式 DOM + 行为挂钩均已接线（Wizard）。"""
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    wizard = (STUDIO_DIR / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    run = (STUDIO_DIR / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    first_success = (STUDIO_DIR / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")

    for marker in (
        "v2-wizard-mode-quick",
        "v2-wizard-mode-fine",
        "快速分享",
        "个性化定制画册",
        'id="v2-wizard-step-fine"',
        "v2-wizard-travel-notes",
        "v2-wizard-date-start",
        "v2-wizard-date-end",
        "v2-wizard-featured-dir",
        "v2-wizard-material-dir",
        "按这些偏好开始 →",
        "v2-success-secondary",
        "v2-wizard-layout-density",
        "设置画册智能排版策略",
        'name="v2-wizard-layout-density"',
        "拼图为主",
        "v2-wizard-photo-mode-recommended",
        "推荐精简（默认）",
        "v2-wizard-photo-mode-keep-bursts",
        "v2-wizard-photo-mode-keep-all",
        "全部保留",
        "v2-wizard-photo-keep-all-risk",
    ):
        assert marker in html, marker
    assert "layoutDensity" in wizard
    assert "readLayoutDensity" in wizard
    assert "readPhotoKeepMode" in wizard
    assert "photoKeepMode" in wizard
    assert "trackImportPhotoKeepMode" in wizard
    assert "layoutDensity" in first_success or "大图为主" in first_success
    assert "已尽量保留全部可用照片" in first_success
    assert "photoKeepMode" in first_success
    assert "trackImportPhotoKeepMode" in run or "photoKeepMode" in run

    for marker in (
        "setActiveMode(",
        "saveDraft(",
        "body.travelNotes",
        "body.dateRange",
        "body.featuredDir",
        "body.materialDir",
    ):
        assert marker in wizard, marker

    css = V2_CSS_BUNDLE
    assert ".v2-wizard" in css
    assert "display: none !important;" in css

    for marker in (
        "autoExport",
        "writeFtueAutoExport",
        "v2-success-secondary",
        "success_preview_unavailable_fallback_longshot",
    ):
        assert marker in first_success, marker


def test_studio_home_v2_first_success_module() -> None:
    """FirstSuccess 专屏 + harness studioState / studioJob。"""
    fs = (STUDIO_DIR / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
    harness = (STUDIO_DIR / "homepage-v2" / "harness.js").read_text(encoding="utf-8")
    assert "showFirstSuccess" in fs and "captureImportShell" in fs
    assert "success_primary_click" in fs
    assert "trapFocus" in fs
    assert "Escape" in fs
    assert "harnessApplyStartup" in harness and "studioState" in harness
    assert "studioJob" in harness and "harnessInstallFetchMocks" in harness


def test_studio_home_v2_variant_guard_and_dev_panel() -> None:
    """AC-HP2-23 variant guard + DEV-HARNESS dev panel。"""
    guard = (STUDIO_DIR / "homepage-v2" / "variant-guard.js").read_text(encoding="utf-8")
    panel = (STUDIO_DIR / "homepage-v2" / "dev-panel.js").read_text(encoding="utf-8")
    css = V2_CSS_BUNDLE
    assert "isVariantSwitchLocked" in guard and "syncVariantGuard" in guard
    assert "initDevPanel" in panel and "Copy repro URL" in panel
    assert ".v2-dev-panel" in css


def test_studio_home_v2_layout_tier_and_failed_modules() -> None:
    """L2 懒加载层级 + Import Failed 专屏 + bucket_id。"""
    tier = (STUDIO_DIR / "homepage-v2" / "layout-tier.js").read_text(encoding="utf-8")
    failed = (STUDIO_DIR / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
    bucket = (STUDIO_DIR / "js" / "bucket.js").read_text(encoding="utf-8")
    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    carousel = (STUDIO_DIR / "homepage-v2" / "carousel.js").read_text(encoding="utf-8")

    assert "resolveLayoutTier" in tier and "shouldEagerCarouselPage" in tier
    assert "showImportFailed" in failed and "failureNextHint" in failed
    assert "trapFocus" in failed
    assert "Escape" in failed
    css = V2_CSS_BUNDLE
    assert ".v2-first-success {" in css
    first_success_block = css.split(".v2-first-success {", 1)[1].split("}", 1)[0]
    first_success_panel = css.split(".v2-first-success__panel {", 1)[1].split("}", 1)[0]
    failure_block = css.split(".v2-failure {", 1)[1].split("}", 1)[0]
    assert "position: fixed" in first_success_block
    assert "position: fixed" in failure_block
    assert "isolation: isolate" in first_success_panel
    assert "--v2-fs-ink" in first_success_panel
    assert "z-index: 2500" in failure_block
    assert "readServerBucketId" in bucket
    assert "resolveBucketId" in bucket
    assert "travelogue.studio.eventRing" in analytics
    assert "bucket_id" in (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "lazySrc" in carousel or "lazy" in carousel
    # 邻页预载不可对未入 DOM 的 img 使用 loading=lazy（否则请求被跳过、placeholder 永驻）
    assert "img.loading" not in carousel
    phone = (STUDIO_DIR / "homepage-v2" / "phone-strip.js").read_text(encoding="utf-8")
    assert "img.loading" not in phone
    assert "dataset.lazySrc" in phone


def test_studio_home_v2_carousel_modules() -> None:
    """M20-b · Carousel clamp/spread 控制器与纯逻辑。"""
    logic = (STUDIO_DIR / "homepage-v2" / "carousel-logic.js").read_text(encoding="utf-8")
    carousel = (STUDIO_DIR / "homepage-v2" / "carousel.js").read_text(encoding="utf-8")

    for js in (logic, carousel):
        assert "\ufffd" not in js

    for fn in ("clampIndex", "spreadFor", "scrollLeftFor", "indexFromScrollLeft",
               "canPrev", "canNext", "isOddTail"):
        assert fn in logic, fn

    assert "initCarousel" in carousel
    assert "carousel-logic.js" in carousel  # 控制器复用纯逻辑
    assert "aria-current" in carousel       # dots 无障碍
    assert "ArrowLeft" in carousel and "ArrowRight" in carousel  # 键盘 ←/→
    # bento 委托 carousel，不再自带 renderCarousel（去重）
    bento = (STUDIO_DIR / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    assert "initCarousel" in bento
    assert "renderCarousel" not in bento


def test_v2_js_logic_node_units() -> None:
    """运行 tests/js 全量 Node 单测（SFH W0a · 目录扫描）。

    本地无 node 可 skip。CI 合同见 ci.yml test-pr（须装 Node 并跑 npm run test:js）；
    Actions 额度用尽期间以本机 npm run test:js 为 Go 证据（PRD R-SFH-01）。
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("node 不可用，跳过 JS 单测（开发 FE 决策时请自备 node）")
    runner = REPO_ROOT / "scripts" / "run-js-tests.mjs"
    assert runner.is_file(), f"缺少 JS 单测入口：{runner}"
    js_dir = REPO_ROOT / "tests" / "js"
    test_files = sorted(js_dir.glob("*.test.mjs"))
    assert test_files, f"{js_dir} 下应有 *.test.mjs"
    try:
        result = subprocess.run(
            [node, str(runner)],
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except OSError as exc:  # 某些受限终端无法创建子进程管道
        pytest.skip(f"无法启动 node 子进程：{exc}")
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "# fail 0" in result.stdout


def test_studio_home_v2_lightbox_modules() -> None:
    """M20-c · Lightbox 控制器 + 阈值纯逻辑。"""
    logic = (STUDIO_DIR / "homepage-v2" / "lightbox-logic.js").read_text(encoding="utf-8")
    lightbox = (STUDIO_DIR / "homepage-v2" / "lightbox.js").read_text(encoding="utf-8")

    for js in (logic, lightbox):
        assert "\ufffd" not in js

    assert "LIGHTBOX_DRAG_THRESHOLD_PX" in logic
    assert "classifyGesture" in logic and "isTap" in logic

    assert "openLightbox" in lightbox and "closeLightbox" in lightbox
    assert "initLightbox" in lightbox
    assert "trapFocus" in lightbox          # focus trap
    assert "Escape" in lightbox             # Esc 关闭
    # 不进 editor preview（只读验货）：不嵌 iframe
    assert "iframe" not in lightbox.lower()

    # bootstrap 接入真 Lightbox（覆盖占位）
    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "initLightbox" in bootstrap
    assert "M20-c" not in bootstrap  # 占位 toast 已移除


def test_studio_home_v2_stale_recurate_modules() -> None:
    """算法过期 · Bento 提示条 + curate 客户端 + 纯逻辑。"""
    stale = (STUDIO_DIR / "homepage-v2" / "bento-stale.js").read_text(encoding="utf-8")
    curate = (STUDIO_DIR / "homepage-v2" / "curate-client.js").read_text(encoding="utf-8")
    logic = (STUDIO_DIR / "homepage-v2" / "shelf-actions-logic.js").read_text(encoding="utf-8")
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    css = V2_CSS_BUNDLE
    bento = (STUDIO_DIR / "homepage-v2" / "bento.js").read_text(encoding="utf-8")

    assert "syncBentoStaleBar" in stale and "triggerHomepageRecurate" in stale
    assert "runTripCurateJob" in curate and "withJobBusyRetry" in curate
    assert "shelfResumeActions" in logic and "shouldShowBentoStaleBar" in logic
    assert "v2-bento-stale" in html and 'aria-live="polite"' in html
    assert ".v2-bento__stale" in css
    assert "syncBentoStaleBar" in bento
    assert "clearBentoPreviewCache" in (
        STUDIO_DIR / "homepage-v2" / "trip-preview.js"
    ).read_text(encoding="utf-8")


def test_studio_home_v2_shelf_module() -> None:
    """M20-e · Web 书架（§8）。"""
    shelf = (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "\ufffd" not in shelf
    assert "renderShelf" in shelf
    assert "你的影像画册" in shelf
    logic = (STUDIO_DIR / "homepage-v2" / "shelf-actions-logic.js").read_text(encoding="utf-8")
    assert "更新长图" in logic            # stale → 更新长图
    assert "可重排" in shelf
    assert "重新排版" in logic
    assert "longshotStale" in shelf
    assert "algorithmStale" in shelf
    assert "shelf-actions-logic.js" in shelf
    assert "triggerHomepageRecurate" in shelf
    assert "isDemoTrip" in shelf          # demo → 示例徽章
    assert "openImportSheet" in shelf     # 新建 → Sheet
    assert 'forceStep: "pick"' in shelf   # 新建默认回选夹，避免停在旧文件夹确认页
    assert "v2-wizard__change-folder" in V2_CSS_BUNDLE
    assert "shelfCoverRelPath" in shelf   # 书架竖版封面（mobile cover）
    assert "loadMoreShelf" in shelf
    assert "fetchTripsPage" in shelf
    assert "加载更多" in shelf
    assert "即将上线" not in shelf
    assert "shelf-menu.js" in shelf
    assert "v2-shelf__card" in shelf
    assert "v2-shelf__ticket" in shelf
    assert "v2-shelf__stub" in shelf
    assert "v2-shelf__barcode" in shelf
    assert "stubMetaLine" in shelf
    assert "v2-shelf__menu-btn" in V2_CSS_BUNDLE
    assert ".v2-shelf__ticket" in V2_CSS_BUNDLE
    assert ".v2-shelf__perf" in V2_CSS_BUNDLE
    assert ".v2-shelf__barcode" in V2_CSS_BUNDLE
    assert "shelf-outputs.js" in shelf
    assert "buildOutputStubs" in shelf
    assert "allowReadyBadge" in shelf
    outputs_js = (STUDIO_DIR / "homepage-v2" / "shelf-outputs.js").read_text(encoding="utf-8")
    assert "v2-shelf__stubs" in outputs_js
    assert ".v2-shelf__stub-chip" in V2_CSS_BUNDLE
    assert "管理成品" in (STUDIO_DIR / "homepage-v2" / "shelf-menu.js").read_text(
        encoding="utf-8"
    )

    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    assert "studio-modal.css" in html
    modal_css = (STUDIO_DIR / "studio-modal.css").read_text(encoding="utf-8")
    assert ".studio__modal-backdrop" in modal_css
    assert "position: fixed" in modal_css
    # 须高于 LLM 设置层(12000)，否则覆盖确认被挡住
    assert "z-index: 13000" in modal_css

    modal_js = (STUDIO_DIR / "studio-modal.js").read_text(encoding="utf-8")
    assert "studio-modal-open" in modal_js
    assert "preventScroll" in modal_js
    assert "GHOST_CLICK_MS" in modal_js
    assert "Date.now() - openedAt < GHOST_CLICK_MS" in modal_js

    menu = (STUDIO_DIR / "homepage-v2" / "shelf-menu.js").read_text(encoding="utf-8")
    assert "改为游记重排" in menu
    assert "shelfExportMenuCopy" in menu
    assert "管理成品" in menu
    export_copy = (STUDIO_DIR / "js" / "portfolio-export-logic.js").read_text(encoding="utf-8")
    assert "保存长图" in export_copy
    assert "打开长图文件夹" in export_copy
    assert "openShelfLongshotFolder" in menu
    assert "canOpenShelfLongshotFolder" in menu
    assert "删除画册" in menu
    assert "shelf_menu_open" in menu
    assert "deleteTrip" in menu
    assert "runShelfLongshot" in menu
    assert "shelf-longshot.js" in menu

    longshot_client = (STUDIO_DIR / "js" / "longshot-client.js").read_text(encoding="utf-8")
    assert "LONGSHOT_PRESETS" in longshot_client
    assert "copyDisplay" in longshot_client
    assert '"photos"' in longshot_client
    assert "scale: 3" in longshot_client

    shelf_longshot = (STUDIO_DIR / "homepage-v2" / "shelf-longshot.js").read_text(encoding="utf-8")
    assert "shelf_longshot_start" in shelf_longshot
    assert "shelf_open_longshot_folder" in shelf_longshot
    assert "openShelfLongshotFolder" in shelf_longshot
    assert "longshot-current.json" in shelf_longshot
    assert "V2.reroute" in shelf_longshot

    events = (REPO_ROOT / "travelogue" / "domain" / "studio_events.py").read_text(
        encoding="utf-8"
    )
    assert "shelf_open_longshot_folder" in events

    trips_client = (STUDIO_DIR / "homepage-v2" / "trips-client.js").read_text(encoding="utf-8")
    assert "deleteTrip" in trips_client
    assert "studioAuthHeaders" in trips_client
    assert 'method: "DELETE"' in trips_client

    css = V2_CSS_BUNDLE
    assert ".v2-shelf" in css
    assert "line-clamp" in css            # 长标题 2 行 clamp

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "renderShelf" in bootstrap
    assert "renderShelfPlaceholder" not in bootstrap  # 占位已移除


def test_studio_home_v2_viewport_modules() -> None:
    """M20-f · iPad 横屏 + UnsupportedViewport（§10）。"""
    logic = (STUDIO_DIR / "homepage-v2" / "viewport-logic.js").read_text(encoding="utf-8")
    unsupported = (STUDIO_DIR / "homepage-v2" / "unsupported.js").read_text(encoding="utf-8")

    for js in (logic, unsupported):
        assert "\ufffd" not in js

    assert "classifyViewport" in logic
    assert "isSupported" in logic
    assert "unsupportedCopy" in logic
    assert "tablet_landscape" in logic

    assert "applyViewport" in unsupported
    assert "initViewportWatch" in unsupported
    assert "orientationchange" in unsupported  # 动态重判
    assert "resize" in unsupported

    css = V2_CSS_BUNDLE
    # iPad 横屏断点保持双列（不堆叠）
    assert "min-width: 768px) and (max-width: 1023px" in css

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "initViewportWatch" in bootstrap
    assert "detectLayout" not in bootstrap  # 已抽到 viewport-logic


def test_studio_home_v2_coldstart_background() -> None:
    """M20-g · 冷启动 Importing 静帧背景（§9.2 / AC-HP2-17）。"""
    bento = (STUDIO_DIR / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    import_run = (STUDIO_DIR / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")

    assert "renderColdStartBackground" in bento
    # 静帧：明确移除 Ken Burns 动效
    assert "classList.remove(\"is-kenburns\")" in bento
    # 幂等：已有壳层背景不覆盖（暖启动）
    assert "if (bg.style.backgroundImage) return" in bento

    assert "renderColdStartBackground" in import_run


def test_studio_home_v2_telemetry_wired() -> None:
    """M20-h · 漏斗埋点接线（TELEMETRY §2 / PRD §13.2）。"""
    # 服务端 ALLOWED 已纳入 v2 事件
    from travelogue.web.studio_homepage_telemetry import (
        ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    )
    for ev in (
        "experiment_exposure", "homepage_view", "cta_click",
        "sheet_close", "sheet_abandon", "lightbox_open",
        "spread_page_view", "shelf_resume_click",
        "shelf_menu_open", "shelf_delete_confirm", "shelf_delete_success",
        "shelf_delete_fail",
        "shelf_longshot_start", "shelf_longshot_success",
        "longshot_export_start", "longshot_export_success",
        "longshot_export_fail", "longshot_platform_change",
    ):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS

    # 客户端 analytics.js ALLOWED 同步
    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in (
        "homepage_view",
        "cta_click",
        "spread_page_view",
        "shelf_resume_click",
        "longshot_export_start",
        "longshot_platform_change",
    ):
        assert ev in analytics

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "experiment_exposure" in bootstrap
    assert "homepage_view" in bootstrap
    assert "_viewTracked" in bootstrap  # 仅最终态首帧一次

    entry = (STUDIO_DIR / "homepage-v2" / "import-entry.js").read_text(encoding="utf-8")
    assert "cta_click" in entry
    homepage_cta = (STUDIO_DIR / "homepage-v2" / "homepage-cta.js").read_text(encoding="utf-8")
    assert "cta_click" in homepage_cta

    wizard = (STUDIO_DIR / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    assert "sheet_close" in wizard
    assert "sheet_abandon" in wizard

    carousel = (STUDIO_DIR / "homepage-v2" / "carousel.js").read_text(encoding="utf-8")
    assert "spread_page_view" in carousel

    shelf = (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "shelf_resume_click" in shelf

    lightbox = (STUDIO_DIR / "homepage-v2" / "lightbox.js").read_text(encoding="utf-8")
    assert "lightbox_open" in lightbox


@pytest.mark.e2e
def test_studio_home_v2_event_endpoint(tmp_path: Path) -> None:
    """Studio telemetry POST /__travelogue/studio-event accepts allowlisted events."""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        status, body = _post_json(
            f"{base}{STUDIO_EVENT_PATH}",
            {"event": "open_sheet", "meta": {"state": "IdleEmpty", "qa": True}},
        )
        assert status == 200
        assert body == {"ok": True}
        bad_status, bad_body = _post_json(
            f"{base}{STUDIO_EVENT_PATH}",
            {"event": "not_allowed"},
        )
        assert bad_status == 400
        assert "allowed" in bad_body
    finally:
        server.shutdown()
        server.server_close()


def test_studio_home_v2_error_pipeline() -> None:
    """M20-i · JS error 管道（TELEMETRY §3 / §17.2）。"""
    from travelogue.web.studio_homepage_telemetry import (
        ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    )
    assert "js_error" in ALLOWED_STUDIO_HOMEPAGE_EVENTS

    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    assert "js_error" in analytics

    pipe = (STUDIO_DIR / "homepage-v2" / "error-pipeline.js").read_text(encoding="utf-8")
    assert "\ufffd" not in pipe
    assert "initErrorPipeline" in pipe
    assert "unhandledrejection" in pipe
    assert "addEventListener(\"error\"" in pipe
    assert "MAX_ERRORS_PER_SESSION" in pipe  # 节流防风暴

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "initErrorPipeline" in bootstrap


def test_studio_home_v2_harness_and_ac_hooks() -> None:
    """M20-h/AC · dev harness + AC e2e 依赖的 DOM/CSS 钩子。"""
    harness = (STUDIO_DIR / "homepage-v2" / "harness.js").read_text(encoding="utf-8")
    assert "\ufffd" not in harness
    assert "harnessTripsOverride" in harness
    assert "harnessAssetsFail" in harness
    assert "studioFixture" in harness
    assert "studioAssetsFail" in harness

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "harnessTripsOverride" in bootstrap
    assert "harnessAssetsFail" in bootstrap

    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-carousel-hint"' in html
    assert 'data-demo-flag' in html
    assert html.count('data-demo-flag') >= 2
    assert 'id="v2-bento-preview-select"' in html
    assert 'id="v2-bento-preview-trigger"' in html
    assert 'id="v2-bento-preview-listbox"' in html
    assert "预览画册" in html
    assert 'id="v2-success-set-preview"' in html

    picker = (STUDIO_DIR / "homepage-v2" / "bento-preview-picker.js").read_text(encoding="utf-8")
    assert "setBentoPreviewTripId" in picker
    assert "v2-preview-combobox__option" in picker
    shelf_menu = (STUDIO_DIR / "homepage-v2" / "shelf-menu.js").read_text(encoding="utf-8")
    assert "在上方预览" in shelf_menu
    assert "is-previewing" in (STUDIO_DIR / "homepage-v2" / "css" / "bench.css").read_text(
        encoding="utf-8"
    )
    assert "bentoPreviewTrip" in (
        STUDIO_DIR / "homepage-v2" / "harness.js"
    ).read_text(encoding="utf-8")
    assert "bentoPreview404" in harness
    assert "studioCurate" in harness
    assert "harnessInstallCurateMock" in harness
    deeplink = (STUDIO_DIR / "homepage-v2" / "bento-preview-deeplink.js").read_text(encoding="utf-8")
    assert "applyPreviewDeepLink" in deeplink
    migrate = (STUDIO_DIR / "homepage-v2" / "bento-preview-migrate.js").read_text(encoding="utf-8")
    assert "migrateD13BentoPreference" in migrate
    assert "ensureTripInCatalog" in (STUDIO_DIR / "homepage-v2" / "trip-preview.js").read_text(encoding="utf-8")
    assert "v2-bento-preview-search" in picker
    assert "#v2-web-cell" in html or 'id="v2-web-cell"' in html

    css = V2_CSS_BUNDLE
    assert ".v2-preview-combobox__trigger" in css
    assert ".v2-preview-combobox__option-stale" in css
    # 隐藏的 fixed 覆盖层不得拦截点击
    assert "#v2-unsupported[hidden]" in css
    assert "display: none !important" in css
    # FOUC guard：JS 写入 data-v2-layout 前窄屏先亮 Unsupported
    assert "html:not([data-v2-layout]) #v2-unsupported[hidden]" in css
    assert 'setAttribute("data-v2-layout"' in (
        STUDIO_DIR / "homepage-v2" / "unsupported.js"
    ).read_text(encoding="utf-8")
    # Unsupported 态隐藏首页帮助 FAB
    help_css = (STUDIO_DIR / "help-drawer.css").read_text(encoding="utf-8")
    assert 'html[data-v2-layout^="unsupported"] .studio-help-open--home' in help_css
    # 卷轴页点扩大命中区
    assert ".v2-carousel__dots button::after" in css
    # CTA 触控目标 ≥44px（AC-HP2-21）
    assert "min-height: 44px" in css

    dev_panel = (STUDIO_DIR / "homepage-v2" / "dev-panel.js").read_text(encoding="utf-8")
    assert 'href="/classic"' in dev_panel


def test_is_demo_trip_distinguishes_user_slug_hash() -> None:
    """CJK 文件夹导入的 demo-{hash} slug 是用户画册，不是 bundled demo。"""
    js = (STUDIO_DIR / "js" / "constants.js").read_text(encoding="utf-8")
    assert "/^demo-[a-f0-9]{10}$/" not in js
    assert 'id === "demo-album"' in js


def test_studio_home_v2_review_followups() -> None:
    """代码审查 P1/P2 后续修复断言。"""
    manifest_js = (STUDIO_DIR / "homepage-v2" / "manifest.js").read_text(encoding="utf-8")
    assert 'cache: "no-cache"' not in manifest_js

    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'rel="modulepreload"' in html

    carousel = (STUDIO_DIR / "homepage-v2" / "carousel.js").read_text(encoding="utf-8")
    assert 'fetchpriority' in carousel

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "_reroutePromise" in bootstrap
    assert 'import("./shelf.js")' in bootstrap
    assert 'from "./shelf.js"' not in bootstrap

    shelf = (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "cssBackgroundImage" in shelf

    static = (
        REPO_ROOT / "travelogue" / "web" / "studio_handlers" / "static_handlers.py"
    ).read_text(encoding="utf-8")
    assert "Cache-Control" in static
    assert "ETag" in static


def test_demo_showcase_manifest_valid() -> None:
    manifest_path = (
        STUDIO_DIR / "assets" / "demo-showcase" / "manifest.json"
    )
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["version"]
    assert data["title"]
    assert data["assets"]["background"]
    assert data["assets"]["longshot"]
    pages = data["pages"]
    assert isinstance(pages, list) and len(pages) >= 3
    # 顺序约束：首 cover、尾 epilogue（DATA-CONTRACT §1.2）
    assert pages[0]["role"] == "cover"
    assert pages[-1]["role"] == "epilogue"
    for page in pages:
        for field in ("id", "role", "label", "webp"):
            assert page.get(field), field
        if page["role"] == "chapter":
            assert page.get("chapterIndex"), page["id"]

    asset_root = manifest_path.parent
    rel_paths = {data["assets"]["background"], data["assets"]["longshot"]}
    rel_paths.update(p["webp"] for p in pages)
    for rel in rel_paths:
        path = asset_root / rel
        assert path.is_file(), f"缺失 dev 占位 WebP: {rel}（运行 scripts/generate_demo_placeholders.py）"
        assert path.read_bytes()[:4] == b"RIFF", rel


@pytest.mark.e2e
def test_studio_home_gate_off_serves_classic_at_root(tmp_path: Path, monkeypatch) -> None:
    """AC-HP2-23 回滚 · TRAVELOGUE_STUDIO_HOMEPAGE_V2=off → GET / 为 classic 冻结页。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        for marker in CLASSIC_FREEZE_MARKERS:
            assert marker in html, marker
        assert "studio-home-v2.css" not in html
        assert "/__studio/legacy-freeze/studio.classic.js" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_auto_zero_percent_no_redirect(tmp_path: Path, monkeypatch) -> None:
    """holdback 0% · auto 模式不 redirect 到 /v2。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "0")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert 'data-studio-v="4"' in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_classic_contract_smoke_config_capabilities(tmp_path: Path, monkeypatch) -> None:
    """M21 · classic 合同 smoke：页面与导入能力配置可达。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/classic", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert "classic-pick" in html

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/__travelogue/config", timeout=10) as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
        caps = body.get("capabilities") or {}
        assert "pickFolder" in caps
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_on_serves_v2_at_root(tmp_path: Path, monkeypatch) -> None:
    """M20-j · TRAVELOGUE_STUDIO_HOMEPAGE_V2=on → GET / 直接 v2。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "on")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="v2"' in html
        assert "studio-home-v2.css" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_classic_serves_frozen_page(tmp_path: Path, monkeypatch) -> None:
    """M21-e2 · GET /classic 始终返回 legacy-freeze classic 页（与 gate 模式无关）。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "on")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/classic", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        for marker in CLASSIC_FREEZE_MARKERS:
            assert marker in html, marker
        assert "/__studio/legacy-freeze/studio.classic.js" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_auto_redirects_to_v2(tmp_path: Path, monkeypatch) -> None:
    """M21-c · auto + 100% 直接在根路径返回 v2（无 /v2 重定向）。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "100")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            cookie = resp.headers.get("Set-Cookie") or ""
        assert 'data-homepage-variant="v2"' in html
        assert "studio-home-v2.css" in html
        assert "travelogue.studio.hp_bucket=" in cookie
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_auto_treatment_redirects(tmp_path: Path, monkeypatch) -> None:
    """M21-c · auto 10% 进组 UA 在根路径直接返回 v2。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    ua = "M20jTest/5"  # bucket=3 < 10
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/",
            method="GET",
            headers={"User-Agent": ua},
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="v2"' in html
        assert "studio-home-v2.css" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_auto_control_stays_classic(tmp_path: Path, monkeypatch) -> None:
    """M20-j · auto 10% · 对照组 UA → 200 classic（data-homepage-variant=classic）。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    ua = "M20jTest/1"  # bucket=70 >= 10
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/",
            method="GET",
            headers={"User-Agent": ua},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="classic"' in html
        assert 'data-studio-v="4"' in html
        assert "studio-home-v2.css" not in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_auto_yaml_percent_redirects(tmp_path: Path, monkeypatch) -> None:
    """M21-c · auto 无 env percent 时读 yaml；进组 UA 在根路径返回 v2。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", raising=False)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"studio": {"homepage": {"v2_bento": {"percent": 10}}}}),
        encoding="utf-8",
    )
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port, config_path=config_path)
    ua = "M20jTest/5"  # bucket=3 < 10
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/",
            method="GET",
            headers={"User-Agent": ua},
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="v2"' in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_query_override_v2(tmp_path: Path, monkeypatch) -> None:
    """dev · ?homepageVariant=v2 在 off 模式下仍 serve v2。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/?homepageVariant=v2",
            timeout=10,
        ) as resp:
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="v2"' in html
    finally:
        server.shutdown()
        server.server_close()


def test_studio_homepage_gate_wired() -> None:
    """门控模块已接入 studio_dispatch 路由表 + static_handlers（M-C1 后）。"""
    dispatch = (REPO_ROOT / "travelogue" / "web" / "studio_dispatch.py").read_text(encoding="utf-8")
    static = (
        REPO_ROOT / "travelogue" / "web" / "studio_handlers" / "static_handlers.py"
    ).read_text(encoding="utf-8")
    assert "static_handlers.handle_home_root" in dispatch
    assert "handle_home_root" in static
    assert "HOME_CLASSIC_PATH" in dispatch
    gate = (REPO_ROOT / "travelogue" / "web" / "studio_homepage_gate.py").read_text(encoding="utf-8")
    assert "TRAVELOGUE_STUDIO_HOMEPAGE_V2" in gate
    assert "decide_root_variant" in gate


HOMEPAGE_V21_FORBIDDEN_COPY = (
    "算法待更新",
    "长图待更新",
    "到头停止",
    "← 横滑",
)


def test_homepage_v21_no_internal_terminology_in_studio_templates() -> None:
    """AC-HP21-06 · G-HP21-05 · 首页用户可见文案禁止内部术语。"""
    for path in STUDIO_DIR.rglob("*"):
        if path.suffix not in {".html", ".js", ".css"}:
            continue
        if "legacy-freeze" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for term in HOMEPAGE_V21_FORBIDDEN_COPY:
            assert term not in text, f"禁止术语 {term!r} 出现在 {path.relative_to(REPO_ROOT)}"


def test_homepage_v21_telemetry_events_registered() -> None:
    """M22-e · v2.1 新增事件已登记于客户端与服务端 allowlist。"""
    from travelogue.web.studio_homepage_telemetry import ALLOWED_STUDIO_HOMEPAGE_EVENTS

    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    for event in ("settings_open", "bench_resume_click", "shelf_scroll_into_view"):
        assert f'"{event}"' in analytics
        assert event in ALLOWED_STUDIO_HOMEPAGE_EVENTS


def test_homepage_v21_markers_present() -> None:
    """v2.1 壳层 marker：设置入口、信任行、data-homepage-v21。"""
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    for marker in (
        'data-homepage-v21="1"',
        'id="v2-headline-trust"',
        'id="v2-settings-toggle"',
        'id="v2-bench-layout-lab"',
        "版式",
        'href="/templates-admin"',
        "无需上传照片 · 个人隐私无忧 · 智能拼图排版 · 一键多种输出",
    ):
        assert marker in html
