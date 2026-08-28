"""First-Session Trust V1 · W0 e2e（AC-FST-04 / 05 / 08 / 08b / 08c / 13）。

对照 docs/ACCEPTANCE-FIRST-SESSION-TRUST-V1.md · QA-FST-01 / QA-FST-03。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from tests.e2e.test_import_wizard_v3_playwright import (
    _goto_v2,
    _route_harness_import_mocks,
    _wait_visible,
    _wizard_quick_folder_to_confirm,
)
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from tests.preview_arc14_fixtures import (
    arc14_studio_browser,
    demo_assets_available,
    wait_preview_dock,
)
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def wizard_server(tmp_path: Path):
    trips_dir = tmp_path / "trips-fst"
    trips_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _route_slow_trips_list(page, gate: dict, delay_ms: int = 6000) -> None:
    """拖慢书架刷新，验证 FirstSuccess 不被 refreshTrips 阻塞（AC-FST-05）。

    ``gate["on"]`` 为 True 后才延迟，避免挡住首页首屏拉 trips。
    """

    def _trips(route) -> None:
        if gate.get("on"):
            time.sleep(delay_ms / 1000.0)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "trips": [], "total": 0}),
        )

    page.route("**/__travelogue/trips?**", _trips)
    page.route("**/__travelogue/trips", _trips)


def test_ac_fst_04_succeeded_shows_first_success_within_1s(wizard_server) -> None:
    """QA-FST-01 / AC-FST-04 · succeeded → FirstSuccess ≤1s；忙碌壳关闭。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=8,
            layout_eligible=8,
            photo_cull_enabled=True,
            import_mode="quick_share",
        )
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)

        succeeded_at: list[float] = []

        def _on_response(resp) -> None:
            if "/__travelogue/status" in resp.url and resp.ok:
                try:
                    body = resp.json()
                except Exception:
                    return
                if body.get("status") == "succeeded" and not succeeded_at:
                    succeeded_at.append(time.perf_counter())

        page.on("response", _on_response)
        page.locator("#v2-wizard-start").click()
        page.wait_for_selector("#v2-success-open", state="visible", timeout=30_000)
        shown_at = time.perf_counter()

        assert succeeded_at, "expected status poll to return succeeded"
        assert (shown_at - succeeded_at[0]) <= 1.0, (
            f"FirstSuccess lag {(shown_at - succeeded_at[0]):.3f}s > 1s"
        )

        importing = page.locator("#v2-importing")
        assert importing.count() == 0 or not importing.is_visible()
        browser.close()


def test_ac_fst_05_refresh_trips_delay_does_not_block_first_success(
    wizard_server,
) -> None:
    """AC-FST-05 · refreshTrips 慢/失败不阻止 FirstSuccess。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _route_harness_import_mocks(
            page,
            photo_count=6,
            layout_eligible=6,
            import_mode="quick_share",
        )
        trips_gate = {"on": False}
        _route_slow_trips_list(page, trips_gate, delay_ms=6000)
        _goto_v2(page, wizard_server["base"])
        _wait_visible(page, "v2-frame")
        _wizard_quick_folder_to_confirm(page)
        trips_gate["on"] = True
        page.locator("#v2-wizard-start").click()
        # 书架刷新被拖慢 6s；FirstSuccess 必须在此之前出现
        page.wait_for_selector("#v2-success-open", state="visible", timeout=3_000)
        browser.close()


def _route_longshot_instant_success(page, *, trip_id: str) -> list[str]:
    """Mock longshot job → 立刻 succeeded；记录 reveal 请求。"""
    reveal_hits: list[str] = []

    def _longshot_post(route) -> None:
        route.fulfill(
            status=202,
            content_type="application/json",
            body=json.dumps({"jobId": "fst-longshot-job"}),
        )

    def _status(route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "jobId": "fst-longshot-job",
                    "status": "succeeded",
                    "result": {
                        "platform": "wechat_chat",
                        "title": "雨后京都",
                        "displayTitle": "雨后京都",
                        "outputs": ["exports/longshot-01.png"],
                        "captureMethod": "p0",
                    },
                }
            ),
        )

    def _reveal(route) -> None:
        reveal_hits.append(route.request.url)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True}),
        )

    page.route("**/__travelogue/longshot", _longshot_post)
    page.route("**/__travelogue/status**", _status)
    page.route("**/__travelogue/reveal", _reveal)
    return reveal_hits


def test_ac_fst_08_longshot_success_surface_primary_and_no_auto_reveal(
    tmp_path: Path,
) -> None:
    """QA-FST-03 · 成功面 ≥3s；主钮「在文件夹中显示」；无发群教学；禁自动 reveal。"""
    if not demo_assets_available():
        pytest.skip("demo assets not present")

    with arc14_studio_browser(tmp_path) as (_pw, page, _base, trip_id):
        wait_preview_dock(page)
        reveal_hits = _route_longshot_instant_success(page, trip_id=trip_id)

        export_btn = page.locator(".preview-toolbar__dock-btn--export")
        export_btn.wait_for(state="visible", timeout=10_000)
        export_btn.click()

        dock = page.locator(".preview-task-dock--success")
        dock.wait_for(state="visible", timeout=20_000)

        main = page.locator(".preview-task-dock--success .preview-task-dock__main")
        main_text = main.inner_text().strip()
        assert "已导出" in main_text
        assert "长图" in main_text
        assert "打开微信" not in main_text
        assert "按文件名顺序" not in main_text
        assert "拖进微信群" not in main_text

        primary = page.locator(
            ".preview-task-dock--success .preview-task-dock__btn--primary"
        )
        assert primary.count() >= 1
        assert primary.first.inner_text().strip() == "在文件夹中显示"

        help_link = page.locator(".preview-task-dock--success .preview-task-dock__help-link")
        assert help_link.count() == 0

        # AC-FST-08 · 成功面保持可见 ≥3s（自动隐藏 8s）
        page.wait_for_timeout(3100)
        assert dock.is_visible()

        # AC-FST-08b · 成功瞬间无自动 reveal
        assert reveal_hits == [], f"unexpected auto reveal: {reveal_hits}"

        primary.first.click()
        page.wait_for_timeout(800)
        assert len(reveal_hits) >= 1, "click primary should call /__travelogue/reveal"
