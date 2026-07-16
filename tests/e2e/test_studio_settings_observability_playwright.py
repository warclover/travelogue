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
            page.locator("#studio-cfg-vision").select_option("true")
        vision = next(b for b in patches if "vision" in b)
        assert vision["vision"].get("enabled") == "true"
        assert isinstance(vision.get("layout", {}).get("scoring"), dict)
        assert "enabled" in vision["layout"]["scoring"]

        with page.expect_response(
            lambda r: r.request.method == "PATCH" and "/__travelogue/config" in r.url,
            timeout=10_000,
        ):
            page.locator("#studio-cfg-copy-source").select_option("false")
        copy = next(
            b for b in patches if "ingest" in b and "copySourceFiles" in b.get("ingest", {})
        )
        assert copy["ingest"].get("copySourceFiles") is False

        browser.close()
