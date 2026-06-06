"""Longshot export (Phase 2 M9)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.export.longshot import (
    CAPTURE_WIDTH,
    MAX_WECHAT_BYTES,
    LongshotExportError,
    _estimate_output_bytes,
    _segment_user_hint,
    _should_segment,
    _slug_title,
    apply_chapter_watermark,
    export_trip_longshot,
    reset_browser_pool_for_tests,
    reveal_path_in_folder,
    warm_playwright_browser,
)
from travelogue.paths import FIXTURES_DIR
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip

pytest.importorskip("playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture
def longshot_workspace(tmp_path: Path) -> Path:
    demo = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")
    ws = tmp_path / "longshot-export"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    assert (ws / LONGSHOT_INDEX_NAME).is_file()
    return ws


@pytest.fixture(autouse=True)
def _reset_pool() -> None:
    yield
    reset_browser_pool_for_tests()


def test_slug_title_strips_invalid_chars() -> None:
    assert _slug_title('bad<>:"/\\|?*name') == "badname"


def test_capture_width_is_428() -> None:
    assert CAPTURE_WIDTH == 428


def test_should_segment_by_height() -> None:
    assert _should_segment({"scrollHeight": 3000, "perChapter": [10]}, scale=2) is True
    assert _should_segment({"scrollHeight": 1000, "perChapter": [10]}, scale=1) is False


def test_should_segment_by_estimated_size() -> None:
    metrics = {"scrollHeight": 12000, "perChapter": [10]}
    assert _estimate_output_bytes(metrics, scale=2, fmt="png") > MAX_WECHAT_BYTES
    assert _should_segment(metrics, scale=2, fmt="png") is True


def test_segment_user_hint_size() -> None:
    hint = _segment_user_hint(5, "size")
    assert "5 张" in hint
    assert "20MB" in hint


def test_warm_playwright_browser_best_effort() -> None:
    assert warm_playwright_browser() is True


def test_should_segment_by_chapter_cards() -> None:
    assert _should_segment({"scrollHeight": 1000, "perChapter": [61]}, scale=1) is True


def test_apply_chapter_watermark_adds_label() -> None:
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (CAPTURE_WIDTH, 200), (240, 240, 240))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    out = apply_chapter_watermark(raw, page=2, total=5, fmt="png")
    assert out != raw
    decoded = Image.open(BytesIO(out)).convert("RGB")
    bottom_band = decoded.crop((0, decoded.height - 48, decoded.width, decoded.height))
    px = bottom_band.load()
    changed = False
    for y in range(bottom_band.height):
        for x in range(bottom_band.width):
            if px[x, y] != (240, 240, 240):
                changed = True
                break
        if changed:
            break
    assert changed


def test_apply_chapter_watermark_skips_single_page() -> None:
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), (10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    assert apply_chapter_watermark(raw, page=1, total=1, fmt="png") == raw


def test_export_longshot_single_file(longshot_workspace: Path) -> None:
    result = export_trip_longshot(longshot_workspace, scale=1)
    assert result.outputs
    for item in result.outputs:
        assert item.path.is_file()
        assert item.path.stat().st_size > 1024
    names = [item.path.name for item in result.outputs]
    assert any(n.endswith("-longshot.png") or "-ch" in n for n in names)


def test_export_longshot_missing_html(tmp_path: Path) -> None:
    trip_dir = tmp_path / "empty"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text('{"meta":{"title":"x"}}', encoding="utf-8")
    with pytest.raises(LongshotExportError, match="E_LNG_NO_LONGSHOT"):
        export_trip_longshot(trip_dir)


def test_reveal_path_denied_outside_trips(tmp_path: Path) -> None:
    allowed = tmp_path / "trips"
    allowed.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    with pytest.raises(LongshotExportError, match="E_STUDIO_REVEAL_DENIED"):
        reveal_path_in_folder(outside, allowed_root=allowed)


def test_reveal_path_allows_inside_trips(tmp_path: Path) -> None:
    allowed = tmp_path / "trips"
    trip = allowed / "demo"
    trip.mkdir(parents=True)
    target = trip / "demo-longshot.png"
    target.write_bytes(b"png")
    reveal_path_in_folder(target, allowed_root=allowed)


def test_export_longshot_closes_page_when_goto_fails(
    longshot_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: page must close on navigation failure (no pool leak)."""
    closed: list[bool] = []

    class _FakePage:
        viewport_size = {"width": CAPTURE_WIDTH, "height": 844}

        def goto(self, *args: object, **kwargs: object) -> None:
            raise TimeoutError("navigation timeout")

        def close(self) -> None:
            closed.append(True)

        def wait_for_function(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("wait_for_function should not run after failed goto")

    class _FakeBrowser:
        def new_page(self, **kwargs: object) -> _FakePage:
            return _FakePage()

    monkeypatch.setattr(
        "travelogue.export.longshot._BROWSER_POOL.acquire",
        lambda: _FakeBrowser(),
    )
    monkeypatch.setattr("travelogue.export.longshot._BROWSER_POOL.release", lambda: None)

    with pytest.raises(TimeoutError, match="navigation timeout"):
        export_trip_longshot(longshot_workspace, base_url="http://127.0.0.1:9/")

    assert closed == [True]
