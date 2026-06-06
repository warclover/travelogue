"""Studio 首页 v2 · AC 自动验收 e2e（Playwright）。

对照 docs/studio-homepage-v2/AC-VERIFICATION.md 标「自动」项：
  AC-HP2-02 双 demo-flag · 04/08/09 carousel · 06 ⤢ Lightbox · 07 横拖不误触
  10 CTA→Sheet · 11 书架无 Bento 闪屏 · 12 iPad 横屏双列 · 13/14 Unsupported
  15 取消无半成品 · 16 刷新续 poll · 17 冷启动静帧 · 18 FirstSuccess 壳层 · 19 键盘 ←/→
  20 对比度冒烟 · 21 触控 ≥44px · 22 assets 失败不白屏 · 23 Import 禁切 variant
  24 Sheet focus trap/Esc/归还 · 25 homepage_view 时序 · demo-showcase WebP 200 · 06 轻点 Lightbox
  M20-j holdback redirect → experiment_exposure（bucket_id 与 cookie 一致）

依赖 dev harness（DEV-HARNESS §2/§3，loopback 自动启用）：studioFixture / studioAssetsFail / studioJob。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.web.studio_homepage_gate import stable_bucket
from travelogue.web.studio_jobs import reset_job_store
from tests.test_studio_server import _free_port, _start_studio_server

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

MANIFEST_PAGES = 5  # templates/studio/assets/demo-showcase/manifest.json


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _wait_visible(page, el_id: str, timeout: int = 20_000) -> None:
    # 用 computed style 判断，兼容 position:fixed（offsetParent 恒为 null）。
    page.wait_for_function(
        """
        (id) => {
          const el = document.getElementById(id);
          if (!el || el.hidden) return false;
          const cs = getComputedStyle(el);
          return cs.display !== 'none' && cs.visibility !== 'hidden'
            && el.getClientRects().length > 0;
        }
        """,
        arg=el_id,
        timeout=timeout,
    )


def _goto_v2(page, base: str, query: str = "") -> None:
    # M21-c 后 v2 主入口收敛到根路径；保留 helper 名称避免批量改用例名。
    url = base + "/" + (("?" + query) if query else "")
    page.goto(url, wait_until="networkidle")


def _install_frame_flash_tracker(page) -> None:
    """AC-HP2-11：从首帧起追踪 #v2-frame 是否曾可见。"""
    page.add_init_script(
        """
        (() => {
          window.__v2FrameFlash = false;
          const check = () => {
            const f = document.getElementById('v2-frame');
            if (!f || f.hidden) return;
            const cs = getComputedStyle(f);
            if (cs.display !== 'none' && cs.visibility !== 'hidden'
                && f.getClientRects().length > 0) {
              window.__v2FrameFlash = true;
            }
          };
          new MutationObserver(check).observe(document.documentElement, {
            subtree: true,
            attributes: true,
            attributeFilter: ['hidden', 'class', 'style'],
          });
          document.addEventListener('DOMContentLoaded', check);
          setInterval(check, 16);
        })();
        """
    )


def _contrast_ratio(page, selector: str) -> float:
    """WCAG 相对亮度对比度（computed color/background）。"""
    return page.evaluate(
        """
        (sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const cs = getComputedStyle(el);
          const parse = (raw) => {
            if (!raw || raw === 'transparent') return null;
            const m = raw.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
            if (raw.startsWith('#')) {
              const hex = raw.slice(1);
              const full = hex.length === 3
                ? hex.split('').map((c) => c + c).join('')
                : hex;
              return [
                parseInt(full.slice(0, 2), 16),
                parseInt(full.slice(2, 4), 16),
                parseInt(full.slice(4, 6), 16),
              ];
            }
            return null;
          };
          const lum = ([r, g, b]) => {
            const lin = [r, g, b].map((c) => {
              const v = c / 255;
              return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
            });
            return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
          };
          const fg = parse(cs.color);
          let bg = parse(cs.backgroundColor);
          if (!fg || !bg) return 0;
          const l1 = lum(fg) + 0.05;
          const l2 = lum(bg) + 0.05;
          return Math.max(l1, l2) / Math.min(l1, l2);
        }
        """,
        selector,
    )


def test_ac_hp2_02_demo_flags(studio_server) -> None:
    """AC-HP2-02 · 卷轴说明 + 预览 Tab（示例 / 我的）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")
        assert "横滑" in page.locator("#v2-carousel-hint").inner_text()
        assert page.locator("#v2-tab-demo").is_visible()
        assert page.locator("#v2-tab-demo").evaluate("el => el.classList.contains('is-active')")
        assert page.locator("#v2-bench-source-tabs").is_visible()
        browser.close()


def test_ac_hp2_04_09_19_carousel(studio_server) -> None:
    """AC-HP2-04 dots=pages · 09 clamp 不 wrap · 19 键盘 ←/→。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        # AC-04：dots 数量 === manifest.pages.length
        page.wait_for_function(
            "(n) => document.querySelectorAll('#v2-carousel-dots button').length === n",
            arg=MANIFEST_PAGES,
            timeout=10_000,
        )

        prev = page.locator("#v2-carousel-prev")
        nxt = page.locator("#v2-carousel-next")
        # AC-09：起点 prev disabled，无 wrap
        assert prev.is_disabled()
        assert not nxt.is_disabled()

        # AC-19：键盘 →，aria-current 前移
        web = page.locator("#v2-web-cell")
        web.focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(120)
        cur = page.evaluate(
            "() => { const d = document.querySelector('#v2-carousel-dots [aria-current=\\\"true\\\"]'); return d ? Number(d.dataset.index) : -1; }"
        )
        assert cur >= 1

        # 连点 next 到末尾 → next disabled（clamp 不 wrap）
        for _ in range(MANIFEST_PAGES + 2):
            if nxt.is_disabled():
                break
            nxt.click()
            page.wait_for_timeout(60)
        assert nxt.is_disabled()
        assert not prev.is_disabled()
        browser.close()


def test_ac_hp2_10_cta_opens_sheet(studio_server) -> None:
    """AC-HP2-10 · 主 CTA → Sheet；路径输入仅在 Sheet 内（Bento 不暴露）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        # Bento 内不应有可见路径输入
        assert not page.locator("#v2-album-path").is_visible()

        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")
        assert page.locator("#v2-sheet-pick").is_visible()
        browser.close()


def test_ac_hp2_24_sheet_focus_trap_esc(studio_server) -> None:
    """AC-HP2-24 · Sheet focus trap + Esc 关闭 + 焦点归还 CTA。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")

        # 焦点落在 Sheet 内
        in_sheet = page.evaluate(
            "() => { const s = document.getElementById('v2-import-sheet'); return s && s.contains(document.activeElement); }"
        )
        assert in_sheet

        # Esc 关闭 + 焦点归还 CTA
        page.keyboard.press("Escape")
        page.wait_for_function(
            "() => document.getElementById('v2-sheet-root').hidden === true",
            timeout=5_000,
        )
        focused_cta = page.evaluate(
            "() => document.activeElement === document.getElementById('v2-cta')"
        )
        assert focused_cta
        browser.close()


def test_ac_hp2_v2_sheet_background_inert(studio_server) -> None:
    """v2 Sheet 打开时背景 inert；关闭后恢复。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")
        inert_on = page.evaluate(
            """
            () => {
              const hero = document.getElementById('v2-bento-hero');
              const shelf = document.getElementById('v2-shelf');
              return {
                heroInert: hero ? hero.hasAttribute('inert') : false,
                heroHidden: hero ? hero.getAttribute('aria-hidden') : null,
                shelfInert: shelf ? shelf.hasAttribute('inert') : false,
                shelfHidden: shelf ? shelf.getAttribute('aria-hidden') : null,
              };
            }
            """
        )
        assert inert_on["heroInert"] and inert_on["heroHidden"] == "true"
        assert inert_on["shelfInert"] and inert_on["shelfHidden"] == "true"

        page.keyboard.press("Escape")
        page.wait_for_function(
            "() => document.getElementById('v2-sheet-root').hidden === true",
            timeout=5_000,
        )
        inert_off = page.evaluate(
            """
            () => {
              const hero = document.getElementById('v2-bento-hero');
              const shelf = document.getElementById('v2-shelf');
              return {
                heroInert: hero ? hero.hasAttribute('inert') : false,
                heroHidden: hero ? hero.hasAttribute('aria-hidden') : false,
                shelfInert: shelf ? shelf.hasAttribute('inert') : false,
                shelfHidden: shelf ? shelf.hasAttribute('aria-hidden') : false,
              };
            }
            """
        )
        assert not inert_off["heroInert"] and not inert_off["heroHidden"]
        assert not inert_off["shelfInert"] and not inert_off["shelfHidden"]
        browser.close()


def test_ac_hp2_v2_advanced_popover_focus_trap(studio_server) -> None:
    """高级设置 Popover：打开聚焦、Tab 不逃逸、Esc 关闭回焦 toggle。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        toggle = page.locator("#v2-advanced-toggle")
        toggle.click()
        page.wait_for_function(
            """
            () => {
              const pop = document.getElementById('v2-advanced-popover');
              return !!pop && !pop.hidden;
            }
            """,
            timeout=5_000,
        )
        focused_in_popover = page.evaluate(
            """
            () => {
              const pop = document.getElementById('v2-advanced-popover');
              return pop && pop.contains(document.activeElement);
            }
            """
        )
        assert focused_in_popover

        for _ in range(6):
            page.keyboard.press("Tab")
            inside = page.evaluate(
                """
                () => {
                  const pop = document.getElementById('v2-advanced-popover');
                  return pop && pop.contains(document.activeElement);
                }
                """
            )
            assert inside

        page.keyboard.press("Escape")
        page.wait_for_function(
            """
            () => {
              const pop = document.getElementById('v2-advanced-popover');
              return !!pop && pop.hidden;
            }
            """,
            timeout=5_000,
        )
        focused_toggle = page.evaluate(
            "() => document.activeElement === document.getElementById('v2-advanced-toggle')"
        )
        assert focused_toggle
        browser.close()


def test_ac_hp2_21_touch_targets(studio_server) -> None:
    """AC-HP2-21 · 关键触控目标 ≥44px。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")
        cta_box = page.locator("#v2-cta").bounding_box()
        assert cta_box and cta_box["height"] >= 44

        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")
        close_box = page.locator("#v2-sheet-close").bounding_box()
        assert close_box and min(close_box["width"], close_box["height"]) >= 44
        browser.close()


def test_ac_hp2_22_assets_fail_no_whitescreen(studio_server) -> None:
    """AC-HP2-22 · manifest 失败仍显示 Slogan + CTA（不白屏）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "studioAssetsFail=1")
        _wait_visible(page, "v2-frame")
        assert page.locator("#v2-cta").is_visible()
        assert page.locator("#v2-headline").is_visible()
        browser.close()


def test_ac_hp2_13_unsupported_phone(studio_server) -> None:
    """AC-HP2-13 · 手机宽度 → Unsupported，Bento 不显示。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-unsupported")
        bento_hidden = page.evaluate(
            "() => { const m = document.getElementById('v2-bento-main'); return !m || m.hidden; }"
        )
        assert bento_hidden
        browser.close()


def test_ac_hp2_11_idle_returning_shelf(studio_server) -> None:
    """AC-HP2-11 · trips≥1 → Bento 与书架区同屏。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "studioFixture=multi")
        _wait_visible(page, "v2-frame")
        _wait_visible(page, "v2-shelf")
        assert "你的游记画册" in page.locator("#v2-shelf").inner_text()
        assert page.locator("#v2-carousel-hint").is_visible()
        browser.close()


def test_ac_hp2_bento_tab_mine(studio_server) -> None:
    """D-13 · 有用户画册时可切「我的最近一本」Tab。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "studioFixture=multi")
        _wait_visible(page, "v2-frame")
        mine = page.locator("#v2-tab-mine")
        page.wait_for_function(
            "() => !document.getElementById('v2-tab-mine').disabled",
            timeout=10_000,
        )
        mine.click()
        page.wait_for_function(
            "() => document.getElementById('v2-tab-mine').classList.contains('is-active')",
            timeout=5_000,
        )
        assert page.locator("#v2-tab-mine").evaluate("el => el.classList.contains('is-active')")
        assert not page.locator("#v2-tab-demo").evaluate("el => el.classList.contains('is-active')")
        assert "Harness" in page.locator("#v2-bench-title").inner_text()
        browser.close()


def test_ac_hp2_15_cancel_no_half_trip(studio_server) -> None:
    """AC-HP2-15 · 取消导入 → Modal 确认 → trips 无新 slug。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            studio_server["base"],
            "dev=1&studioFixture=empty&studioJob=running",
        )
        _wait_visible(page, "v2-frame")

        trips_before = page.evaluate(
            "() => fetch('/__travelogue/trips?limit=20').then(r => r.json()).then(d => (d.trips || []).length)"
        )

        page.locator("#v2-cta").click()
        _wait_visible(page, "v2-sheet-root")
        page.locator(".v2-sheet__details").nth(1).click()
        page.locator("#v2-album-path").fill("/harness/album")
        page.locator("#v2-path-submit").click()
        _wait_visible(page, "v2-sheet-confirm")
        page.locator("#v2-sheet-start-quick").click()
        _wait_visible(page, "v2-import-cancel")

        page.locator("#v2-import-cancel").click()
        confirm = page.locator(".studio__modal .studio__btn--primary")
        if confirm.count() > 0:
            confirm.click()
        page.wait_for_timeout(400)

        trips_after = page.evaluate(
            "() => fetch('/__travelogue/trips?limit=20').then(r => r.json()).then(d => (d.trips || []).length)"
        )
        assert trips_after == trips_before == 0

        active_job = page.evaluate(
            "() => sessionStorage.getItem('travelogue.studio.activeJobId')"
        )
        # dev harness 的 studioJob=running 可能持续注入占位 jobId。
        assert active_job in (None, "harness-job-1")
        browser.close()


def test_ac_hp2_16_refresh_resumes_import(studio_server) -> None:
    """AC-HP2-16 · 刷新后 activeJobId 续 poll Importing。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            studio_server["base"],
            "dev=1&studioFixture=empty&studioState=importing-resume&studioJob=running",
        )
        _wait_visible(page, "v2-import-cancel")

        page.reload(wait_until="networkidle")
        _wait_visible(page, "v2-import-cancel")

        stage = page.locator("#v2-import-stage").inner_text()
        assert stage  # 续 poll 后应有阶段文案
        assert page.locator("#v2-import-progress").get_attribute("role") == "progressbar"
        assert page.locator("#v2-import-progress").get_attribute("aria-valuenow") is not None
        assert page.locator(".v2-skip-link").get_attribute("href") == "#v2-import-cancel"
        browser.close()


def test_ac_hp2_failed_overlay(studio_server) -> None:
    """Import Failed 专屏 · harness studioState=failed。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioState=failed&studioFixture=empty")
        _wait_visible(page, "v2-failure-retry")
        assert page.locator("#v2-failure-msg").is_visible()
        assert "重试" in page.locator("#v2-failure-retry").inner_text()
        browser.close()


def test_ac_hp2_failed_retry_upload_reopens_sheet(studio_server) -> None:
    """上传失败重试：应回到导入 Sheet 重新选择文件，而非直接退出失败态。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=empty")
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            () => {
              sessionStorage.setItem(
                'travelogue.studio.activePending',
                JSON.stringify({ uploadForm: true, fileCount: 3, title: '上传测试' })
              );
              const failure = document.getElementById('v2-failure');
              if (failure) failure.hidden = false;
            }
            """
        )
        _wait_visible(page, "v2-failure-retry")
        page.locator("#v2-failure-retry").click()
        _wait_visible(page, "v2-sheet-root")
        failure_hidden = page.evaluate("() => document.getElementById('v2-failure').hidden")
        assert failure_hidden
        pending = page.evaluate("() => sessionStorage.getItem('travelogue.studio.activePending')")
        assert pending is None
        browser.close()


def test_ac_hp2_resume_clears_stale_upload_pending(studio_server) -> None:
    """无 activeJobId 的 upload pending 应在冷启动清理，避免会话残留。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(
            """
            () => {
              sessionStorage.removeItem('travelogue.studio.activeJobId');
              sessionStorage.setItem(
                'travelogue.studio.activePending',
                JSON.stringify({ uploadForm: true, fileCount: 2, title: '待清理' })
              );
            }
            """
        )
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=empty")
        _wait_visible(page, "v2-frame")
        pending = page.evaluate("() => sessionStorage.getItem('travelogue.studio.activePending')")
        assert pending is None
        browser.close()


def test_ac_hp2_l2_carousel_lazy(studio_server) -> None:
    """L2 · carousel 第 3 屏起 deferred（studioSlowNet=1）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioSlowNet=1")
        _wait_visible(page, "v2-frame")
        lazy_count = page.evaluate(
            "() => document.querySelectorAll('#v2-carousel-track .v2-carousel__slide[data-lazy-src]').length"
        )
        assert lazy_count >= 3  # manifest 5 页 → index 2..4 lazy
        browser.close()


def test_ac_hp2_23_import_blocks_variant_switch(studio_server) -> None:
    """AC-HP2-23 · Importing 中隐藏「经典首页」链，禁止切 v3。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        assert page.locator("#v2-classic-link").is_visible()

        _goto_v2(
            page,
            studio_server["base"],
            "dev=1&studioState=importing&studioJob=running",
        )
        _wait_visible(page, "v2-import-cancel")
        classic_hidden = page.evaluate(
            "() => { const el = document.getElementById('v2-classic-link'); return !el || el.hidden; }"
        )
        assert classic_hidden
        browser.close()


def test_ac_hp2_dev_panel_visible(studio_server) -> None:
    """Dev harness · ?dev=1 注入 dev panel。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        assert page.locator("#v2-dev-panel").is_visible()
        assert page.locator("#v2-dev-copy").is_visible()
        browser.close()


def test_ac_hp2_shelf_load_more(studio_server) -> None:
    """书架 total>20 · 首屏 20 本 + 加载更多。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=many")
        _wait_visible(page, "v2-shelf")

        initial = page.locator(".v2-shelf__book:not(.v2-shelf__book--new)").count()
        assert initial == 20
        assert page.locator("#v2-shelf-load-more").is_visible()
        assert "20 / 25" in page.locator(".v2-shelf__more-hint").inner_text()

        page.locator("#v2-shelf-load-more").click()
        page.wait_for_function(
            "() => document.querySelectorAll('.v2-shelf__book:not(.v2-shelf__book--new)').length === 25",
            timeout=10_000,
        )
        assert not page.locator("#v2-shelf-load-more").is_visible()
        browser.close()


def test_ac_hp2_06_expand_opens_lightbox(studio_server) -> None:
    """AC-HP2-06 · Bento 放大入口已移除，无 ⤢ 按钮。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")
        assert page.locator("#v2-expand-scroll").count() == 0
        assert page.locator("#v2-expand-phone").count() == 0
        browser.close()


def test_ac_hp2_07_drag_does_not_open_lightbox(studio_server) -> None:
    """AC-HP2-07 · carousel 横拖 >10px 仅翻页，不误开 Lightbox。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        viewport = page.locator(".v2-carousel__viewport")
        box = viewport.bounding_box()
        assert box
        cx = box["x"] + box["width"] * 0.5
        cy = box["y"] + box["height"] * 0.5
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + 15, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)

        lb_open = page.evaluate(
            "() => document.getElementById('v2-lightbox').classList.contains('is-open')"
        )
        assert not lb_open
        browser.close()


def test_ac_hp2_08_odd_tail_left_align(studio_server) -> None:
    """AC-HP2-08 · 奇数尾页末 index 左对齐（scrollLeft ≈ maxScroll，右侧留白）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        nxt = page.locator("#v2-carousel-next")
        for target in range(1, MANIFEST_PAGES):
            if nxt.is_disabled():
                break
            nxt.click()
            page.wait_for_function(
                """
                (idx) => {
                  const dot = document.querySelector('#v2-carousel-dots [aria-current="true"]');
                  return dot && Number(dot.dataset.index) === idx;
                }
                """,
                arg=target,
                timeout=5_000,
            )

        last_idx = MANIFEST_PAGES - 1
        page.wait_for_function(
            """
            (lastIdx) => {
              const dot = document.querySelector('#v2-carousel-dots [aria-current="true"]');
              return dot && Number(dot.dataset.index) === lastIdx;
            }
            """,
            arg=last_idx,
            timeout=10_000,
        )
        page.wait_for_timeout(400)

        tail = page.evaluate(
            """
            (pageCount) => {
              const track = document.getElementById('v2-carousel-track');
              const viewport = track.parentElement;
              const dot = document.querySelector('#v2-carousel-dots [aria-current="true"]');
              const idx = dot ? Number(dot.dataset.index) : -1;
              const maxScroll = track.scrollWidth - viewport.clientWidth;
              return {
                index: idx,
                scrollLeft: track.scrollLeft,
                maxScroll,
                oddTail: pageCount % 2 === 1 && idx === pageCount - 1,
              };
            }
            """,
            MANIFEST_PAGES,
        )
        assert tail["index"] == MANIFEST_PAGES - 1
        assert tail["oddTail"]
        assert abs(tail["scrollLeft"] - tail["maxScroll"]) <= 24
        assert nxt.is_disabled()
        browser.close()


def test_ac_hp2_12_ipad_landscape_bento_grid(studio_server) -> None:
    """AC-HP2-12 · 1024×768 横屏 Bento 双列 grid，非三行堆叠。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        grid = page.evaluate(
            """
            () => {
              const g = document.querySelector('.v2-bento__grid');
              const cols = getComputedStyle(g).gridTemplateColumns.split(' ').filter(Boolean);
              return { colCount: cols.length, cols };
            }
            """
        )
        assert grid["colCount"] >= 2
        assert page.locator("#v2-web-cell").is_visible()
        assert page.locator(".v2-bento__mobile").is_visible()
        browser.close()


def test_ac_hp2_14_ipad_portrait_rotate_hint(studio_server) -> None:
    """AC-HP2-14 · 768×1024 竖屏 → Unsupported 旋转提示。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 768, "height": 1024})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-unsupported")
        title = page.locator("#v2-unsupported-title").inner_text()
        assert "旋转" in title or "横屏" in title
        bento_hidden = page.evaluate(
            "() => { const f = document.getElementById('v2-frame'); return !f || f.hidden; }"
        )
        assert bento_hidden
        browser.close()


def test_ac_hp2_20_cta_contrast(studio_server) -> None:
    """AC-HP2-20 · 主 CTA computed 对比度 ≥ WCAG AA（4.5:1）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        ratio = _contrast_ratio(page, "#v2-cta")
        assert ratio >= 4.5, f"#v2-cta contrast {ratio:.2f} < 4.5"
        browser.close()


def test_ac_hp2_demo_assets_serve_200(studio_server) -> None:
    """demo-showcase · manifest 引用 WebP 均 200（dev 占位，非 404）。"""
    statuses: list[int] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        def _on_response(resp) -> None:
            if "demo-showcase" in resp.url and resp.url.endswith(".webp"):
                statuses.append(resp.status)

        page.on("response", _on_response)
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")
        page.wait_for_timeout(600)
        assert statuses, "未捕获 demo-showcase webp 请求"
        assert all(s == 200 for s in statuses), statuses
        browser.close()


def test_ac_hp2_06_tap_opens_lightbox(studio_server) -> None:
    """AC-HP2-06 · 轻点 carousel 不再打开 Lightbox。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")

        track = page.locator("#v2-carousel-track")
        box = track.bounding_box()
        assert box
        page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
        page.wait_for_timeout(400)
        lb_open = page.evaluate(
            "() => document.getElementById('v2-lightbox').classList.contains('is-open')"
        )
        assert not lb_open
        browser.close()


def test_ac_hp2_17_importing_cold_static_bg(studio_server) -> None:
    """AC-HP2-17 · 冷启动 Importing：demo 静帧背景、无 Ken Burns。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"], "dev=1&studioState=importing-cold")
        _wait_visible(page, "v2-import-cancel")
        page.wait_for_function(
            """
            () => {
              const bg = document.getElementById('v2-bento-bg');
              return bg && /demo-showcase/.test(bg.style.backgroundImage || '');
            }
            """,
            timeout=10_000,
        )
        kenburns = page.evaluate(
            "() => document.getElementById('v2-bento-bg').classList.contains('is-kenburns')"
        )
        assert not kenburns
        browser.close()


def test_ac_hp2_18_first_success_shelf_shell(studio_server) -> None:
    """AC-HP2-18 · FirstSuccess 背景 = Bento 首屏 + 下方书架区同屏。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(
            page,
            studio_server["base"],
            "dev=1&studioState=first-success&studioFixture=multi",
        )
        _wait_visible(page, "v2-success-open")
        assert page.locator("#v2-shelf").is_visible()
        frame_visible = page.evaluate(
            "() => !document.getElementById('v2-frame').hidden"
        )
        assert frame_visible
        assert "你的游记画册" in page.locator("#v2-shelf").inner_text()
        browser.close()


def test_ac_hp2_25_homepage_view_after_state(studio_server) -> None:
    """AC-HP2-25 · homepage_view 仅在最终态确定后上报，且带 state。"""
    events: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        def _on_request(req):
            if req.method == "POST" and req.url.endswith("/__travelogue/studio-event"):
                try:
                    events.append(json.loads(req.post_data or "{}"))
                except (ValueError, TypeError):
                    pass

        page.on("request", _on_request)
        _goto_v2(page, studio_server["base"], "studioFixture=multi")
        _wait_visible(page, "v2-shelf")
        page.wait_for_timeout(300)

        views = [e for e in events if e.get("event") == "homepage_view"]
        assert views, f"未捕获 homepage_view，captured={[e.get('event') for e in events]}"
        assert views[0].get("meta", {}).get("state") == "returning"
        assert views[0].get("meta", {}).get("variant") == "v2"
        browser.close()


def test_m20j_holdback_redirect_experiment_exposure(tmp_path: Path, monkeypatch) -> None:
    """M20-j · GET / auto 10% 进组 → 302 /v2 → experiment_exposure 带 bucket_id。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    ua = "M20jTest/5"  # bucket=3 < 10
    expected_bucket = stable_bucket(ua)
    events: list[dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                user_agent=ua,
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()

            def _on_request(req):
                if req.method == "POST" and req.url.endswith("/__travelogue/studio-event"):
                    try:
                        events.append(json.loads(req.post_data or "{}"))
                    except (ValueError, TypeError):
                        pass

            page.on("request", _on_request)
            page.goto(base + "/", wait_until="networkidle")
            assert page.url.startswith(base + "/"), page.url
            assert not page.url.rstrip("/").endswith("/v2"), page.url
            page.wait_for_timeout(400)

            cookies = context.cookies()
            bucket_cookie = next(
                (c for c in cookies if c.get("name") == "travelogue.studio.hp_bucket"),
                None,
            )
            assert bucket_cookie is not None
            raw_cookie = str(bucket_cookie["value"])
            cookie_bucket = int(raw_cookie.split(".")[0])
            assert cookie_bucket == expected_bucket

            exposures = [e for e in events if e.get("event") == "experiment_exposure"]
            assert exposures, f"未捕获 experiment_exposure，captured={[e.get('event') for e in events]}"
            meta = exposures[0].get("meta", {})
            assert meta.get("variant") == "v2"
            assert meta.get("bucket_id") == expected_bucket
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_m20j_holdback_control_experiment_exposure(tmp_path: Path, monkeypatch) -> None:
    """M21-e2 · auto 10% 对照组留 legacy classic，默认不再要求 v3 exposure。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    ua = "M20jTest/1"  # bucket=70 >= 10
    expected_bucket = stable_bucket(ua)
    events: list[dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                user_agent=ua,
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()

            def _on_request(req):
                if req.method == "POST" and req.url.endswith("/__travelogue/studio-event"):
                    try:
                        events.append(json.loads(req.post_data or "{}"))
                    except (ValueError, TypeError):
                        pass

            page.on("request", _on_request)
            page.goto(base + "/", wait_until="networkidle")
            assert page.url.rstrip("/").endswith(f":{port}")
            assert "studio-home-v2.css" not in page.content()
            page.wait_for_timeout(400)

            exposures = [e for e in events if e.get("event") == "experiment_exposure"]
            assert not exposures, f"legacy classic 不应上报 v3 exposure，captured={exposures}"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_ac_hp2_23_rollback_ignores_homepage_variant(tmp_path: Path, monkeypatch) -> None:
    """AC-HP2-23 · gate off + sessionStorage homepageVariant=v2 → v3 正常、无报错。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    errors: list[str] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.add_init_script(
                """
                sessionStorage.setItem('travelogue.studio.homepageVariant', 'v2');
                """
            )
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.goto(base + "/", wait_until="networkidle")
            assert 'data-studio-v="4"' in page.content()
            assert "studio-home-v2.css" not in page.content()
            page.wait_for_selector("#studio-hero, #studio-hero-empty", timeout=15_000)
            assert not errors, f"页面报错: {errors}"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_js_error_pipeline_posts_event(studio_server) -> None:
    """P2 · window.error → js_error POST 端到端。"""
    events: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        def _on_request(req):
            if req.method == "POST" and req.url.endswith("/__travelogue/studio-event"):
                try:
                    events.append(json.loads(req.post_data or "{}"))
                except (ValueError, TypeError):
                    pass

        page.on("request", _on_request)
        _goto_v2(page, studio_server["base"], "dev=1&studioFixture=empty")
        _wait_visible(page, "v2-headline")
        page.evaluate(
            "() => window.dispatchEvent(new ErrorEvent('error', "
            "{ message: 'harness-js-error-probe', filename: 'harness.js' }))"
        )
        page.wait_for_timeout(500)

        js_errors = [e for e in events if e.get("event") == "js_error"]
        assert js_errors, f"未捕获 js_error，captured={[e.get('event') for e in events]}"
        meta = js_errors[0].get("meta", {})
        assert meta.get("variant") == "v2"
        assert "harness-js-error-probe" in (meta.get("message") or "")
        browser.close()
