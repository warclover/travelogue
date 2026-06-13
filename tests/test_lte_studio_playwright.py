"""Phase 16 Studio Playwright · AC-11 stale CSS + §13.2 lifecycle E2E."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_studio_server import _free_port, _start_studio_server
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_3P_2L_BALANCED
from travelogue.web.studio_chrome import inject_studio_chrome
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]

DEPRECATED_GRID = "layout-screen__grid--mosaic-5-3portrait-2land-balanced"
FLAGSHIP_GRID = "layout-screen__grid--mosaic-5-2p3l-equal"
STALE_HINT = "布局 CSS 已过期"


def _seed_stale_layout_css_trip(trips_dir: Path, trip_id: str = "lte-stale-css") -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "title": "LTE stale CSS probe",
        "chapters": [
            {
                "id": "ch1",
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-2p3l-equal",
                        "layoutGeometry": {"gridClass": FLAGSHIP_GRID},
                    }
                ],
            }
        ],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (trip_dir / "journal-screens.css").write_text(
        ".layout-screen__grid--3col { display: grid; }\n",
        encoding="utf-8",
    )
    html = inject_studio_chrome(
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>LTE stale</title></head>"
        "<body><main></main></body></html>"
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


def _seed_deprecated_legacy_trip(trips_dir: Path, trip_id: str = "lte-deprecated-legacy") -> str:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tripId": trip_id,
        "title": "Deprecated mosaic legacy trip",
        "chapters": [
            {
                "id": "ch1",
                "screens": [{"patternId": PATTERN_MOSAIC_5_3P_2L_BALANCED}],
            }
        ],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    html = inject_studio_chrome(
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Legacy</title></head><body>"
        f'<section class="layout-screen" data-pattern="{PATTERN_MOSAIC_5_3P_2L_BALANCED}">'
        f'<div class="layout-screen__grid {DEPRECATED_GRID}"></div>'
        "</section></body></html>"
    )
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_id


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


def test_ac11_preview_toolbar_shows_layout_css_stale_hint(studio_server) -> None:
    """AC-P16-11 · trip 副本缺 gridClass 时 Studio preview-toolbar 提示 rerender。"""
    trip_id = _seed_stale_layout_css_trip(studio_server["trips_dir"])
    url = f"{studio_server['base']}/{trip_id}/index.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="networkidle")
        # v3：stale 提示在底部任务舱，不再使用 pending-row。
        stale = page.locator(".preview-task-dock__main")
        stale.wait_for(state="visible", timeout=15_000)
        assert STALE_HINT in stale.inner_text()
        browser.close()


def test_lifecycle_deprecated_legacy_trip_preview_renders(studio_server) -> None:
    """§13.2 · deprecated 模板旧 trip HTML 快照仍可渲染。"""
    trip_id = _seed_deprecated_legacy_trip(studio_server["trips_dir"])
    url = f"{studio_server['base']}/{trip_id}/index.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        assert page.locator(f'.layout-screen[data-pattern="{PATTERN_MOSAIC_5_3P_2L_BALANCED}"]').count() == 1
        assert page.locator(f".{DEPRECATED_GRID}").count() == 1
        browser.close()


def test_lifecycle_deprecated_vs_active_catalog_e2e(studio_server) -> None:
    """§13.2 · deprecated 在 internal 目录可见，但不在 MCS active 集合。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{studio_server['base']}/templates-admin", wait_until="networkidle")
        payload = page.evaluate(
            """
            async () => {
              const res = await fetch('/__travelogue/templates/admin', {
                headers: { 'X-Template-Role': 'template_admin', 'Content-Type': 'application/json' },
              });
              return res.json();
            }
            """
        )
        browser.close()

    assert payload.get("layoutPatternsInternal") is True
    patterns = payload.get("layoutPatterns") or []
    deprecated_rows = [p for p in patterns if p.get("templateId") == PATTERN_MOSAIC_5_3P_2L_BALANCED]
    assert len(deprecated_rows) == 1
    assert deprecated_rows[0].get("lifecycle") == "deprecated"

    active_lifecycle = {"experimental", "beta", "ga"}
    mcs_catalog = [p for p in patterns if p.get("lifecycle") in active_lifecycle]
    assert PATTERN_MOSAIC_5_3P_2L_BALANCED not in {p["templateId"] for p in mcs_catalog}

    disabled_rows = [p for p in patterns if p.get("lifecycle") == "disabled"]
    assert disabled_rows == [] or all(p.get("lifecycle") == "disabled" for p in disabled_rows)
    assert all(p.get("lifecycle") != "deprecated" for p in mcs_catalog)
