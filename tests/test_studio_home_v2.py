"""Studio 首页 v2（GET /v2）路由 + 冒烟测试（Phase 0 / M20-a）。

覆盖：
- GET /v2 返回 200 且含 v2 Bento 标记
- GET / 仍 200 且 v3 DOM 不变（回归护栏）
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

from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_server import _free_port, _start_studio_server

REPO_ROOT = Path(__file__).resolve().parents[1]
STUDIO_DIR = REPO_ROOT / "templates" / "studio"


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
    "开始制作我的游记",
    "示例作品",
    "自动分章成文",
    "v2-unsupported",
    # M20-d · Import Sheet
    "v2-import-sheet",
    'role="dialog"',
    'aria-modal="true"',
    "选择本次旅行的照片文件夹",
    "步骤 1 / 2",
    "v2-album-path",
    "v2-album-upload",
    "小文件夹试用（建议 ≤200MB）",
    "v2-sheet-close",
    # M20-c · Lightbox
    "v2-lightbox",
    "v2-lightbox-scroll",
    "v2-lightbox-close",
    # FirstSuccess overlay（§9.3）
    "v2-first-success",
    "v2-success-open",
    "v2-success-stay",
    "打开卷轴预览",
    # M20 · 高级分析选项（工作台 Popover）
    "v2-advanced-toggle",
    "v2-advanced-popover",
    'id="studio-cfg-clustering"',
    'id="studio-cfg-vision"',
    "高级 · 分析选项",
    "智能排版",
    # Import Failed overlay
    "v2-failure",
    "v2-failure-retry",
    "v2-failure-stay",
)

V3_HOME_MARKERS = (
    'data-studio-v="4"',
    "studio-hero",
    "studio-hero-empty",
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
def test_studio_home_v3_unchanged(tmp_path: Path, monkeypatch) -> None:
    """v2 引入后，v3 `/` 路径零回归。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        for marker in V3_HOME_MARKERS:
            assert marker in html, marker
        # v3 不应引用 v2 资源（Bundle 隔离 · LCP 护栏）
        assert "studio-home-v2.css" not in html
        assert "homepage-v2/bootstrap.js" not in html
    finally:
        server.shutdown()
        server.server_close()


def test_studio_home_v2_css_present() -> None:
    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
    for sel in (
        ".v2-bento",
        ".v2-carousel",
        ".v2-phone",
        ".v2-bench",
        ".v2-demo-flag",
        ".v2-auto-tag",
        ".v2-shared__bg",
        ".v2-unsupported",
    ):
        assert sel in css, sel


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
    advanced = (STUDIO_DIR / "homepage-v2" / "advanced-options.js").read_text(encoding="utf-8")
    assert "bindAdvancedConfigControls" in advanced
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
    """M20-d · Import Sheet + 导入编排，复用 v3 共享原语（非复制视图）。"""
    sheet = (STUDIO_DIR / "homepage-v2" / "import-sheet.js").read_text(encoding="utf-8")
    run = (STUDIO_DIR / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    assert "refreshTripsForImportSuccess" in run

    for js in (sheet, run):
        assert "\ufffd" not in js

    # Sheet a11y（§7.1）：focus trap + Esc + 焦点归还 CTA
    assert "openImportSheet" in sheet and "closeImportSheet" in sheet
    assert "trapFocus" in sheet
    assert "Escape" in sheet
    assert "SHEET_FOCUSABLE" in sheet
    # pick-folder + 路径仅在 Sheet 内
    assert "/__travelogue/pick-folder" in sheet
    assert "submitWithPath" in sheet
    assert "v2-album-upload" in sheet
    assert "confirmLargeUpload" in sheet
    assert "UPLOAD_BYTES_SOFT_LIMIT" in sheet
    assert "仍要上传" in sheet
    assert "建议总量≤200MB" in sheet
    assert "startV2UploadImport" in sheet

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
    assert "AI 自动生成" not in sheet and "AI 自动生成" not in run


def test_studio_home_v2_phase14_dual_mode_smoke() -> None:
    """Phase 14 最小前端冒烟：双模式 DOM + 行为挂钩均已接线。"""
    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    sheet = (STUDIO_DIR / "homepage-v2" / "import-sheet.js").read_text(encoding="utf-8")
    first_success = (STUDIO_DIR / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")

    for marker in (
        "v2-sheet-mode-quick",
        "v2-sheet-mode-fine",
        "快速分享",
        "精细制作",
        'id="v2-sheet-panel-fine" data-mode="fine_craft" hidden',
        "v2-travel-notes",
        "v2-date-start",
        "v2-date-end",
        "v2-featured-dir",
        "v2-material-dir",
        "开始制作（专业）",
        "v2-success-secondary",
        "v2-layout-density-field",
        "版面密度（可选）",
        'name="v2-layout-density"',
        "拼图为主",
    ):
        assert marker in html, marker
    assert "layoutDensity" in sheet
    assert "readLayoutDensity" in sheet
    assert "layoutDensity" in first_success or "大图为主" in first_success

    for marker in (
        "switchMode(",
        "saveSheetDraft(",
        "restoreModeAndDraft(",
        "validateFineFields(",
        "body.travelNotes",
        "body.dateRange",
        "body.featuredDir",
        "body.materialDir",
    ):
        assert marker in sheet, marker

    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
    assert ".v2-sheet__mode-panel[hidden]" in css
    assert "display: none !important;" in css

    for marker in (
        "runShelfLongshot",
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
    assert "harnessApplyStartup" in harness and "studioState" in harness
    assert "studioJob" in harness and "harnessInstallFetchMocks" in harness


def test_studio_home_v2_variant_guard_and_dev_panel() -> None:
    """AC-HP2-23 variant guard + DEV-HARNESS dev panel。"""
    guard = (STUDIO_DIR / "homepage-v2" / "variant-guard.js").read_text(encoding="utf-8")
    panel = (STUDIO_DIR / "homepage-v2" / "dev-panel.js").read_text(encoding="utf-8")
    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
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
    assert "readServerBucketId" in bucket
    assert "resolveBucketId" in bucket
    assert "travelogue.studio.eventRing" in analytics
    assert "bucket_id" in (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "lazySrc" in carousel or "lazy" in carousel


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
    """运行 v2 纯逻辑 node 单测（carousel + lightbox 阈值）；无 node 则跳过。"""
    node = shutil.which("node")
    if not node:
        pytest.skip("node 不可用，跳过 JS 单测")
    js_dir = Path(__file__).resolve().parent / "js"
    test_files = [
        str(js_dir / "carousel-logic.test.mjs"),
        str(js_dir / "lightbox-logic.test.mjs"),
        str(js_dir / "viewport-logic.test.mjs"),
        str(js_dir / "layout-tier.test.mjs"),
    ]
    try:
        result = subprocess.run(
            [node, "--test", *test_files],
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


def test_studio_home_v2_shelf_module() -> None:
    """M20-e · Web 书架（§8）。"""
    shelf = (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "\ufffd" not in shelf
    assert "renderShelf" in shelf
    assert "你的游记画册" in shelf
    assert "更新长图" in shelf            # stale → 更新长图
    assert "算法待更新" in shelf
    assert "重新排版" in shelf
    assert "longshotStale" in shelf
    assert "algorithmStale" in shelf
    assert "isDemoTrip" in shelf          # demo → 示例徽章
    assert "openImportSheet" in shelf     # 新建 → Sheet
    assert "previewRelPath" in shelf      # 封面派生
    assert "loadMoreShelf" in shelf
    assert "fetchTripsPage" in shelf
    assert "加载更多" in shelf
    assert "即将上线" not in shelf
    assert "shelf-menu.js" in shelf
    assert "v2-shelf__card" in shelf
    assert "v2-shelf__menu-btn" in (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")

    html = (STUDIO_DIR / "studio-home-v2.html").read_text(encoding="utf-8")
    assert "studio-modal.css" in html
    modal_css = (STUDIO_DIR / "studio-modal.css").read_text(encoding="utf-8")
    assert ".studio__modal-backdrop" in modal_css
    assert "position: fixed" in modal_css
    assert "z-index: 6000" in modal_css

    modal_js = (STUDIO_DIR / "studio-modal.js").read_text(encoding="utf-8")
    assert "studio-modal-open" in modal_js
    assert "preventScroll" in modal_js

    menu = (STUDIO_DIR / "homepage-v2" / "shelf-menu.js").read_text(encoding="utf-8")
    assert "保存长图" in menu
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
    assert "V2.reroute" in shelf_longshot

    trips_client = (STUDIO_DIR / "homepage-v2" / "trips-client.js").read_text(encoding="utf-8")
    assert "deleteTrip" in trips_client
    assert "studioAuthHeaders" in trips_client
    assert 'method: "DELETE"' in trips_client

    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
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

    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
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
        "shelf_longshot_start", "shelf_longshot_success",
    ):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS

    # 客户端 analytics.js ALLOWED 同步
    analytics = (STUDIO_DIR / "js" / "analytics.js").read_text(encoding="utf-8")
    for ev in ("homepage_view", "cta_click", "spread_page_view", "shelf_resume_click"):
        assert ev in analytics

    bootstrap = (STUDIO_DIR / "homepage-v2" / "bootstrap.js").read_text(encoding="utf-8")
    assert "experiment_exposure" in bootstrap
    assert "homepage_view" in bootstrap
    assert "_viewTracked" in bootstrap  # 仅最终态首帧一次

    sheet = (STUDIO_DIR / "homepage-v2" / "import-sheet.js").read_text(encoding="utf-8")
    assert "cta_click" in sheet
    assert "sheet_close" in sheet
    assert "sheet_abandon" in sheet

    carousel = (STUDIO_DIR / "homepage-v2" / "carousel.js").read_text(encoding="utf-8")
    assert "spread_page_view" in carousel

    shelf = (STUDIO_DIR / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    assert "shelf_resume_click" in shelf

    lightbox = (STUDIO_DIR / "homepage-v2" / "lightbox.js").read_text(encoding="utf-8")
    assert "lightbox_open" in lightbox


@pytest.mark.legacy_homepage
def test_studio_v3_experiment_exposure_wired() -> None:
    """M20-j · v3 对照组 holdback 曝光（TELEMETRY §2 experiment_exposure）。"""
    studio_js_path = STUDIO_DIR / "studio.js"
    if not studio_js_path.exists():
        pytest.skip("M21-e2 之后已删除完整 v3 入口")
    studio_js = studio_js_path.read_text(encoding="utf-8")
    assert "resolveBucketId" in studio_js
    assert "./js/bucket.js" in studio_js
    assert "homepage-v2/bucket" not in studio_js
    assert "experiment_exposure" in studio_js
    assert 'variant: "v3"' in studio_js


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
    assert 'id="v2-tab-demo"' in html
    assert "#v2-web-cell" in html or 'id="v2-web-cell"' in html

    css = (STUDIO_DIR / "studio-home-v2.css").read_text(encoding="utf-8")
    # 隐藏的 fixed 覆盖层不得拦截点击
    assert "#v2-unsupported[hidden]" in css
    assert "display: none !important" in css
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
def test_studio_home_gate_off_serves_v3_at_root(tmp_path: Path, monkeypatch) -> None:
    """AC-HP2-23 回滚 · TRAVELOGUE_STUDIO_HOMEPAGE_V2=off → GET / 仍 v3。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        for marker in V3_HOME_MARKERS:
            assert marker in html, marker
        assert "studio-home-v2.css" not in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_off_legacy_root_uses_frozen_classic(tmp_path: Path, monkeypatch) -> None:
    """M21-e2 · off 模式根路径回退到冻结 classic。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert "Travelogue Studio Classic (Deprecated)" in html
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
def test_studio_home_gate_classic_serves_v3(tmp_path: Path, monkeypatch) -> None:
    """M20-j · GET /classic 始终 v3（on 模式下 v3 迁 classic）。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "on")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/classic", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        for marker in V3_HOME_MARKERS:
            assert marker in html, marker
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
def test_studio_home_gate_auto_control_stays_v3(tmp_path: Path, monkeypatch) -> None:
    """M20-j · auto 10% · 对照组 UA → 200 v3。"""
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
    """门控模块已接入 studio_routes + static_handlers。"""
    routes = (REPO_ROOT / "travelogue" / "web" / "studio_routes.py").read_text(encoding="utf-8")
    static = (
        REPO_ROOT / "travelogue" / "web" / "studio_handlers" / "static_handlers.py"
    ).read_text(encoding="utf-8")
    assert "_dispatch_home_root" in routes
    assert "handle_home_root" in routes
    assert "handle_home_root" in static
    assert "HOME_CLASSIC_PATH" in routes
    gate = (REPO_ROOT / "travelogue" / "web" / "studio_homepage_gate.py").read_text(encoding="utf-8")
    assert "TRAVELOGUE_STUDIO_HOMEPAGE_V2" in gate
    assert "decide_root_variant" in gate
