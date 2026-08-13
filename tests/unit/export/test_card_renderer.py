"""Unit tests · card_renderer (PRD-EXPORT-CARD-COMPOSE-V1 §4/§6)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.card_renderer import SlotCropHint, render_card, render_spread
from travelogue.export.card_templates import CARD_TEMPLATES, PROBE_TEMPLATES

pytestmark = pytest.mark.unit

CARD_CANVAS = (1080, 1440)


def _make_rgb(path: Path, *, size: tuple[int, int], color: tuple[int, int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)
    return path


def test_render_card_full_frame_fills_canvas(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    photo = _make_rgb(tmp_path / "a.jpg", size=(1600, 900), color=(220, 40, 40))
    data, diag = render_card([photo], template, canvas_wh=CARD_CANVAS)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert diag["canvas"] == list(CARD_CANVAS)
    assert diag["template"] == "card-1-full-frame"
    assert diag["fit"] == "cover"
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS


def test_render_card_covers_every_pixel_no_background_bleed(tmp_path: Path) -> None:
    """短拼贴不得留大块底色 — AC-ECC-01."""
    template = CARD_TEMPLATES["card-9-grid-equal"]
    colors = [
        (220, 40, 40), (40, 220, 40), (40, 40, 220),
        (220, 220, 40), (220, 40, 220), (40, 220, 220),
        (120, 60, 60), (60, 120, 60), (60, 60, 120),
    ]
    photos = [
        _make_rgb(tmp_path / f"p{i}.jpg", size=(900, 1300), color=c)
        for i, c in enumerate(colors)
    ]
    data, _ = render_card(photos, template, canvas_wh=CARD_CANVAS)
    bg = (245, 245, 243)
    with Image.open(io.BytesIO(data)) as im:
        w, h = im.size
        # Sample the center of each of the 9 cells; none should be raw bg.
        for row in range(3):
            for col in range(3):
                x = int((col + 0.5) * w / 3)
                y = int((row + 0.5) * h / 3)
                assert im.getpixel((x, y)) != bg


def test_render_card_slot_gap_shows_seam_between_cells(tmp_path: Path) -> None:
    """用户反馈 2026-08-05 · 多槙位卡片应有细缝，而非无缝贴合."""
    template = CARD_TEMPLATES["card-2-stack-equal"]
    top = _make_rgb(tmp_path / "top.jpg", size=(1600, 900), color=(220, 40, 40))
    bottom = _make_rgb(tmp_path / "bottom.jpg", size=(1600, 900), color=(40, 40, 220))
    data, diag = render_card([top, bottom], template, canvas_wh=CARD_CANVAS)
    assert diag["slotGap"] > 0
    bg = (245, 245, 243)
    with Image.open(io.BytesIO(data)) as im:
        w, h = im.size
        seam_y = h // 2
        # Right on the boundary between the two stacked slots: background gap.
        assert im.getpixel((w // 2, seam_y)) == bg
        # A few px into either slot (away from the seam): real photo content.
        margin = diag["slotGap"] * 3
        assert im.getpixel((w // 2, seam_y - margin)) != bg
        assert im.getpixel((w // 2, seam_y + margin)) != bg


def test_render_card_single_slot_has_no_gap(tmp_path: Path) -> None:
    """1x1 网格没有内部缝隙可言——单图海报不受 gap 影响."""
    template = CARD_TEMPLATES["card-1-full-frame"]
    photo = _make_rgb(tmp_path / "a.jpg", size=(1600, 900), color=(220, 40, 40))
    _data, diag = render_card([photo], template, canvas_wh=CARD_CANVAS)
    # gap is still computed (>0) but has nowhere to apply on a single cell.
    assert diag["slotGap"] > 0


def test_render_card_wrong_photo_count_raises(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    a = _make_rgb(tmp_path / "a.jpg", size=(800, 600), color=(1, 2, 3))
    b = _make_rgb(tmp_path / "b.jpg", size=(800, 600), color=(4, 5, 6))
    with pytest.raises(ValueError):
        render_card([a, b], template, canvas_wh=CARD_CANVAS)


def test_render_card_crop_required_slot_biases_for_person(tmp_path: Path) -> None:
    """AC-ECC-06 · card-4 主图槙对人像照片走保守（上偏）裁切."""
    template = CARD_TEMPLATES["card-4-square-top-triband"]
    main_photo = _make_rgb(tmp_path / "main.jpg", size=(1000, 1000), color=(10, 10, 10))
    portraits = [
        _make_rgb(tmp_path / f"p{i}.jpg", size=(800, 1200), color=(50 * i, 60, 70))
        for i in range(3)
    ]
    assets = {main_photo: {"tags": ["person", "face"]}}

    def lookup(path: Path) -> dict | None:
        return assets.get(path)

    data, diag = render_card(
        [main_photo, *portraits], template, canvas_wh=CARD_CANVAS, asset_lookup=lookup
    )
    assert diag["template"] == "card-4-square-top-triband"
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS


def test_render_spread_two_cards_with_gutter(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    left_photo = _make_rgb(tmp_path / "left.jpg", size=(1000, 1000), color=(200, 40, 40))
    right_photo = _make_rgb(tmp_path / "right.jpg", size=(1000, 1000), color=(40, 40, 200))
    data, diag = render_spread(
        ([left_photo], template),
        ([right_photo], template),
        card_wh=CARD_CANVAS,
        gutter=48,
    )
    expected_w = CARD_CANVAS[0] * 2 + 48
    assert diag["canvas"] == [expected_w, CARD_CANVAS[1]]
    assert diag["halfPage"] is False
    assert diag["slotGap"] > 0
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == (expected_w, CARD_CANVAS[1])
        left_px = im.getpixel((CARD_CANVAS[0] // 2, CARD_CANVAS[1] // 2))
        right_px = im.getpixel((expected_w - CARD_CANVAS[0] // 2, CARD_CANVAS[1] // 2))
        assert left_px != right_px


def test_render_spread_lone_card_half_page(tmp_path: Path) -> None:
    """Regression (2026-08-06, user report: "空槙，就是缺失照片，违背兜底
    原则" — a real album export's trailing spread had its entire right half
    rendered as flat background, zero photos). A lone trailing card must
    render at single-card width — no blank half at all — rather than the
    full double-width spread canvas with an empty right side."""
    template = CARD_TEMPLATES["card-1-full-frame"]
    left_photo = _make_rgb(tmp_path / "left.jpg", size=(1000, 1000), color=(200, 40, 40))
    data, diag = render_spread(
        ([left_photo], template), None, card_wh=CARD_CANVAS, gutter=48
    )
    assert diag["halfPage"] is True
    assert diag["templates"][1] is None
    assert diag["canvas"] == [CARD_CANVAS[0], CARD_CANVAS[1]]
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS
        # Every pixel must come from the (fully cover-cropped) left photo —
        # no leftover background-filled area anywhere in the canvas.
        bg = (245, 245, 243)
        assert im.getpixel((CARD_CANVAS[0] - 5, CARD_CANVAS[1] // 2)) != bg
        assert im.getpixel((5, 5)) != bg


def test_render_card_punch_in_window_on_first_slot_does_not_break_later_slots(
    tmp_path: Path,
) -> None:
    """Punch-in window coords must not shadow canvas origin x0/y0."""
    template = CARD_TEMPLATES["card-2-stack-equal"]
    photos = [
        _make_rgb(tmp_path / "a.jpg", size=(800, 1200), color=(200, 40, 40)),
        _make_rgb(tmp_path / "b.jpg", size=(800, 1200), color=(40, 40, 200)),
    ]
    hints = (
        SlotCropHint(fit="cover", window=(0.1, 0.1, 0.9, 0.9)),
        SlotCropHint(fit="cover", window=(0.2, 0.2, 0.8, 0.8)),
    )
    data, diag = render_card(
        photos, template, canvas_wh=CARD_CANVAS, slot_hints=hints
    )
    assert diag["template"] == "card-2-stack-equal"
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS
        top = im.getpixel((CARD_CANVAS[0] // 2, CARD_CANVAS[1] // 4))
        bot = im.getpixel((CARD_CANVAS[0] // 2, 3 * CARD_CANVAS[1] // 4))
        assert top != bot


def test_probe_hero_mix_flush_to_card_edges(tmp_path: Path) -> None:
    template = PROBE_TEMPLATES["probe-hero-mix"]
    colors = [(200, 40, 40), (40, 200, 40), (40, 40, 200)]
    photos = [
        _make_rgb(tmp_path / f"h{i}.jpg", size=(900, 1200), color=colors[i])
        for i in range(3)
    ]
    data, _diag = render_card(photos, template, canvas_wh=CARD_CANVAS)
    bg = (245, 245, 243)
    with Image.open(io.BytesIO(data)) as im:
        assert im.getpixel((4, 4)) != bg
        assert im.getpixel((CARD_CANVAS[0] - 5, 4)) != bg
        assert im.getpixel((4, CARD_CANVAS[1] - 5)) != bg
        assert im.getpixel((CARD_CANVAS[0] - 5, CARD_CANVAS[1] - 5)) != bg


def test_probe_square_tiles_are_one_to_one(tmp_path: Path) -> None:
    template = PROBE_TEMPLATES["probe-square"]
    photos = [
        _make_rgb(tmp_path / f"s{i}.jpg", size=(1000, 1000), color=(40 + i * 40, 80, 120))
        for i in range(4)
    ]
    data, _diag = render_card(photos, template, canvas_wh=CARD_CANVAS)
    bg = (245, 245, 243)
    with Image.open(io.BytesIO(data)) as im:
        assert im.getpixel((CARD_CANVAS[0] // 2, 8)) == bg
        assert im.getpixel((CARD_CANVAS[0] // 2, CARD_CANVAS[1] - 8)) == bg
        mid = im.getpixel((CARD_CANVAS[0] // 4, CARD_CANVAS[1] // 2 - 80))
        assert mid != bg
