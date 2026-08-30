"""2026-08-30 功能交互报告 · 导入恢复与分章导出真人复核。"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2, _wait_visible
from tests.integration.studio.test_studio_server import (
    _free_port,
    _get_json,
    _post_json,
    _start_studio_server,
)
from tests.studio_test_helpers import wait_for_job
from travelogue.config import get_config
from travelogue.config.studio import OutputRecipeBandsConfig, OutputRecipeConfig
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _recipe_on():
    base = get_config()
    return replace(
        base,
        studio=replace(
            base.studio,
            output_recipe=OutputRecipeConfig(
                enabled=True,
                bands=OutputRecipeBandsConfig(
                    sparse_max=9,
                    ambiguous_max=30,
                    narrative_chapter_hint_at=50,
                ),
            ),
        ),
    )


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port, app_config=_recipe_on())
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base, "trips_dir": trips_dir}
    finally:
        server.shutdown()
        server.server_close()


def test_invalid_path_confirm_blocks_start(studio_server) -> None:
    """BUG-03 · 不允许路径在确认页阻断开始制作。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, studio_server["base"])
        _wait_visible(page, "v2-frame")
        page.evaluate(
            """
            async () => {
              const mod = await import('/__studio/homepage-v2/import-entry.js');
              mod.openImportSheet();
            }
            """
        )
        _wait_visible(page, "v2-wizard-root")
        page.locator("#v2-wizard-more-import").evaluate(
            "el => { el.open = true; }"
        )
        page.locator("#v2-wizard-album-path").fill("C:/__travelogue_missing_folder__")
        page.locator("#v2-wizard-path-submit").click()
        page.wait_for_function(
            """
            () => {
              const start = document.getElementById('v2-wizard-start');
              const line = document.getElementById('v2-wizard-verify-line');
              return !!(start && line && start.textContent.includes('更换文件夹')
                && line.textContent.includes('请更换文件夹'));
            }
            """,
            timeout=15_000,
        )
        browser.close()


def test_demo_chapter_export_survives_single_recipe(studio_server) -> None:
    """BUG-02 · 示例 3 章 + 配方 single 时，显式按章必须落成多张。"""
    base = studio_server["base"]
    trips_dir = Path(studio_server["trips_dir"])
    status, body = _post_json(
        f"{base}/__travelogue/import",
        {"useDemoAlbum": True, "title": "示例旅途", "place": "示例", "forceStub": True},
    )
    assert status == 202, body
    last = wait_for_job(
        lambda: _get_json(f"{base}/__travelogue/status?jobId={body['jobId']}")[1],
        timeout_sec=180,
        poll_sec=0.4,
    )
    assert last.get("status") == "succeeded", last
    trip_id = last["tripId"]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _goto_v2(page, base)
        page.evaluate(
            """
            async (result) => {
              const mod = await import('/__studio/homepage-v2/first-success.js');
              mod.showFirstSuccess({ result });
            }
            """,
            {"tripId": trip_id, "title": "示例旅途", "photoCount": 16, "segmentCount": 3},
        )
        _wait_visible(page, "v2-success-open")
        hidden = page.evaluate(
            "() => document.getElementById('v2-success-set-preview').hidden"
        )
        assert hidden is True
        browser.close()

    status, export_body = _post_json(
        f"{base}/__travelogue/longshot",
        {
            "tripId": trip_id,
            "intent": "chat_longshot",
            "entrypoint": "preview",
            "segmentMode": "chapter",
            "platform": "wechat_chat",
            "scale": 1,
            "allowMissingSource": True,
        },
    )
    assert status == 202, export_body
    export_job = wait_for_job(
        lambda: _get_json(f"{base}/__travelogue/status?jobId={export_body['jobId']}")[1],
        timeout_sec=240,
        poll_sec=0.5,
    )
    assert export_job.get("status") == "succeeded", export_job
    result = export_job.get("result") or {}
    assert result.get("segmented") is True, result
    assert len(result.get("outputs") or []) >= 3, result
    current_path = trips_dir / trip_id / "导出文件" / "longshot-current.json"
    assert current_path.is_file(), list((trips_dir / trip_id).rglob("*.json"))
    current = json.loads(current_path.read_text(encoding="utf-8"))
    assert current.get("kind") == "segmented"
    assert len(current.get("files") or []) >= 3
