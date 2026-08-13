"""CardRenderer — Pillow slot-based rendering for 3:4 cards.

PRD-EXPORT-CARD-COMPOSE-V1 §4/§6 (方案 A), ADR-021 v0.5. Each template slot is
a rectangle on that template's own base grid (``grid_rows x grid_cols`` —
3x3 for the original 9 templates, or a plain N-up grid for the 4 equal-grid
templates added in v0.4.0); every photo is cover-cropped to its slot's
exact aspect then pasted — the canvas is always fully covered (AC-ECC-01),
never letterboxed, unless album SSC passes per-slot ``fit=contain`` (AEL L1,
default off). Subject-safety reuses ``layout_contract/subject.py``'s
``asset_has_person`` signal plus ``media/image_ops.py``'s focal-aware crop
(AC-ECC-06), so the one crop-required slot in the whole library
(``card-4-square-top-triband``'s ``main`` cell) biases upward instead of
dead-center when the photo is tagged as containing a person.

Slots within a single card are separated by a thin ``CARD_SLOT_GAP`` seam
(user feedback 2026-08-05: multi-slot cards should read as "assembled tiles"
rather than one bleed image); a multi-cell slot (``col_span``/``row_span`` >
1) stays a continuous rectangle — the seam only appears *between* distinct
slots, never inside one. The gap is expressed at ``CARD_CANVAS`` base scale
and rescaled proportionally to whatever canvas width is actually rendered
(covers both the plain 1080 base and the 1.25x "更清晰" scale bump).
"""

from __future__ import annotations

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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

#: Seam between adjacent slots *within* one card (px, at CARD_CANVAS base
#: scale) — thin on purpose (a divider, not a second gutter); keeps dense
#: templates (e.g. 16-grid) from losing too much per-slot area.
CARD_SLOT_GAP = 6


def scale_canvas(base_wh: tuple[int, int], scale: int) -> tuple[int, int]:
    """Bump a base canvas ~1.25x for the "更清晰" (scale>2) Studio option."""
    w, h = base_wh
    if int(scale or 2) > 2:
        return int(round(w * 1.25)), int(round(h * 1.25))
    return w, h


def _slot_gap_for_width(width: int) -> int:
    """Scale ``CARD_SLOT_GAP`` proportionally to the rendered card width."""
    if CARD_CANVAS[0] <= 0:
        return CARD_SLOT_GAP
    return max(0, round(CARD_SLOT_GAP * (width / CARD_CANVAS[0])))

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


@dataclass(frozen=True)
class SlotCropHint:
    """Optional per-slot fit/focal from album SSC. xhs/mp leave this unset."""

    fit: str = "cover"  # "cover" | "contain"
    focal: tuple[float, float] | None = None
    # Normalized source window (x0, y0, x1, y1) for punch-in; None = full frame.
    window: tuple[float, float, float, float] | None = None


def _fit_contain(
    img: Image.Image,
    tw: int,
    th: int,
    *,
    bg: tuple[int, int, int],
) -> Image.Image:
    """Letterbox ``img`` into ``tw x th`` on paper-colored canvas (AC-AEL-08)."""
    if tw <= 0 or th <= 0:
        return Image.new("RGB", (max(1, tw), max(1, th)), bg)
    ir = img.width / max(1, img.height)
    sr = tw / th
    if ir >= sr:
        nw = tw
        nh = max(1, round(tw / ir))
    else:
        nh = th
        nw = max(1, round(th * ir))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (tw, th), bg)
    canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
    return canvas


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
    gap: int = 0,
    slot_hints: Sequence[SlotCropHint] | None = None,
    bg: tuple[int, int, int] = DEFAULT_BG,
) -> None:
    if len(photos) != template.slot_count:
        raise ValueError(
            f"card_renderer: template {template.id} expects "
            f"{template.slot_count} photos, got {len(photos)}"
        )
    if slot_hints is not None and len(slot_hints) != template.slot_count:
        raise ValueError(
            f"card_renderer: template {template.id} expects "
            f"{template.slot_count} slot hints, got {len(slot_hints)}"
        )
    cols, rows = template.grid_cols, template.grid_rows
    pad_t = round(float(template.inset[0]) * height)
    pad_r = round(float(template.inset[1]) * width)
    pad_b = round(float(template.inset[2]) * height)
    pad_l = round(float(template.inset[3]) * width)
    gx0 = x0 + pad_l
    gy0 = y0 + pad_t
    inner_w = max(1, width - pad_l - pad_r)
    inner_h = max(1, height - pad_t - pad_b)
    # Reserve (cols-1)/(rows-1) internal seams from the usable area up front,
    # so cells stay evenly sized instead of the last column/row absorbing
    # the gap's rounding slack.
    usable_w = max(1, inner_w - gap * max(0, cols - 1))
    usable_h = max(1, inner_h - gap * max(0, rows - 1))
    cell_w = usable_w / cols
    cell_h = usable_h / rows
    for idx, (path, slot) in enumerate(zip(photos, template.slots, strict=True)):
        sx0 = gx0 + round(slot.col * (cell_w + gap))
        sy0 = gy0 + round(slot.row * (cell_h + gap))
        # A multi-cell slot (col_span/row_span > 1) is one continuous photo —
        # the seam only separates *distinct* slots, never splits one in two.
        sx1 = sx0 + round(slot.col_span * cell_w + max(0, slot.col_span - 1) * gap)
        sy1 = sy0 + round(slot.row_span * cell_h + max(0, slot.row_span - 1) * gap)
        tw, th = max(1, sx1 - sx0), max(1, sy1 - sy0)
        loaded = load_image_normalized(path)
        img = loaded.image
        if img.mode != "RGB":
            img = img.convert("RGB")
        hint = slot_hints[idx] if slot_hints is not None else None
        fit = str(hint.fit).lower() if hint is not None else "cover"
        if hint is not None and hint.window is not None:
            # Do not unpack into x0/y0 — those are the canvas origin for this
            # card (or spread half). Shadowing them breaks later slots.
            wx0, wy0, wx1, wy1 = hint.window
            iw, ih = img.size
            box = (
                max(0, int(round(float(wx0) * iw))),
                max(0, int(round(float(wy0) * ih))),
                min(iw, int(round(float(wx1) * iw))),
                min(ih, int(round(float(wy1) * ih))),
            )
            if box[2] > box[0] + 1 and box[3] > box[1] + 1:
                cropped_src = img.crop(box)
                img.close()
                img = cropped_src
        if fit == "contain":
            fitted = _fit_contain(img, tw, th, bg=bg)
        else:
            if hint is not None and hint.focal is not None and hint.window is None:
                focal = hint.focal
            elif hint is not None and hint.window is not None:
                focal = (0.5, 0.5)
            else:
                focal = _focal_for_slot(path, slot.display_aspect, asset_lookup)
            cropped = crop_aspect_focal(img, tw / th, focal=focal)
            if cropped.size != (tw, th):
                cropped = cropped.resize((tw, th), Image.Resampling.LANCZOS)
            fitted = cropped
        canvas.paste(fitted, (sx0, sy0))
        img.close()


def render_card(
    photos: list[Path],
    template: CardTemplate,
    *,
    canvas_wh: tuple[int, int],
    asset_lookup: AssetLookup | None = None,
    bg: tuple[int, int, int] = DEFAULT_BG,
    slot_hints: Sequence[SlotCropHint] | None = None,
) -> tuple[bytes, dict]:
    """Render a single 3:4 card. Returns ``(png_bytes, diagnostics)``."""
    width, height = canvas_wh
    canvas = Image.new("RGB", (width, height), bg)
    gap = _slot_gap_for_width(width)
    _paint_template(
        canvas,
        template,
        photos,
        x0=0,
        y0=0,
        width=width,
        height=height,
        asset_lookup=asset_lookup,
        gap=gap,
        slot_hints=slot_hints,
        bg=bg,
    )
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    fits = [str(h.fit) for h in slot_hints] if slot_hints is not None else ["cover"] * len(photos)
    diag = {
        "canvas": [width, height],
        "template": template.id,
        "n": len(photos),
        "fit": "cover" if all(f == "cover" for f in fits) else "mixed",
        "slotFits": fits,
        "slotGap": gap,
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
    slot_hints_left: Sequence[SlotCropHint] | None = None,
    slot_hints_right: Sequence[SlotCropHint] | None = None,
) -> tuple[bytes, dict]:
    """Render an album spread: two 3:4 cards side by side with a gutter.

    ``right`` may be ``None`` for a trailing lone card (OQ-ECC-02 default:
    stand-alone half-page). 2026-08-06 fix (user report: "空槙，就是缺失照片，
    违背兜底原则" — a real screenshot showed the entire right half rendered
    as flat background with zero photos in it): the *canvas* for a lone
    card must be single-card width (``card_w``), not the full double-width
    spread with its other half left blank — a whole half-page of nothing
    is strictly worse than the "two pages open" visual it was meant to
    preserve, and every other Card in the pipeline already guarantees
    every slot gets a real photo (``assign_photos_to_slots``'s own
    "兜底" contract); the spread canvas silently broke that guarantee at
    the *page* level instead of the slot level. OQ-ECC-02's own intent —
    "stand-alone half-page" — reads naturally as *half the pixel width*,
    which is what this now does; it just wasn't implemented that way.
    """
    card_w, card_h = card_wh
    slot_gap = _slot_gap_for_width(card_w)
    half_page = right is None
    if half_page:
        canvas = Image.new("RGB", (card_w, card_h), bg)
        left_photos, left_template = left
        _paint_template(
            canvas,
            left_template,
            left_photos,
            x0=0,
            y0=0,
            width=card_w,
            height=card_h,
            asset_lookup=asset_lookup,
            gap=slot_gap,
            slot_hints=slot_hints_left,
            bg=bg,
        )
        buf = io.BytesIO()
        canvas.save(buf, format="PNG", optimize=True)
        diag = {
            "canvas": [card_w, card_h],
            "templates": [left_template.id, None],
            "gutter": 0,
            "slotGap": slot_gap,
            "halfPage": True,
            "fit": "cover",
        }
        return buf.getvalue(), diag

    total_w = card_w * 2 + gutter
    canvas = Image.new("RGB", (total_w, card_h), bg)
    left_photos, left_template = left
    _paint_template(
        canvas,
        left_template,
        left_photos,
        x0=0,
        y0=0,
        width=card_w,
        height=card_h,
        asset_lookup=asset_lookup,
        gap=slot_gap,
        slot_hints=slot_hints_left,
        bg=bg,
    )
    right_photos, right_template = right
    _paint_template(
        canvas,
        right_template,
        right_photos,
        x0=card_w + gutter,
        y0=0,
        width=card_w,
        height=card_h,
        asset_lookup=asset_lookup,
        gap=slot_gap,
        slot_hints=slot_hints_right,
        bg=bg,
    )
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    diag = {
        "canvas": [total_w, card_h],
        "templates": [left_template.id, right_template.id],
        "gutter": gutter,
        "slotGap": slot_gap,
        "halfPage": False,
        "fit": "cover",
    }
    return buf.getvalue(), diag
