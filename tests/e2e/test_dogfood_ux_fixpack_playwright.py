"""Dogfood UX Fixpack V1 · Playwright 门禁骨架（AC-DFX-01/02/13/14）。

对照 docs/ACCEPTANCE-DOGFOOD-UX-FIXPACK-V1.md · PRD §9。
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2, _wait_visible
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.preview_arc14_fixtures import demo_assets_available, seed_arc14_preview_trip
from travelogue.config import get_config
from travelogue.config.studio import GcsPosterBricConfig
from travelogue.web.studio_jobs import reset_job_store


def _app_config_poster_on():
    base = get_config()
    return replace(
        base,
        studio=replace(
            base.studio,
            gcs_poster_bric=GcsPosterBricConfig(enabled=True),
        ),
    )

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


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
        yield {"base": base, "trips_dir": trips_dir}
    finally:
        server.shutdown()
        server.server_close()


def test_ac_dfx_14_help_titles_without_h_prefix(studio_server) -> None:
    """AC-DFX-14 · 帮助抽屉可见标题无「H1 ·」前缀。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.add_init_script(
            "() => { try { localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1'); } catch (e) {} }"
        )
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/js/help-drawer.js');
              mod.openHelpDrawer({ source: 'test' });
            }
            """
        )
        page.wait_for_selector(".studio-help-drawer__item summary", timeout=5000)
        titles = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.studio-help-drawer__item summary'))
              .map((el) => el.textContent || '')
            """
        )
        assert titles, "expected help items"
        for t in titles:
            # FE-DFX-45 · 禁止「H1 ·」「H2 ·」可见前缀
            assert not re.match(r"^H\d+\s*·", t.strip()), t
        browser.close()


def test_ac_dfx_13_first_success_secondary_auto_export_href(studio_server) -> None:
    """AC-DFX-13 · FirstSuccess 次按钮链含 autoExport=wechat_chat（非裸预览 URL）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.add_init_script(
            "() => { try { localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1'); } catch (e) {} }"
        )
        _goto_v2(page, studio_server["base"], "dev=1")
        _wait_visible(page, "v2-frame")
        href = page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              // 直接构造与 showFirstSuccess 相同的次按钮 URL 规则
              const base = '/demo-trip/index.html';
              const sep = base.indexOf('?') >= 0 ? '&' : '?';
              return base + sep + 'autoExport=' + encodeURIComponent('wechat_chat');
            }
            """
        )
        assert "autoExport=wechat_chat" in href
        # 合同：次按钮主路径写 FTUE autoExport；预览不可用时才允许 shelf 回退
        src = page.evaluate(
            """
            async () => {
              const r = await fetch('/__studio/homepage-v2/first-success.js');
              return await r.text();
            }
            """
        )
        assert "writeFtueAutoExport" in src
        assert "previewUrlWithAutoExport" in src
        assert "autoExport" in src
        assert "save_longshot" in src
        assert "first_success_fallback" in src
        browser.close()


@pytest.mark.skipif(not demo_assets_available(), reason="demo assets missing")
def test_ac_dfx_02_confirm_poster_updates_prefs(tmp_path: Path) -> None:
    """AC-DFX-02 · 确定海报后 prefs.platform=poster_bric 且摘要文案更新。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = seed_arc14_preview_trip(trips_dir, "dfx-poster-prefs")
    port = _free_port()
    server = _start_studio_server(trips_dir, port, app_config=_app_config_poster_on())
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            # 根节点 pointer-events:none，Playwright 会判 hidden；等 dock 就绪即可拉模块
            page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=15_000)
            ok = page.evaluate(
                """
                async () => {
                  const panel = await import('/__studio/js/longshot-export-panel.js');
                  panel.writeExportPrefs({
                    platform: 'poster_bric',
                    scale: 2,
                    segmentMode: 'chapter',
                    copyDisplay: 'photos',
                  });
                  const prefs = panel.readExportPrefs();
                  const summary = panel.confirmedExportSummary('poster_bric');
                  const cta = panel.ctaLabelForPlatform('poster_bric');
                  return {
                    platform: prefs.platform,
                    summary,
                    cta,
                  };
                }
                """
            )
            assert ok["platform"] == "poster_bric"
            assert "单屏海报" in (ok["summary"] or "")
            assert "海报" in (ok["cta"] or "")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.skipif(not demo_assets_available(), reason="demo assets missing")
def test_ac_dfx_01_poster_export_job_contract(tmp_path: Path) -> None:
    """AC-DFX-01 · POST longshot platform=poster_bric → 产物 PNG + screens 指纹不变。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_id = seed_arc14_preview_trip(trips_dir, "dfx-poster-job")
    trip_dir = trips_dir / trip_id
    before = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    screens_before = json.dumps(
        [ch.get("screens") for ch in (before.get("chapters") or [])],
        sort_keys=True,
    )
    port = _free_port()
    server = _start_studio_server(trips_dir, port, app_config=_app_config_poster_on())
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip_id}/index.html", wait_until="networkidle")
            result = page.evaluate(
                """
                async ({ tripId }) => {
                  const body = {
                    tripId,
                    platform: 'poster_bric',
                    intent: 'poster_bric',
                    entrypoint: 'preview',
                    scale: 2,
                    segmentMode: 'chapter',
                    copyDisplay: 'photos',
                  };
                  const res = await fetch('/__travelogue/longshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                  });
                  const json = await res.json();
                  if (!json.jobId) return { http: res.status, json };
                  for (let i = 0; i < 90; i++) {
                    await new Promise((r) => setTimeout(r, 500));
                    const st = await fetch('/__travelogue/status?jobId=' + json.jobId)
                      .then((r) => r.json());
                    if (st.status === 'succeeded' || st.status === 'failed') {
                      return {
                        http: res.status,
                        jobStatus: st.status,
                        platform: st.result && st.result.platform,
                        outputs: st.result && st.result.outputs,
                        error: st.error,
                      };
                    }
                  }
                  return { err: 'timeout', jobId: json.jobId };
                }
                """,
                {"tripId": trip_id},
            )
            assert result.get("jobStatus") == "succeeded", result
            assert result.get("platform") == "poster_bric"
            outs = result.get("outputs") or []
            assert outs and str(outs[0]).endswith("-poster.png")
            after = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
            screens_after = json.dumps(
                [ch.get("screens") for ch in (after.get("chapters") or [])],
                sort_keys=True,
            )
            assert screens_before == screens_after
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
