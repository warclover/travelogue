"""Sample chapter/screen background tone from image files (layoutEngine=screens)."""

from __future__ import annotations

from pathlib import Path

from travelogue.media.color_metrics import _iter_rgb_pixels

_DEFAULT_TONE = {"r": 232, "g": 228, "b": 223}

_FALLBACK_TONES = (
    {"r": 232, "g": 228, "b": 223},
    {"r": 216, "g": 222, "b": 218},
    {"r": 228, "g": 220, "b": 210},
    {"r": 210, "g": 214, "b": 220},
)


def fallback_tone(index: int = 0) -> dict:
    return dict(_FALLBACK_TONES[index % len(_FALLBACK_TONES)])


def sample_tone_from_path(path: Path) -> dict | None:
    """Average RGB of a downscaled image; None if unreadable."""
    if not path.is_file():
        return None
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return None
    try:
        with Image.open(path) as img:
            rgb = img.convert("RGB").resize((32, 32))
            pixels = list(_iter_rgb_pixels(rgb))
        if not pixels:
            return None
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return {"r": r, "g": g, "b": b}
    except OSError:
        return None


def sample_tone_for_asset(
    asset: dict,
    *,
    trip_root: Path | None,
    fallback_index: int = 0,
) -> dict:
    if trip_root is not None:
        for key in ("displayFile", "sourceFile"):
            rel = asset.get(key)
            if rel:
                sampled = sample_tone_from_path(trip_root / rel)
                if sampled:
                    return sampled
    return fallback_tone(fallback_index)


def enrich_screen_tones(
    screens: list[dict],
    assets: dict[str, dict],
    *,
    trip_root: Path | None = None,
    chapter_index: int = 0,
) -> list[dict]:
    """Fill screen.tone for contain singles; others may stay None (CSS page bg)."""
    out: list[dict] = []
    prev_tone: dict | None = None
    for i, sc in enumerate(screens):
        sc = dict(sc)
        if sc.get("tone"):
            out.append(sc)
            prev_tone = sc["tone"]
            continue
        pattern = sc.get("patternId", "")
        needs_tone = pattern.endswith("-1") and "portrait" in pattern
        if needs_tone:
            slot_ids = [s["assetId"] for s in sc.get("slots") or []]
            tone = None
            if slot_ids:
                tone = sample_tone_for_asset(
                    assets[slot_ids[0]],
                    trip_root=trip_root,
                    fallback_index=chapter_index + i,
                )
            if tone is None and prev_tone:
                tone = prev_tone
            if tone is None:
                tone = fallback_tone(chapter_index + i)
            sc["tone"] = tone
            prev_tone = tone
        out.append(sc)
    return out
