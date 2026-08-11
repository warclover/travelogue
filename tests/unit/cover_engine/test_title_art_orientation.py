"""Title-art orientation must follow Opening style (folio vertical / others horizontal)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.cover_engine.title_art.engine import (
    _horizontal_style_cached_art_is_portrait,
    _vertical_style_cached_art_is_landscape,
)
from travelogue.cover_engine.title_art.render_b import render_title_art


def test_folio_render_produces_portrait_strip() -> None:
    art = render_title_art("珠海东澳岛一日游", opening_style_id="folio-overlap")
    im = Image.open(__import__("io").BytesIO(art.png_bytes))
    assert im.size[1] > im.size[0] * 1.25


def test_veil_render_produces_landscape_strip() -> None:
    art = render_title_art("珠海东澳岛一日游", opening_style_id="veil-footer")
    im = Image.open(__import__("io").BytesIO(art.png_bytes))
    assert im.size[0] > im.size[1] * 1.25


def test_cached_landscape_invalid_for_folio(tmp_path: Path) -> None:
    png = tmp_path / "wide.png"
    Image.new("RGBA", (800, 80), (0, 0, 0, 0)).save(png)
    existing = {"assetPath": "wide.png"}
    assert (
        _vertical_style_cached_art_is_landscape(
            existing, style_id="folio-overlap", trip_root=tmp_path
        )
        is True
    )
    assert (
        _vertical_style_cached_art_is_landscape(
            existing, style_id="veil-footer", trip_root=tmp_path
        )
        is False
    )


def test_cached_portrait_invalid_for_veil(tmp_path: Path) -> None:
    png = tmp_path / "tall.png"
    Image.new("RGBA", (80, 800), (0, 0, 0, 0)).save(png)
    existing = {"assetPath": "tall.png"}
    assert (
        _horizontal_style_cached_art_is_portrait(
            existing, style_id="veil-footer", trip_root=tmp_path
        )
        is True
    )
    assert (
        _horizontal_style_cached_art_is_portrait(
            existing, style_id="folio-overlap", trip_root=tmp_path
        )
        is False
    )
