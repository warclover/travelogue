"""CardRenderer — Pillow slot-based rendering for 3:4 cards.

PRD-EXPORT-CARD-COMPOSE-V1 §4/§6 (方案 A), ADR-021 v0.4. Each template slot is
a rectangle on a 3x3 base grid; every photo is cover-cropped to its slot's
exact aspect then pasted — the canvas is always fully covered (AC-ECC-01),
never letterboxed. Subject-safety reuses ``layout_contract/subject.py``'s
``asset_has_person`` signal plus ``media/image_ops.py``'s focal-aware crop
(AC-ECC-06), so the one crop-required slot in the whole library
(``card-4-square-top-triband``'s ``main`` cell) biases upward instead of
dead-center when the photo is tagged as containing a person.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from travelogue.export.card_templates import CardTemplate
from travelogue.layout_contract.subject import asset_has_person
from travelogue.media.image_ops import crop_aspect_focal, load_image_normalized

DEFAULT_BG = (245, 245, 243)

#: Base single-card canvas (3:4), shared by xiaohongshu pages, poster_bric,
#: and each half of an album_spread.
CARD_CANVAS = (1080, 1440)

#: Album spread gutter (px, at CARD_CANVAS base scale) — visually separates
#: the two cards so the spread reads as "two pages open", not one seamless
#: image (PRD-EXPORT-CARD-COMPOSE-V1 §3.1).
ALBUM_GUTTER = 48


def scale_canvas(base_wh: tuple[int, int], scale: int) -> tuple[int, int]:
    """Bump a base canvas ~1.25x for the "更清晰" (scale>2) Studio option."""
    w, h = base_wh
    if int(scale or 2) > 2:
        return int(round(w * 1.25)), int(round(h * 1.25))
    return w, h

#: displayAspect band that forces a real crop for *every* natural photo
#: orientation (portrait ~0.75, landscape ~1.5 both miss it) — currently only
#: card-4-square-top-triband's main slot (aspect≈1.125) falls in this band.
_CROP_REQUIRED_ASPECT_RANGE = (1.0, 1.3)
_CONSERVATIVE_FOCAL_PERSON: tuple[float, float] = (0.5, 0.38)
_DEFAULT_FOCAL: tuple[float, float] = (0.5, 0.45)

#: Given a photo Path, return its asset dict (for focalPoint / person tags),
#: or None if unknown. Callers (poster_bric_pack.py / collage_pack.py) build
#: this from trip.json; CardRenderer stays decoupled from trip structure.
AssetLookup = Callable[[Path], "dict | None"]


def _focal_for_slot(
    path: Path, display_aspect: float, asset_lookup: AssetLookup | None
) -> tuple[float, float]:
    asset = asset_lookup(path) if asset_lookup else None
    if asset:
        raw = asset.get("focalPoint")
        if raw:
            try:
                return (float(raw.get("x", 0.5)), float(raw.get("y", 0.45)))
            except (TypeError, ValueError):
                pass
    lo, hi = _CROP_REQUIRED_ASPECT_RANGE
    if lo < display_aspect < hi and asset_has_person(asset):
        return _CONSERVATIVE_FOCAL_PERSON
    return _DEFAULT_FOCAL


def _paint_template(
    canvas: Image.Image,
    template: CardTemplate,
    photos: list[Path],
    *,
    x0: int,
    y0: int,
    width: int,
    height: int,
    asset_lookup: AssetLookup | None,
) -> None:
    if len(photos) != template.slot_count:
        raise ValueError(
            f"card_renderer: template {template.id} expects "
            f"{template.slot_count} photos, got {len(photos)}"
        )
    cell_w = width / 3
    cell_h = height / 3
    for path, slot in zip(photos, template.slots, strict=True):
        sx0 = x0 + round(slot.col * cell_w)
        sy0 = y0 + round(slot.row * cell_h)
        sx1 = x0 + round((slot.col + slot.col_span) * cell_w)
        sy1 = y0 + round((slot.row + slot.row_span) * cell_h)
        tw, th = max(1, sx1 - sx0), max(1, sy1 - sy0)
        loaded = load_image_normalized(path)
        img = loaded.image
        if img.mode != "RGB":
            img = img.convert("RGB")
        focal = _focal_for_slot(path, slot.display_aspect, asset_lookup)
        cropped = crop_aspect_focal(img, tw / th, focal=focal)
        if cropped.size != (tw, th):
            cropped = cropped.resize((tw, th), Image.Resampling.LANCZOS)
        canvas.paste(cropped, (sx0, sy0))
        img.close()


def render_card(
    photos: list[Path],
    template: CardTemplate,
    *,
    canvas_wh: tuple[int, int],
    asset_lookup: AssetLookup | None = None,
    bg: tuple[int, int, int] = DEFAULT_BG,
) -> tuple[bytes, dict]:
    """Render a single 3:4 card. Returns ``(png_bytes, diagnostics)``."""
    width, height = canvas_wh
    canvas = Image.new("RGB", (width, height), bg)
    _paint_template(
        canvas, template, photos, x0=0, y0=0, width=width, height=height, asset_lookup=asset_lookup
    )
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    diag = {
        "canvas": [width, height],
        "template": template.id,
        "n": len(photos),
        "fit": "cover",
    }
    return buf.getvalue(), diag


def render_spread(
    left: tuple[list[Path], CardTemplate],
    right: tuple[list[Path], CardTemplate] | None,
    *,
    card_wh: tuple[int, int],
    gutter: int,
    asset_lookup: AssetLookup | None = None,
    bg: tuple[int, int, int] = DEFAULT_BG,
) -> tuple[bytes, dict]:
    """Render an album spread: two 3:4 cards side by side with a gutter.

    ``right`` may be ``None`` for a trailing lone card (OQ-ECC-02 default:
    stand-alone half-page — the right half stays background-filled rather
    than stretching the left card, keeping the "two pages open" read intact).
    """
    card_w, card_h = card_wh
    total_w = card_w * 2 + gutter
    canvas = Image.new("RGB", (total_w, card_h), bg)
    left_photos, left_template = left
    _paint_template(
        canvas, left_template, left_photos, x0=0, y0=0, width=card_w, height=card_h, asset_lookup=asset_lookup
    )
    half_page = right is None
    right_template_id = None
    if right is not None:
        right_photos, right_template = right
        right_template_id = right_template.id
        _paint_template(
            canvas,
            right_template,
            right_photos,
            x0=card_w + gutter,
            y0=0,
            width=card_w,
            height=card_h,
            asset_lookup=asset_lookup,
        )
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    diag = {
        "canvas": [total_w, card_h],
        "templates": [left_template.id, right_template_id],
        "gutter": gutter,
        "halfPage": half_page,
        "fit": "cover",
    }
    return buf.getvalue(), diag
