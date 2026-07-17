"""P1 · 设置项变更可观测：UI → PATCH /__travelogue/config 字段。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from travelogue.web.studio_jobs import reset_job_store

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
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _goto_v2(page, base: str) -> None:
    page.add_init_script(
        """
        try {
          localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1');
        } catch (e) {}
        """
    )
    page.goto(base + "/", wait_until="networkidle")
    page.evaluate(
        """
        () => {
          const el = document.getElementById('studio-capability-card-root');
          if (el) el.hidden = true;
        }
        """
    )


def _open_settings(page) -> None:
    page.locator("#v2-settings-toggle").click()
    page.wait_for_function(
        "() => { const p = document.getElementById('v2-settings-popover'); return p && !p.hidden; }",
        timeout=10_000,
    )


def test_p1_settings_patch_vision_copy_layout(studio_server) -> None:
    """改场景分析 / 复制源文件 → PATCH；layout.scoring 随 advanced 同包可观测。"""
    patches: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(15_000)

        def _on_request(req) -> None:
            if req.method != "PATCH" or "/__travelogue/config" not in req.url:
                return
            try:
                patches.append(json.loads(req.post_data or "{}"))
            except Exception:
                patches.append({})

        page.on("request", _on_request)
        _goto_v2(page, studio_server["base"])
        page.wait_for_function(
            "() => document.getElementById('v2-frame') && !document.getElementById('v2-frame').hidden",
            timeout=15_000,
        )
        # 实验控件必须在 DOM（智能排版随 vision PATCH 同包发送）
        assert page.evaluate(
            "() => !!(document.getElementById('v2-settings-experimental') "
            "&& document.getElementById('studio-cfg-layout-scoring'))"
        )
        _open_settings(page)

        with page.expect_response(
            lambda r: r.request.method == "PATCH" and "/__travelogue/config" in r.url,
            timeout=10_000,
        ):
            # 底层 select 为 sr-only（手风琴用 seg）；force 跳过可见性门禁
            page.locator("#studio-cfg-vision").select_option("true", force=True)
        vision = next(b for b in patches if "vision" in b)
        assert vision["vision"].get("enabled") == "true"
        assert isinstance(vision.get("layout", {}).get("scoring"), dict)
        assert "enabled" in vision["layout"]["scoring"]

        page.evaluate(
            "() => { const z = document.getElementById('v2-settings-storage-section'); if (z) z.open = true; }"
        )
        with page.expect_response(
            lambda r: r.request.method == "PATCH" and "/__travelogue/config" in r.url,
            timeout=10_000,
        ):
            page.locator("#studio-cfg-copy-source").select_option("false", force=True)
        copy = next(
            b for b in patches if "ingest" in b and "copySourceFiles" in b.get("ingest", {})
        )
        assert copy["ingest"].get("copySourceFiles") is False

        browser.close()


def test_settings_accordion_zones_ai_modal_and_seg(studio_server) -> None:
    """手风琴：默认展开导入 · AI zone→Modal · segmented 改场景分析可 PATCH。"""
    patches: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(15_000)

        def _on_request(req) -> None:
            if req.method != "PATCH" or "/__travelogue/config" not in req.url:
                return
            try:
                patches.append(json.loads(req.post_data or "{}"))
            except Exception:
                patches.append({})

        page.on("request", _on_request)
        _goto_v2(page, studio_server["base"])
        page.wait_for_function(
            "() => document.getElementById('v2-frame') && !document.getElementById('v2-frame').hidden",
            timeout=15_000,
        )
        _open_settings(page)

        state = page.evaluate(
            """() => {
              const imp = document.getElementById('v2-settings-zone-import');
              const ai = document.getElementById('v2-settings-zone-ai');
              const ap = document.getElementById('v2-settings-zone-appearance');
              const st = document.getElementById('v2-settings-storage-section');
              const metaImp = document.getElementById('v2-settings-meta-import');
              const metaAi = document.getElementById('v2-settings-meta-ai');
              return {
                importOpen: !!(imp && imp.open),
                aiOpen: !!(ai && ai.open),
                appearanceOpen: !!(ap && ap.open),
                storageOpen: !!(st && st.open),
                metaImport: metaImp ? metaImp.textContent : '',
                metaAi: metaAi ? metaAi.textContent : '',
                hasEntry: !!document.getElementById('studio-llm-settings-entry'),
                hasZones: !!document.querySelector('.v2-settings-zones'),
              };
            }"""
        )
        assert state["hasZones"] is True
        assert state["importOpen"] is True
        assert state["aiOpen"] is False
        assert state["appearanceOpen"] is False
        assert state["storageOpen"] is False
        assert "行程" in state["metaImport"]
        assert state["metaAi"]
        assert state["hasEntry"] is True

        # AI zone → 打开写作引擎 Modal（失败屏仍直接 Modal；此处测设置内发现路径）
        page.locator("#v2-settings-zone-ai > summary").click()
        page.wait_for_function(
            "() => { const z = document.getElementById('v2-settings-zone-ai'); return z && z.open; }",
            timeout=5_000,
        )
        page.locator("#studio-llm-settings-entry").click()
        page.wait_for_function(
            "() => { const r = document.getElementById('studio-llm-settings-root'); return r && !r.hidden; }",
            timeout=10_000,
        )
        assert page.locator("#studio-llm-settings-title").inner_text()
        page.locator(".studio-llm-settings__close").click()
        page.wait_for_function(
            "() => { const r = document.getElementById('studio-llm-settings-root'); return !r || r.hidden; }",
            timeout=5_000,
        )

        # Modal 关闭后设置应仍开（点击 Modal 不得关掉 Popover）
        assert page.evaluate(
            "() => { const p = document.getElementById('v2-settings-popover'); return p && !p.hidden; }"
        )
        page.evaluate(
            """() => {
              const ai = document.getElementById('v2-settings-zone-ai');
              const imp = document.getElementById('v2-settings-zone-import');
              if (ai) ai.open = false;
              if (imp) imp.open = true;
            }"""
        )

        # segmented：先拨到「关」再拨「开」，保证一定触发 PATCH
        page.locator(
            '[data-seg-for="studio-cfg-vision"] .v2-settings-seg__btn[data-value="false"]'
        ).click()
        page.wait_for_function(
            "() => document.getElementById('studio-cfg-vision').value === 'false'",
            timeout=5_000,
        )
        with page.expect_response(
            lambda r: r.request.method == "PATCH" and "/__travelogue/config" in r.url,
            timeout=10_000,
        ):
            page.locator(
                '[data-seg-for="studio-cfg-vision"] .v2-settings-seg__btn[data-value="true"]'
            ).click()
        vision = next(
            b for b in reversed(patches) if "vision" in b and b["vision"].get("enabled") == "true"
        )
        assert vision["vision"].get("enabled") == "true"
        assert page.evaluate(
            "() => document.getElementById('studio-cfg-vision').value"
        ) == "true"
        meta_after = page.evaluate(
            "() => document.getElementById('v2-settings-meta-import').textContent"
        )
        assert "场景·开" in meta_after

        # 存储 zone 仍在 DOM，且可程序化展开（复制 PATCH 见同文件 P1；行程 seg 与场景同 bindSegControls）
        assert page.evaluate(
            """() => {
              const st = document.getElementById('v2-settings-storage-section');
              const copy = document.getElementById('studio-cfg-copy-source');
              const cluSeg = document.querySelector('[data-seg-for="studio-cfg-clustering"]');
              if (!st || !copy || !cluSeg) return false;
              st.open = true;
              return st.open === true && !!copy;
            }"""
        )

        browser.close()


def test_settings_focus_storage_deeplink(studio_server) -> None:
    """深链 openSettings({ focus: 'storage' }) 展开存储区并刷占用。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(15_000)
        _goto_v2(page, studio_server["base"])
        page.wait_for_function(
            "() => document.getElementById('v2-frame') && !document.getElementById('v2-frame').hidden",
            timeout=15_000,
        )

        page.evaluate(
            """async () => {
              const mod = await import('/__studio/homepage-v2/settings-panel.js');
              mod.openSettings({ focus: 'storage', source: 'test_focus_storage' });
            }"""
        )
        page.wait_for_function(
            """() => {
              const p = document.getElementById('v2-settings-popover');
              const st = document.getElementById('v2-settings-storage-section');
              return p && !p.hidden && st && st.open;
            }""",
            timeout=10_000,
        )
        page.wait_for_function(
            """() => {
              const t = document.getElementById('studio-storage-usage-line');
              return t && t.textContent && t.textContent.trim().length > 0;
            }""",
            timeout=10_000,
        )
        usage = page.evaluate(
            "() => document.getElementById('studio-storage-usage-line').textContent"
        )
        assert usage and ("作品库" in usage or "估算" in usage or "无法" in usage)
        assert page.locator("#studio-storage-cleanup-btn").count() == 1
        assert page.locator("#studio-cfg-copy-source").count() == 1

        page.locator("#v2-settings-close").click()
        page.wait_for_function(
            "() => document.getElementById('v2-settings-popover').hidden === true",
            timeout=5_000,
        )
        browser.close()
