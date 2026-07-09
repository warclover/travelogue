"""AC-ARC-14a-d · preview toolbar Playwright fixtures (golden trip + demo assets)."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from tests._repo_root import repo_root
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from travelogue.paths import TEMPLATE_VISUAL_JOURNAL
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_trip_surfaces
from travelogue.web.studio_jobs import reset_job_store

ROOT = repo_root(__file__)
GOLDEN_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"
DEFAULT_TRIP_ID = "arc14-preview"
DEFAULT_STYLE = "split-mat"


def demo_assets_available() -> bool:
    return DEMO_ASSETS.is_dir()


def seed_arc14_preview_trip(
    trips_dir: Path,
    trip_id: str = DEFAULT_TRIP_ID,
    *,
    cover_opening_style: str = DEFAULT_STYLE,
) -> str:
    """Write trip.json + assets + rendered index / present surfaces for Studio preview."""
    if not demo_assets_available():
        pytest.skip("demo assets not present")

    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    trip = json.loads(GOLDEN_FIXTURE.read_text(encoding="utf-8"))
    trip["tripId"] = trip_id
    trip.setdefault("meta", {})["coverOpeningStyle"] = cover_opening_style
    trip = prepare_trip_web_screens(trip)

    shutil.copytree(DEMO_ASSETS, trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")

    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    web_index, _mobile, present = render_trip_surfaces(
        trip_dir / "trip.json",
        validate=False,
    )
    assert web_index.is_file(), "expected draft index.html"
    assert present is not None and present.is_file(), "expected index-present.html"
    html = web_index.read_text(encoding="utf-8")
    assert "cover-opening__title" in html
    assert 'data-present-preview-url="index-present.html"' in html
    present_html = present.read_text(encoding="utf-8")
    assert 'data-screenplay="on"' in present_html
    assert 'data-screenplay-action="next"' in present_html
    return trip_id


@contextmanager
def arc14_studio_browser(
    tmp_path: Path,
    *,
    trip_id: str = DEFAULT_TRIP_ID,
    query: str = "",
    viewport: dict | None = None,
) -> Iterator[tuple[object, object, str, str]]:
    """Launch Chromium against a seeded Studio server; yields (playwright, page, base, trip_id)."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    seed_arc14_preview_trip(trips_dir, trip_id)

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    suffix = f"?{query.lstrip('?')}" if query else ""
    url = f"{base}/{trip_id}/index.html{suffix}"

    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page(viewport=viewport or {"width": 1280, "height": 900})
    try:
        page.goto(url, wait_until="networkidle")
        yield pw, page, base, trip_id
    finally:
        browser.close()
        pw.stop()
        server.shutdown()
        server.server_close()


def wait_preview_dock(page, *, timeout: float = 15_000) -> None:
    page.locator(".preview-toolbar__dock").wait_for(state="visible", timeout=timeout)


def wait_cover_title(page, *, timeout: float = 10_000) -> None:
    page.locator(".cover-opening__title").wait_for(state="visible", timeout=timeout)
