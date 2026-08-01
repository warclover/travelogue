"""Long-shot capture dimension logic and share toolbar context."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.context import (
    build_render_context,
    has_share_zip,
    share_zip_filename,
)
from travelogue.render.engine import render_html, render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


def capture_dimensions(
    *,
    natural_w: int,
    natural_h: int,
    display_w: float | None = None,
    display_h: float | None = None,
    box_w: float | None = None,
    box_h: float | None = None,
    object_fit: str = "contain",
    use_display_sizes: bool = True,
    width: int = 390,
) -> tuple[int, int]:
    """Mirror of longshot.js captureDimensions + getPaintedImageSize."""
    if not use_display_sizes and natural_w > 0 and natural_h > 0:
        return width, max(1, round((natural_h / natural_w) * width))
    painted_w = display_w
    painted_h = display_h
    if box_w and box_h and box_w > 0 and box_h > 0 and natural_w > 0 and natural_h > 0:
        fit = (object_fit or "fill").lower()
        if fit in ("contain", "scale-down"):
            scale = min(box_w / natural_w, box_h / natural_h)
            painted_w = natural_w * scale
            painted_h = natural_h * scale
        elif fit == "cover":
            painted_w = box_w
            painted_h = box_h
        else:
            painted_w = box_w
            painted_h = box_h

    if painted_w and painted_h and painted_w > 0:
        h = max(1, round((painted_h / painted_w) * width))
        return width, h
    if natural_w <= 0 or natural_h <= 0:
        return width, width
    h = max(1, round((natural_h / natural_w) * width))
    return width, h


def aspect_ratio(w: int, h: int) -> float:
    return w / h if h else 0.0


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_capture_dimensions_prefers_display_box() -> None:
    """Landscape limited to ~28dvh should match screen, not full natural aspect."""
    natural_w, natural_h = 4032, 3024  # 4:3 landscape
    display_w, display_h = 390.0, 130.0  # compact on screen (~28dvh)
    w, h = capture_dimensions(
        natural_w=natural_w,
        natural_h=natural_h,
        display_w=display_w,
        display_h=display_h,
    )
    display_ratio = aspect_ratio(w, h)
    deviation = abs(display_ratio - (display_w / display_h)) / (display_w / display_h)
    assert deviation < 0.02
    assert h < round((natural_h / natural_w) * w)


def test_capture_dimensions_contain_in_web_box() -> None:
    """4:3 photo in 16:9 Web card must not export as 16:9."""
    natural_w, natural_h = 1600, 1200  # 4:3
    box_w, box_h = 960.0, 540.0  # 16:9 layout box (wrong if used raw)
    w, h = capture_dimensions(
        natural_w=natural_w,
        natural_h=natural_h,
        box_w=box_w,
        box_h=box_h,
        object_fit="contain",
    )
    expected_ratio = natural_w / natural_h
    got_ratio = aspect_ratio(w, h)
    assert abs(got_ratio - expected_ratio) / expected_ratio < 0.02
    # Must not collapse to 16:9 box aspect (540/960)
    box_ratio_h = round((box_h / box_w) * w)
    assert h != box_ratio_h
    assert h > box_ratio_h


def test_capture_dimensions_web_uses_natural() -> None:
    w, h = capture_dimensions(
        natural_w=1440,
        natural_h=2210,
        box_w=1400,
        box_h=765,
        object_fit="contain",
        use_display_sizes=False,
    )
    ratio = aspect_ratio(w, h)
    expected = 1440 / 2210
    assert abs(ratio - expected) / expected < 0.02


def test_capture_dimensions_falls_back_to_natural() -> None:
    w, h = capture_dimensions(natural_w=1600, natural_h=900)
    assert w == 390
    assert h == round((900 / 1600) * 390)
    ratio_dev = abs(aspect_ratio(w, h) - (1600 / 900)) / (1600 / 900)
    assert ratio_dev < 0.02


def test_share_zip_filename() -> None:
    trip = {
        "tripId": "demo-kyoto",
        "meta": {"displayTitle": "京都雨季漫游", "title": "示例游记"},
    }
    assert share_zip_filename(trip) == "京都雨季漫游-分享.zip"
    assert "trip-" not in share_zip_filename(trip)


def test_has_share_zip_when_file_exists(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    assert not has_share_zip(trip, trip_workspace)
    zip_name = share_zip_filename(trip)
    (trip_workspace / zip_name).write_bytes(b"PK")
    assert has_share_zip(trip, trip_workspace)


def test_render_includes_share_toolbar(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False)
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert 'data-block="share-toolbar"' in html
    assert "share.js" in html
    assert "share-toggle" in html
    assert "longshot-save" in html
    assert "data-share-action=\"copy-link\"" in html
    assert (trip_workspace / "share.js").is_file()


def test_render_shows_download_zip_when_published(trip_workspace: Path) -> None:
    trip = json.loads((trip_workspace / "trip.json").read_text(encoding="utf-8"))
    (trip_workspace / share_zip_filename(trip)).write_bytes(b"PK")
    ctx = build_render_context(trip, trip_root=trip_workspace)
    assert ctx["hasShareZip"] is True
    assert ctx["shareZipFile"] == share_zip_filename(trip)
    assert "trip-" not in ctx["shareZipFile"]
    html = render_html(trip, trip_root=trip_workspace)
    assert "下载分享包" in html
    assert 'data-share-action="download-zip"' in html
