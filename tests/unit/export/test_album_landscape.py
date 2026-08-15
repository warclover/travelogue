"""ALS W1 · screen-capture kernel (no live browser required)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.album_landscape import (
    CAPTURE_CSS,
    OUTPUT_H,
    OUTPUT_W,
    PAGE_BG_RGB,
    PREPARE_PAGE_JS,
    collect_page_blocks_from_html,
    png_is_flat_white,
    compose_viewport_box,
    export_album_landscape,
    letterbox_to_landscape,
    place_clip_on_landscape,
    resolve_preview_index_url,
    viewport_intersection,
)
from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotCancelled,
    LongshotExportError,
)
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

FIXTURE_HTML = """<!doctype html>
<html data-layout="web">
<body>
  <header class="preview-toolbar" data-preview-toolbar="on">Studio</header>
  <main>
    <section data-block="cover-opening">Opening</section>
    <div data-block="breath-pause-screen" class="breath-pause-screen">···</div>
    <section data-block="chapter-separator">章</section>
    <section data-block="layout-screen" class="layout-screen">屏1</section>
    <section data-block="moment-screen" class="layout-screen" data-block-extra="x">漏收</section>
    <section class="layout-screen" data-block="layout-screen">屏2 mosaic</section>
    <div data-block="breath-pause-card">缝</div>
    <section data-block="cover-closing">Closing</section>
  </main>
</body>
</html>
"""

# moment-screen without layout-screen data-block should not count;
# the fixture above has one bogus moment-screen that also has data-block=moment-screen
# wait - I set data-block="moment-screen" on one section. That should NOT be collected.
# And two layout-screens. Total: opening + separator + 2 layout + closing = 5.


def _png_bytes(size: tuple[int, int], color: tuple[int, int, int] = (80, 120, 160)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _seed_screens_trip(trips: Path, trip_id: str, html: str) -> Path:
    create_trip(trip_id, trips, title="横版测试")
    trip_dir = trips / trip_id
    trip_json = trip_dir / "trip.json"
    text = trip_json.read_text(encoding="utf-8")
    import json

    data = json.loads(text)
    data["layoutEngine"] = "screens"
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (trip_dir / "index.html").write_text(html, encoding="utf-8")
    return trip_dir


def test_capture_css_forces_breath_reveal_visible() -> None:
    """data-breath=off 会丢掉 cinematic 的 opacity:1 覆盖，必须强制揭开。"""
    assert ".breath-reveal" in CAPTURE_CSS
    assert "opacity: 1 !important" in CAPTURE_CSS
    assert "is-visible" in PREPARE_PAGE_JS
    assert "TravelogueBreath" in PREPARE_PAGE_JS


def test_png_is_flat_white_detects_blank_board() -> None:
    assert png_is_flat_white(_png_bytes((64, 36), (255, 255, 255))) is True
    assert png_is_flat_white(_png_bytes((64, 36), (80, 120, 160))) is False
    assert png_is_flat_white(_png_bytes((64, 36), PAGE_BG_RGB)) is False


def test_screenshot_prefers_cdp_over_playwright(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Playwright page.screenshot waits on fonts; CDP must win when available."""
    from travelogue.export.album_landscape import _screenshot_viewport

    class _Cdp:
        def send(self, _method: str, _params: dict) -> dict:
            import base64

            return {"data": base64.b64encode(_png_bytes((64, 36), (10, 20, 30))).decode()}

    class _Ctx:
        def new_cdp_session(self, _page: object) -> _Cdp:
            return _Cdp()

    class _Page:
        context = _Ctx()

        def screenshot(self, **_k) -> bytes:
            raise TimeoutError("fonts")

    raw = _screenshot_viewport(_Page())
    assert png_is_flat_white(raw) is False


def test_capture_css_does_not_hide_html_preview_toolbar_flag() -> None:
    """html[data-preview-toolbar=on] 是开关，不是工具条；误藏 html 会截出纯白。"""
    assert "[data-preview-toolbar]:not(html):not(body)" in CAPTURE_CSS
    assert "el === document.documentElement" in PREPARE_PAGE_JS


def test_collect_page_blocks_skips_breath_and_duplicate_moment() -> None:
    blocks = collect_page_blocks_from_html(FIXTURE_HTML)
    assert blocks == [
        "cover-opening",
        "chapter-separator",
        "layout-screen",
        "layout-screen",
        "cover-closing",
    ]
    assert "breath-pause-screen" not in blocks
    assert "moment-screen" not in blocks


def test_collect_empty_main_is_zero() -> None:
    html = "<html><body><main></main><section data-block='layout-screen'>out</section></body></html>"
    assert collect_page_blocks_from_html(html) == []


def test_letterbox_to_landscape_size() -> None:
    raw = _png_bytes((100, 50), (10, 20, 30))
    out = letterbox_to_landscape(raw, bg=PAGE_BG_RGB)
    img = Image.open(BytesIO(out))
    assert img.size == (OUTPUT_W, OUTPUT_H)
    # corners stay paper color (contain-fit of a wide strip)
    assert img.getpixel((0, 0)) == PAGE_BG_RGB


def test_page_screenshot_clip_must_use_document_coords() -> None:
    """Regression · 视口 (0,0) 当 page.screenshot clip 会裁出视口外纯白。"""
    scrolled = {"x": 0, "y": 0, "width": 1920, "height": 1080, "pageX": 0, "pageY": 5400}
    vis = viewport_intersection(scrolled)
    assert vis is not None
    assert vis["origin"] == (0.0, 0.0)
    # 文档坐标必须带 scrollY，不能把 origin 当 clip
    assert scrolled["pageY"] != vis["origin"][1]


def test_viewport_intersection_clips_tall_flow() -> None:
    info = viewport_intersection({"x": 0, "y": 0, "width": 1920, "height": 4000})
    assert info is not None
    assert info["clip"]["height"] == 1080
    assert info["clip"]["width"] == 1920
    assert info["origin"] == (0.0, 0.0)


def test_place_clip_on_landscape_keeps_3840x2160() -> None:
    raw = _png_bytes((3840, 400))
    out = place_clip_on_landscape(raw, (0.0, 0.0), bg=PAGE_BG_RGB)
    img = Image.open(BytesIO(out))
    assert img.size == (OUTPUT_W, OUTPUT_H)
    assert img.getpixel((10, 10)) != PAGE_BG_RGB
    assert img.getpixel((10, 2000)) == PAGE_BG_RGB


def test_compose_viewport_box_does_not_squash_tall_flow() -> None:
    # 1920×4000 CSS → 3840×8000 px screenshot; visible top 1920×1080
    raw = _png_bytes((3840, 8000), (200, 40, 40))
    out = compose_viewport_box(
        raw,
        {"x": 0, "y": 0, "width": 1920, "height": 4000},
        bg=PAGE_BG_RGB,
    )
    img = Image.open(BytesIO(out))
    assert img.size == (OUTPUT_W, OUTPUT_H)
    assert img.getpixel((10, 10)) == (200, 40, 40)


def test_resolve_preview_index_url_never_longshot() -> None:
    url, server = resolve_preview_index_url(
        Path("/tmp/demo"),
        base_url="http://127.0.0.1:8766",
        trip_id="demo-1",
    )
    assert server is None
    assert url.endswith("/demo-1/index.html")
    assert "index-longshot.html" not in url
    assert not url.startswith("file:")


class _FakeNode:
    def __init__(self, block: str, png: bytes, *, fail: bool = False) -> None:
        self._block = block
        self._png = png
        self._fail = fail

    def get_attribute(self, name: str) -> str | None:
        return self._block if name == "data-block" else None

    def scroll_into_view_if_needed(self, **_k) -> None:
        return None

    def evaluate(self, _js, **_k):
        if "getBoundingClientRect" in str(_js) or "width" in str(_js):
            h = 1080 if self._block == "layout-screen" else 200
            return {"x": 0, "y": 0, "width": 1920, "height": h}
        return True

    def screenshot(self, **_k) -> bytes:
        if self._fail:
            raise RuntimeError("boom")
        return self._png

    def locator(self, _sel: str) -> _FakeLocator:
        return _FakeLocator([])


class _FakeLocator:
    def __init__(
        self, nodes: list[_FakeNode], *, child_nodes: list[_FakeNode] | None = None
    ) -> None:
        self._nodes = nodes
        self._child_nodes = child_nodes if child_nodes is not None else nodes

    def count(self) -> int:
        return len(self._nodes)

    def nth(self, i: int) -> _FakeNode:
        return self._nodes[i]

    def locator(self, sel: str) -> _FakeLocator:
        if "data-block" in sel:
            return _FakeLocator(self._child_nodes)
        return _FakeLocator(self._nodes)


class _FakePage:
    def __init__(
        self,
        nodes: list[_FakeNode],
        *,
        shot_error: BaseException | None = None,
    ) -> None:
        self.goto_urls: list[str] = []
        self._nodes = nodes
        self.closed = False
        self._shot_error = shot_error

    def goto(self, url: str, **_k) -> None:
        self.goto_urls.append(url)

    def wait_for_selector(self, _sel: str, **_k) -> None:
        return None

    def add_style_tag(self, **_k) -> None:
        return None

    def evaluate(self, _js, **_k):
        return "#f5f2ea"

    def screenshot(self, **_k) -> bytes:
        if self._shot_error is not None:
            raise self._shot_error
        return _png_bytes((3840, 2160))

    def locator(self, sel: str) -> _FakeLocator:
        if sel in ("main", "body"):
            return _FakeLocator(
                [_FakeNode(sel, b"x")],
                child_nodes=self._nodes,
            )
        return _FakeLocator(self._nodes)

    def close(self) -> None:
        self.closed = True


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    def new_page(self, **_k) -> _FakePage:
        return self.page


def _install_fake_browser(
    monkeypatch: pytest.MonkeyPatch, page: _FakePage, released: list[str]
) -> None:
    monkeypatch.setattr(
        "travelogue.export.album_landscape.acquire_browser",
        lambda: _FakeBrowser(page),
    )
    monkeypatch.setattr(
        "travelogue.export.album_landscape.release_browser",
        lambda: released.append("release"),
    )


def test_export_goto_index_html_not_longshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-goto", FIXTURE_HTML)
    blocks = collect_page_blocks_from_html(FIXTURE_HTML)
    nodes = [
        _FakeNode(b, _png_bytes((3840, 2160) if b == "layout-screen" else (3840, 400)))
        for b in blocks
    ]
    page = _FakePage(nodes)
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)

    result = export_album_landscape(
        trip_dir,
        base_url="http://127.0.0.1:8766",
        trip_id="als-goto",
        slide_count=8,
    )
    assert page.goto_urls
    assert page.goto_urls[0].endswith("/als-goto/index.html")
    assert "index-longshot.html" not in page.goto_urls[0]
    assert result.page_count == len(blocks)
    assert result.page_count != 8
    assert all("-landscape-" in p.path.name for p in result.outputs)
    assert "画册" not in result.user_hint
    assert "跨页" not in result.user_hint
    assert "16:9" in result.user_hint
    assert "与预览同屏" in result.user_hint
    assert "可预览或送印" in result.user_hint
    assert "套 A4 请留白" in result.user_hint
    assert released == ["release"]
    for item in result.outputs:
        img = Image.open(item.path)
        assert img.size == (OUTPUT_W, OUTPUT_H)


def test_empty_main_no_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><body><main></main></body></html>"
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-empty", html)
    page = _FakePage([])
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    with pytest.raises(LongshotExportError, match="E_ALS_NO_PAGES"):
        export_album_landscape(trip_dir, base_url="http://127.0.0.1:9", trip_id="als-empty")
    assert released == ["release"]
    assert not (trip_dir / EXPORT_OUTPUT_DIRNAME).exists() or not list(
        (trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-landscape-*")
    )


def test_capture_failure_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-fail", FIXTURE_HTML)
    nodes = [_FakeNode("layout-screen", _png_bytes((3840, 2160)))]
    page = _FakePage(nodes, shot_error=RuntimeError("boom"))
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    with pytest.raises(LongshotExportError, match="E_ALS_CAPTURE_FAILED"):
        export_album_landscape(trip_dir, base_url="http://127.0.0.1:9", trip_id="als-fail")
    assert released == ["release"]


def test_no_index_does_not_acquire(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trips = tmp_path / "trips"
    create_trip("als-noindex", trips, title="noindex")
    trip_dir = trips / "als-noindex"
    import json

    data = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    data["layoutEngine"] = "screens"
    (trip_dir / "trip.json").write_text(json.dumps(data), encoding="utf-8")
    acquired: list[str] = []
    monkeypatch.setattr(
        "travelogue.export.album_landscape.acquire_browser",
        lambda: acquired.append("acquire") or (_ for _ in ()).throw(AssertionError("no")),
    )
    with pytest.raises(LongshotExportError, match="E_ALS_NO_INDEX"):
        export_album_landscape(trip_dir)
    assert acquired == []
    assert not list(trip_dir.glob("**/*-landscape-*"))


def test_not_screens_engine(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("als-legacy", trips, title="legacy")
    trip_dir = trips / "als-legacy"
    (trip_dir / "index.html").write_text(FIXTURE_HTML, encoding="utf-8")
    with pytest.raises(LongshotExportError, match="E_ALS_NOT_SCREENS"):
        export_album_landscape(trip_dir)


def test_job_timeout_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-timeout", FIXTURE_HTML)
    nodes = [_FakeNode("layout-screen", _png_bytes((3840, 2160)))]
    page = _FakePage(nodes)
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    monkeypatch.setattr("travelogue.export.album_landscape.JOB_TIMEOUT_SEC", -1)
    with pytest.raises(LongshotExportError, match="E_ALS_TIMEOUT"):
        export_album_landscape(
            trip_dir, base_url="http://127.0.0.1:9", trip_id="als-timeout"
        )
    assert released == ["release"]


def test_screen_timeout_maps_to_e_als_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-screen-to", FIXTURE_HTML)

    page = _FakePage(
        [_FakeNode("layout-screen", _png_bytes((3840, 2160)))],
        shot_error=TimeoutError("Timeout 20000ms exceeded"),
    )
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    with pytest.raises(LongshotExportError, match="E_ALS_TIMEOUT"):
        export_album_landscape(
            trip_dir, base_url="http://127.0.0.1:9", trip_id="als-screen-to"
        )
    assert released == ["release"]


def test_cancel_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-cancel", FIXTURE_HTML)
    nodes = [_FakeNode("layout-screen", _png_bytes((3840, 2160)))]
    page = _FakePage(nodes)
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    checks = {"n": 0}

    def _cancel_after_acquire() -> bool:
        checks["n"] += 1
        return checks["n"] > 1

    with pytest.raises(LongshotCancelled):
        export_album_landscape(
            trip_dir,
            base_url="http://127.0.0.1:9",
            trip_id="als-cancel",
            cancel_check=_cancel_after_acquire,
        )
    assert released == ["release"]


def test_after_als_fail_wechat_chat_still_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-ALS-11 · ALS 失败 release 后，微信群长图仍能走进默认分支。"""
    from travelogue.export.longshot import LongshotExportResult, export_trip_longshot

    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-then-chat", FIXTURE_HTML)
    nodes = [_FakeNode("layout-screen", _png_bytes((3840, 2160)))]
    page = _FakePage(nodes, shot_error=RuntimeError("boom"))
    released: list[str] = []
    _install_fake_browser(monkeypatch, page, released)
    with pytest.raises(LongshotExportError, match="E_ALS_CAPTURE_FAILED"):
        export_album_landscape(
            trip_dir, base_url="http://127.0.0.1:9", trip_id="als-then-chat"
        )
    assert released == ["release"]

    (trip_dir / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    wechat_held = {"n": 0}

    class _WechatBrowser:
        def new_page(self, **_k):
            raise LongshotExportError("E_LNG_CAPTURE_FAILED", "wechat stub reached")

    def _acquire() -> _WechatBrowser:
        wechat_held["n"] += 1
        return _WechatBrowser()

    def _release() -> None:
        wechat_held["n"] -= 1

    import travelogue.export.longshot as longshot_mod

    monkeypatch.setattr(longshot_mod._BROWSER_POOL, "acquire", _acquire)
    monkeypatch.setattr(longshot_mod._BROWSER_POOL, "release", _release)
    monkeypatch.setattr(longshot_mod._BROWSER_POOL, "needs_cold_start", lambda: False)

    with pytest.raises(LongshotExportError, match="E_LNG_CAPTURE_FAILED") as exc:
        export_trip_longshot(trip_dir, platform="wechat_chat")
    assert exc.value.code == "E_LNG_CAPTURE_FAILED"
    assert "E_ALS_" not in exc.value.code
    assert wechat_held["n"] == 0
