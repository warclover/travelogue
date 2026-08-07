"""Unit tests · album export bookends (PRD-ALBUM-EXPORT-BOOKENDS-V1)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.card_bookends import render_closing_card, render_cover_card
from travelogue.export.card_renderer import CARD_CANVAS

pytestmark = pytest.mark.unit


def _rgb(path: Path, *, size: tuple[int, int] = (800, 1200), color=(40, 100, 160)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def test_render_cover_card_with_title_and_subtitle(tmp_path: Path) -> None:
    photo = tmp_path / "cover.jpg"
    _rgb(photo)
    data = render_cover_card(
        photo,
        title="天山南麓",
        subtitle="十一天 · 慢行",
        canvas_wh=CARD_CANVAS,
    )
    assert data is not None
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS
        assert im.mode == "RGB"


def test_render_cover_card_without_subtitle(tmp_path: Path) -> None:
    photo = tmp_path / "cover.jpg"
    _rgb(photo)
    data = render_cover_card(
        photo, title="只有标题", subtitle="", canvas_wh=CARD_CANVAS
    )
    assert data is not None
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS


def test_render_cover_card_missing_photo_returns_none(tmp_path: Path) -> None:
    missing = tmp_path / "nope.jpg"
    assert (
        render_cover_card(
            missing, title="缺图", subtitle="hook", canvas_wh=CARD_CANVAS
        )
        is None
    )


def test_render_closing_card_minimal_colophon(tmp_path: Path) -> None:
    photo = tmp_path / "closing.jpg"
    _rgb(photo, color=(90, 60, 40))
    data = render_closing_card(photo, title="天山南麓", canvas_wh=CARD_CANVAS)
    assert data is not None
    with Image.open(io.BytesIO(data)) as im:
        assert im.size == CARD_CANVAS


def test_render_closing_card_missing_photo_returns_none(tmp_path: Path) -> None:
    assert (
        render_closing_card(tmp_path / "gone.jpg", title="x", canvas_wh=CARD_CANVAS)
        is None
    )


def test_render_closing_card_has_the_end_no_stats_api(tmp_path: Path) -> None:
    """AC-ABE-02 · 封底 API 不接受/不渲染天数·地点·张数统计字段。"""
    import inspect

    sig = inspect.signature(render_closing_card)
    assert "title" in sig.parameters
    assert "days" not in sig.parameters
    assert "places" not in sig.parameters
    assert "photo_count" not in sig.parameters
    assert "stats" not in sig.parameters

    photo = tmp_path / "closing.jpg"
    _rgb(photo, color=(90, 60, 40))
    data = render_closing_card(photo, title="天山南麓", canvas_wh=CARD_CANVAS)
    assert data is not None
    # Re-render must be deterministic for the same inputs (used by collage AC).
    again = render_closing_card(photo, title="天山南麓", canvas_wh=CARD_CANVAS)
    assert data == again
