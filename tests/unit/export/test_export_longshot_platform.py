"""Longshot 2.0 platform export tests (AC-LNG2-01/02/11/12/13)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.boundary_metrics import BoundaryMetrics, parse_boundary_payload
from travelogue.export.content_splitter import BoundaryPoint, plan_moments_split
from travelogue.export.longshot import LongshotExportError, export_trip_longshot
from travelogue.export.platform_longshot import (
    PlatformExportWriter,
    auto_downgrade_scale,
    estimate_capture_memory_bytes,
    export_platform_longshot,
)
from travelogue.export.platform_profiles import (
    PHASE_C_CLI_ONLY,
    PlatformProfileError,
    file_prefix_for_platform,
    get_profile,
    is_single_file_output,
    output_canvas_size,
    resolve_profile,
    with_custom_output,
)
from travelogue.export.slide_postprocess import draw_page_footer

pytestmark = pytest.mark.unit


def test_profiles_load_moments_and_chat() -> None:
    from travelogue.export.platform_profiles import clear_platform_profiles_cache

    clear_platform_profiles_cache()
    chat = get_profile("wechat_chat")
    moments = get_profile("wechat_moments")
    assert chat.allow_p1 is True
    assert moments.allow_p1 is False
    assert moments.target_pages == 9
    assert moments.segment == "content_balanced"
    assert moments.min_pages == 1
    assert moments.is_photo_led is False
    assert moments.is_platform_segment is True


def test_profiles_load_phase_c() -> None:
    ins = get_profile("instagram")
    weibo = get_profile("weibo")
    douyin = get_profile("douyin_cover")
    custom = get_profile("custom")
    assert output_canvas_size(ins) == (1080, 1350)
    assert ins.max_pages == 10
    assert output_canvas_size(weibo) == (1080, 1440)
    assert weibo.max_pages == 9
    assert output_canvas_size(douyin) == (1080, 1920)
    assert is_single_file_output(douyin) is True
    assert douyin.max_pages == 1
    assert output_canvas_size(custom) == (1080, 1440)
    assert custom.max_pages == 18
    assert PHASE_C_CLI_ONLY == {"instagram", "weibo", "douyin_cover", "custom"}
    assert file_prefix_for_platform("林芝", "instagram").endswith("-ins")
    assert file_prefix_for_platform("林芝", "douyin_cover").endswith("-douyin-cover")


def test_with_custom_output_overrides_size() -> None:
    base = get_profile("custom")
    overridden = with_custom_output(base, width=800, height=1200)
    assert output_canvas_size(overridden) == (800, 1200)
    with pytest.raises(PlatformProfileError) as ei:
        with_custom_output(base, width=10, height=10)
    assert ei.value.code == "E_LNG2_INVALID_CUSTOM_SIZE"


def test_resolve_profile_rejects_unknown() -> None:
    with pytest.raises(PlatformProfileError) as ei:
        resolve_profile("not_a_platform")
    assert ei.value.code == "E_LNG2_INVALID_PLATFORM"


def test_resolve_profile_gray_list() -> None:
    with pytest.raises(PlatformProfileError):
        resolve_profile("xiaohongshu", allowed_platforms=["wechat_moments"])
    ok = resolve_profile(
        "xiaohongshu",
        allowed_platforms=["wechat_moments", "xiaohongshu"],
    )
    assert ok.id == "xiaohongshu"
    moments = resolve_profile("wechat_moments", allowed_platforms=["wechat_moments"])
    assert moments.id == "wechat_moments"
    # Phase C bypasses Studio allow-list (CLI/API only)
    ins = resolve_profile("instagram", allowed_platforms=["wechat_moments"])
    assert ins.id == "instagram"


def test_default_longshot2_platforms_include_xhs() -> None:
    from travelogue.config.studio import DEFAULT_LONGSHOT2_PLATFORMS, Longshot2Config
    from travelogue.export.platform_profiles import PHASE_A_PLATFORMS

    assert "wechat_moments" in DEFAULT_LONGSHOT2_PLATFORMS
    assert "xiaohongshu" in DEFAULT_LONGSHOT2_PLATFORMS
    assert PHASE_A_PLATFORMS == DEFAULT_LONGSHOT2_PLATFORMS
    assert Longshot2Config().platforms == DEFAULT_LONGSHOT2_PLATFORMS


def test_platform_export_writer_single_file(tmp_path: Path) -> None:
    writer = PlatformExportWriter(
        tmp_path, "demo-douyin-cover", ext="png", single_file=True
    )
    writer.write(1, b"a" * 100)
    assert (tmp_path / "demo-douyin-cover.png.part").is_file()
    finals = writer.commit()
    assert len(finals) == 1
    assert finals[0].name == "demo-douyin-cover.png"
    assert not (tmp_path / "demo-douyin-cover.png.part").exists()


def test_platform_export_writer_atomic_commit_and_rollback(tmp_path: Path) -> None:
    """AC-LNG2-11."""
    writer = PlatformExportWriter(tmp_path, "demo-moments", ext="png")
    writer.write(1, b"a" * 100)
    writer.write(2, b"b" * 100)
    assert (tmp_path / "demo-moments-01.png.part").is_file()
    finals = writer.commit()
    assert len(finals) == 2
    assert (tmp_path / "demo-moments-01.png").is_file()
    assert not (tmp_path / "demo-moments-01.png.part").exists()

    writer2 = PlatformExportWriter(tmp_path, "fail-moments", ext="png")
    writer2.write(1, b"c" * 100)
    writer2.rollback()
    assert not list(tmp_path.glob("fail-moments-*.part"))
    assert not list(tmp_path.glob("fail-moments-*.png"))


def test_platform_export_writer_context_rollback_on_error(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        with PlatformExportWriter(tmp_path, "boom-moments", ext="png") as w:
            w.write(1, b"x" * 50)
            raise RuntimeError("mid-write")
    assert not list(tmp_path.glob("boom-moments-*"))


def test_draw_page_footer_writes_label() -> None:
    """AC-LNG2-09."""
    img = Image.new("RGB", (428, 200), (240, 240, 240))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    out = draw_page_footer(raw, 2, 9, fmt="png")
    assert out != raw
    decoded = Image.open(BytesIO(out)).convert("RGB")
    band = decoded.crop((0, decoded.height - 48, decoded.width, decoded.height))
    changed = any(band.getpixel((x, y)) != (240, 240, 240) for y in range(band.height) for x in range(0, band.width, 8))
    assert changed


def test_export_platform_routes_no_p1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-LNG2-12: P0 failure must not call P1."""
    trip = tmp_path / "t"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"T"}}', encoding="utf-8")

    p1_called: list[bool] = []

    def _fail_p0(*_a, **_k):
        raise RuntimeError("p0 down")

    def _p1(*_a, **_k):
        p1_called.append(True)
        return b"x" * 2048, "p1"

    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_p0_with_metrics", _fail_p0
    )
    monkeypatch.setattr("travelogue.export.longshot._capture_p1", _p1)

    class _Page:
        def goto(self, *a, **k):
            return None

        def wait_for_function(self, *a, **k):
            return None

        def evaluate(self, *a, **k):
            return {"scrollHeight": 2000, "chapterCount": 1, "perChapter": [10]}

        def close(self):
            return None

    class _Browser:
        def new_page(self, **k):
            return _Page()

    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.acquire",
        lambda: _Browser(),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.release", lambda: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._resolve_longshot_url",
        lambda *a, **k: ("http://127.0.0.1:9/", None),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._apply_copy_display", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._page_metrics",
        lambda *_: {"scrollHeight": 2000, "chapterCount": 1, "perChapter": [10]},
    )

    with pytest.raises(LongshotExportError, match="E_LNG2_CAPTURE_P0_FAILED"):
        export_platform_longshot(trip, platform="wechat_moments", scale=1)
    assert p1_called == []
    assert not list(trip.glob("*-moments-*"))


def test_export_trip_longshot_routes_platform(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called: list[str] = []

    def _stub(*_a, **kwargs):
        called.append(kwargs.get("platform") or "")
        from travelogue.export.longshot import LongshotExportResult

        return LongshotExportResult(platform="wechat_moments", profile_label="朋友圈")

    monkeypatch.setattr(
        "travelogue.export.platform_longshot.export_platform_longshot", _stub
    )
    trip = tmp_path / "x"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("x", encoding="utf-8")
    export_trip_longshot(trip, platform="wechat_moments")
    assert called == ["wechat_moments"]


def test_moments_split_no_mid_cell_cuts() -> None:
    """AC-LNG2-02/13: content_balanced cuts only at photo edges."""
    from travelogue.export.content_splitter import breakpoints_cut_photo_interiors

    cells = [(float(i * 200), float(i * 200 + 180)) for i in range(12)]
    points = [BoundaryPoint(float(t), "photo") for t, _ in cells]
    plan = plan_moments_split(
        scroll_height_css=2400,
        boundaries_css=points,
        scale=1,
        photo_count=12,
        photo_cells=cells,
    )
    assert plan.method in ("dp", "greedy")
    assert plan.breakpoints[0] == 0 and plan.breakpoints[-1] == 2400
    cell_canvas = [(int(t), int(b)) for t, b in cells]
    assert breakpoints_cut_photo_interiors(plan.breakpoints, cell_canvas) == []


def test_parse_boundary_payload() -> None:
    m = parse_boundary_payload(
        {
            "scrollHeightCss": 1000,
            "boundariesCss": [0, 100, 1000],
            "boundaryKinds": ["start", "photo", "end"],
        }
    )
    assert m.scroll_height_css == 1000
    assert len(m.as_points()) == 1


def test_parse_boundary_payload_filters_junk_cells() -> None:
    from travelogue.export.boundary_metrics import parse_boundary_payload

    m = parse_boundary_payload(
        {
            "scrollHeightCss": 2000,
            "boundariesCss": [0, 2000],
            "boundaryKinds": ["start", "end"],
            "photoCells": [
                {"top": 0, "bottom": 400},
                {"top": 420, "bottom": 440},  # junk thin
                {"top": 500, "bottom": 900},
                {"top": 920, "bottom": 1300},
            ],
        }
    )
    assert all(c.bottom_css - c.top_css >= 72 for c in m.photo_cells)
    assert len(m.photo_cells) == 3


def test_auto_downgrade_scale_memory() -> None:
    # Huge scroll forces scale down
    huge = 200_000
    s = auto_downgrade_scale(huge, 3)
    assert s == 1
    assert estimate_capture_memory_bytes(1000, scale=2) > 0


def test_sparse_moments_hint_helpers_in_panel_source() -> None:
    """D-LNG2-17 · panel exports sparse hint helpers (FE contract)."""
    panel = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "longshot-export-panel.js"
    ).read_text(encoding="utf-8")
    assert "SPARSE_MOMENTS_PHOTO_THRESHOLD = 15" in panel
    assert "shouldHintSparseMoments" in panel
    assert "建议改用微信群长图" in panel


def test_export_xhs_pipeline_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-LNG2-03 · slideCount=6 → 6×1080×1440 PNG named *-xhs-*."""
    from io import BytesIO

    from PIL import Image

    from travelogue.export.boundary_metrics import BoundaryMetrics
    from travelogue.export.platform_longshot import export_platform_longshot

    trip = tmp_path / "xhs"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"XHS"}}', encoding="utf-8")

    # Tall canvas so 6 slices are feasible
    canvas = Image.new("RGB", (428, 6000), (180, 120, 80))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    canvas_bytes = buf.getvalue()

    class _Page:
        def goto(self, *a, **k):
            return None

        def wait_for_function(self, *a, **k):
            return None

        def close(self):
            return None

    class _Browser:
        def new_page(self, **k):
            return _Page()

    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.acquire",
        lambda: _Browser(),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.release", lambda: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._resolve_longshot_url",
        lambda *a, **k: ("http://127.0.0.1:9/", None),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._apply_copy_display", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._page_metrics",
        lambda *_: {"scrollHeight": 3000, "chapterCount": 1, "perChapter": [20]},
    )
    tops = list(range(0, 3001, 150))
    from travelogue.export.boundary_metrics import PhotoCell

    cells = [
        PhotoCell(float(y), float(min(y + 140, 3000)))
        for y in tops[:-1]
        if y + 140 <= 3000
    ]
    metrics = BoundaryMetrics(
        3000,
        [float(y) for y in tops],
        ["start"] + ["photo"] * (len(tops) - 2) + ["end"],
        photo_cells=cells,
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot.count_photos_heuristic",
        lambda *_: max(24, len(cells)),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_full_p0_only",
        lambda *a, **k: (canvas_bytes, metrics),
    )

    result = export_platform_longshot(
        trip,
        platform="xiaohongshu",
        scale=1,
        slide_count=6,
        pad_mode="letterbox",
        smart_crop_enabled=False,
    )
    assert result.platform == "xiaohongshu"
    assert result.page_count == 6
    assert len(result.outputs) == 6
    for item in result.outputs:
        assert "-xhs-" in item.path.name
        assert item.path.suffix == ".png"
        im = Image.open(item.path)
        assert im.size == (1080, 1440)
    assert "笔记正文" in (result.user_hint or "")
    assert result.publish_guide


def _mock_platform_capture(
    monkeypatch: pytest.MonkeyPatch, canvas_bytes: bytes, *, scroll_h: int = 3000
) -> None:
    class _Page:
        def goto(self, *a, **k):
            return None

        def wait_for_function(self, *a, **k):
            return None

        def close(self):
            return None

    class _Browser:
        def new_page(self, **k):
            return _Page()

    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.acquire",
        lambda: _Browser(),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.release", lambda: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._resolve_longshot_url",
        lambda *a, **k: ("http://127.0.0.1:9/", None),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._apply_copy_display", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._page_metrics",
        lambda *_: {
            "scrollHeight": scroll_h,
            "chapterCount": 1,
            "perChapter": [20],
        },
    )
    tops = list(range(0, scroll_h + 1, 150))
    from travelogue.export.boundary_metrics import PhotoCell

    cells = [
        PhotoCell(float(y), float(min(y + 140, scroll_h)))
        for y in tops[:-1]
        if y + 140 <= scroll_h
    ]
    metrics = BoundaryMetrics(
        float(scroll_h),
        [float(y) for y in tops],
        ["start"] + ["photo"] * (len(tops) - 2) + ["end"],
        photo_cells=cells,
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot.count_photos_heuristic",
        lambda *_: max(24, len(cells)),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_full_p0_only",
        lambda *a, **k: (canvas_bytes, metrics),
    )


def test_export_instagram_1080x1350(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip = tmp_path / "ins"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"Ins"}}', encoding="utf-8")
    canvas = Image.new("RGB", (428, 3000), (20, 40, 60))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    _mock_platform_capture(monkeypatch, buf.getvalue())

    result = export_platform_longshot(
        trip,
        platform="instagram",
        scale=1,
        slide_count=4,
        pad_mode="letterbox",
        smart_crop_enabled=False,
    )
    assert result.platform == "instagram"
    assert result.page_count == 4
    assert len(result.outputs) == 4
    for item in result.outputs:
        assert "-ins-" in item.path.name
        assert Image.open(item.path).size == (1080, 1350)


def test_export_douyin_cover_single_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip = tmp_path / "dy"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"Dy"}}', encoding="utf-8")
    canvas = Image.new("RGB", (428, 3000), (30, 50, 70))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    _mock_platform_capture(monkeypatch, buf.getvalue())

    result = export_platform_longshot(
        trip,
        platform="douyin_cover",
        scale=1,
        smart_crop_enabled=False,
    )
    assert result.platform == "douyin_cover"
    assert result.page_count == 1
    assert len(result.outputs) == 1
    out = result.outputs[0].path
    assert out.name.endswith("-douyin-cover.png")
    assert "-01" not in out.name
    assert Image.open(out).size == (1080, 1920)


def test_export_custom_canvas_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip = tmp_path / "cu"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"Cu"}}', encoding="utf-8")
    canvas = Image.new("RGB", (428, 3000), (40, 60, 80))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    _mock_platform_capture(monkeypatch, buf.getvalue())
    profile = with_custom_output(get_profile("custom"), width=720, height=960)

    result = export_platform_longshot(
        trip,
        platform="custom",
        scale=1,
        slide_count=3,
        pad_mode="letterbox",
        profile=profile,
        smart_crop_enabled=False,
    )
    assert result.platform == "custom"
    assert result.page_count == 3
    for item in result.outputs:
        assert "-custom-" in item.path.name
        assert Image.open(item.path).size == (720, 960)


def test_xhs_safe_area_warn_during_letterbox(caplog) -> None:
    """AC-LNG2-03s · letterbox tall slice triggers warn log (non-hard-fail)."""
    import logging

    from travelogue.export.slide_postprocess import fit_aspect_letterbox

    # Very tall → letterbox with side margins < SAFE_LEFT → warn
    img = Image.new("RGB", (200, 2000), (40, 80, 120))
    buf = BytesIO()
    img.save(buf, format="PNG")
    with caplog.at_level(logging.WARNING, logger="travelogue.export.slide_postprocess"):
        out, box = fit_aspect_letterbox(buf.getvalue())
    assert Image.open(BytesIO(out)).size == (1080, 1440)
    assert any("safe-area warn" in r.message for r in caplog.records)


def test_draw_page_footer_label_i_of_n_pixels() -> None:
    """AC-LNG2-09 · footer band differs from blank canvas (i/n orientation)."""
    img = Image.new("RGB", (1080, 1440), (250, 250, 250))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    out = draw_page_footer(raw, 3, 6, fmt="png")
    assert out != raw
    decoded = Image.open(BytesIO(out)).convert("RGB")
    band = decoded.crop((0, decoded.height - 64, decoded.width, decoded.height))
    blank = (250, 250, 250)
    changed = any(
        band.getpixel((x, y)) != blank
        for y in range(0, band.height, 4)
        for x in range(0, band.width, 16)
    )
    assert changed


def test_platform_slice_too_large_raises_after_retries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-LNG2-08 · slices stay >20MB → E_LNG2_SLICE_TOO_LARGE (no silent success)."""
    from travelogue.export.boundary_metrics import BoundaryMetrics
    from travelogue.export.platform_longshot import (
        MAX_WECHAT_SLICE_BYTES,
        export_platform_longshot,
    )

    trip = tmp_path / "huge"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"Huge"}}', encoding="utf-8")

    # Tiny real PNG; size check is mocked via slice_canvas_png
    canvas = Image.new("RGB", (428, 3000), (10, 10, 10))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    canvas_bytes = buf.getvalue()

    class _Page:
        def goto(self, *a, **k):
            return None

        def wait_for_function(self, *a, **k):
            return None

        def close(self):
            return None

    class _Browser:
        def new_page(self, **k):
            return _Page()

    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.acquire",
        lambda: _Browser(),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._BROWSER_POOL.release", lambda: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._resolve_longshot_url",
        lambda *a, **k: ("http://127.0.0.1:9/", None),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._apply_copy_display", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._page_metrics",
        lambda *_: {"scrollHeight": 3000, "chapterCount": 1, "perChapter": [20]},
    )
    tops = list(range(0, 3001, 500))
    from travelogue.export.boundary_metrics import PhotoCell

    cells = [
        PhotoCell(float(y), float(min(y + 400, 3000)))
        for y in tops[:-1]
        if y + 100 <= 3000
    ]
    metrics = BoundaryMetrics(
        3000,
        [float(y) for y in tops],
        ["start"] + ["photo"] * (len(tops) - 2) + ["end"],
        photo_cells=cells,
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot.count_photos_heuristic",
        lambda *_: max(24, len(cells)),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_full_p0_only",
        lambda *a, **k: (canvas_bytes, metrics),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot.slice_canvas_png",
        lambda *_a, **_k: b"x" * (MAX_WECHAT_SLICE_BYTES + 1),
    )

    with pytest.raises(LongshotExportError) as ei:
        export_platform_longshot(trip, platform="wechat_moments", scale=1)
    assert ei.value.code == "E_LNG2_SLICE_TOO_LARGE"
    assert not list(trip.glob("*-moments-*.png"))
    assert not list(trip.glob("*.part"))


def test_export_moments_missing_boundary_metrics_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stale longshot.js without boundaryMetrics must fail closed (not drift-cut)."""
    trip = tmp_path / "stale"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text('{"meta":{"title":"Stale"}}', encoding="utf-8")
    canvas = Image.new("RGB", (428, 800), (10, 10, 10))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    _mock_platform_capture(monkeypatch, buf.getvalue(), scroll_h=800)
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_full_p0_only",
        lambda *a, **k: (buf.getvalue(), None),
    )
    with pytest.raises(LongshotExportError) as ei:
        export_platform_longshot(trip, platform="wechat_moments", scale=1)
    assert ei.value.code == "E_LNG2_BOUNDARIES_MISSING"


def test_export_moments_contiguous_no_mid_cell_cut(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-LNG2-02 · content_balanced contiguous strips never cut mid-photo."""
    from PIL import ImageDraw

    from travelogue.export.boundary_metrics import PhotoCell
    from travelogue.export.content_splitter import breakpoints_cut_photo_interiors

    trip = tmp_path / "moments"
    trip.mkdir()
    (trip / "index-longshot.html").write_text("<html></html>", encoding="utf-8")
    (trip / "trip.json").write_text(
        '{"meta":{"title":"凯哥拍摄精选"}}', encoding="utf-8"
    )

    h = 1800
    canvas = Image.new("RGB", (428, h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    cells_css = [(i * 200, i * 200 + 180) for i in range(9)]
    colors = [(30 + i * 20, 80, 160 - i * 10) for i in range(9)]
    for (t, b), color in zip(cells_css, colors):
        draw.rectangle([0, t, 427, b - 1], fill=color)
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    canvas_bytes = buf.getvalue()

    tops_and_bottoms = [0.0]
    for t, b in cells_css:
        tops_and_bottoms.append(float(t))
        tops_and_bottoms.append(float(b))
    tops_and_bottoms.append(float(h))
    # dedupe preserve order
    bcss: list[float] = []
    for y in tops_and_bottoms:
        if not bcss or abs(y - bcss[-1]) > 0.5:
            bcss.append(y)
    kinds = ["start"] + ["photo"] * (len(bcss) - 2) + ["end"]
    metrics = BoundaryMetrics(
        float(h),
        bcss,
        kinds,
        photo_cells=[PhotoCell(float(t), float(b)) for t, b in cells_css],
    )
    _mock_platform_capture(monkeypatch, canvas_bytes, scroll_h=h)
    monkeypatch.setattr(
        "travelogue.export.platform_longshot._capture_full_p0_only",
        lambda *a, **k: (canvas_bytes, metrics),
    )
    monkeypatch.setattr(
        "travelogue.export.platform_longshot.count_photos_heuristic",
        lambda *_: 9,
    )

    result = export_platform_longshot(trip, platform="wechat_moments", scale=1)
    assert result.platform == "wechat_moments"
    assert 1 <= result.page_count <= 9
    assert len(result.outputs) == result.page_count
    # Reconstruct breakpoints from successive heights
    y = 0
    bps = [0]
    for item in result.outputs:
        im = Image.open(item.path)
        y += im.height
        bps.append(y)
    assert bps[-1] == h
    cell_canvas = [(t, b) for t, b in cells_css]
    assert breakpoints_cut_photo_interiors(bps, cell_canvas) == []
    for i, item in enumerate(result.outputs):
        assert f"-moments-{i + 1:02d}" in item.path.name
