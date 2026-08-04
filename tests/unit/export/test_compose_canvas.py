"""Unit tests · compose_canvas fixed collage."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.compose_canvas import (
    A4_CANVAS,
    XHS_CANVAS,
    compose_fixed_canvas,
    pack_photo_pages,
)

pytestmark = pytest.mark.unit


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def test_compose_fixed_canvas_a4(tmp_path: Path) -> None:
    paths = []
    for i in range(3):
        p = tmp_path / f"a{i}.jpg"
        _make_rgb(p, size=(800, 600) if i % 2 == 0 else (500, 900))
        paths.append(p)
    data, diag = compose_fixed_canvas(paths, canvas_wh=A4_CANVAS)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(__import__("io").BytesIO(data)) as im:
        assert im.size == A4_CANVAS
    assert diag["canvas"] == list(A4_CANVAS)
    assert diag["n"] == 3
    assert "naturalCanvas" in diag
    assert "scale" in diag


def test_compose_fixed_canvas_cover_fills_frame(tmp_path: Path) -> None:
    """短拼贴不得 letterbox 留大块底色；cover 后画布应被铺满。"""
    paths = []
    colors = [(220, 40, 40), (40, 220, 40), (40, 40, 220)]
    for i, color in enumerate(colors):
        p = tmp_path / f"c{i}.jpg"
        # Wide landscape → bric natural height << A4 → old contain left huge bands
        _make_rgb(p, size=(1200, 400), color=color)
        paths.append(p)
    data, diag = compose_fixed_canvas(
        paths, canvas_wh=A4_CANVAS, border=0, spacing=0
    )
    assert diag.get("fit") == "cover"
    assert diag.get("cellFit") == "cover"
    assert float(diag["scale"]) >= 1.0
    with Image.open(__import__("io").BytesIO(data)) as im:
        assert im.size == A4_CANVAS
        # Sample mid-edge bands that used to be empty letterbox; must not be canvas bg
        bg = (245, 245, 243)
        samples = [
            im.getpixel((A4_CANVAS[0] // 2, A4_CANVAS[1] // 8)),
            im.getpixel((A4_CANVAS[0] // 2, A4_CANVAS[1] // 2)),
            im.getpixel((A4_CANVAS[0] // 2, 7 * A4_CANVAS[1] // 8)),
        ]
        assert all(px != bg for px in samples)


def test_pack_photo_pages_basic_chunking() -> None:
    paths = [Path(f"p{i}.jpg") for i in range(8)]
    pages = pack_photo_pages(paths, per_page=3, max_pages=9)
    assert [len(p) for p in pages] == [3, 3, 2]
    assert pages[0][0].name == "p0.jpg"
    assert pages[-1][-1].name == "p7.jpg"


def test_pack_photo_pages_avoid_singleton() -> None:
    paths = [Path(f"p{i}.jpg") for i in range(7)]
    pages = pack_photo_pages(paths, per_page=3, max_pages=9)
    # 3+3+1 → steal → 3+2+2
    assert [len(p) for p in pages] == [3, 2, 2]


def test_pack_photo_pages_empty() -> None:
    assert pack_photo_pages([], per_page=4, max_pages=9) == []
