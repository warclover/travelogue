"""ASCII tripId slugs matching schemas/trip.schema.json."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_TRIP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


def normalize_trip_id(raw: str, *, fallback_seed: str = "trip") -> str:
    """Produce tripId matching ^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$."""
    out = re.sub(r"[^a-z0-9]+", "-", raw.strip().lower())
    out = re.sub(r"-+", "-", out).strip("-")
    if len(out) < 3:
        digest = hashlib.sha256(fallback_seed.encode("utf-8")).hexdigest()[:10]
        out = f"demo-{digest}"
    if len(out) > 64:
        out = out[:64].rstrip("-")
    if not out or not out[0].isalnum():
        out = f"t-{out}" if out else f"demo-{hashlib.sha256(fallback_seed.encode()).hexdigest()[:10]}"
    if not out[-1].isalnum():
        out = f"{out}0"
    if not _TRIP_ID_RE.match(out):
        digest = hashlib.sha256(fallback_seed.encode("utf-8")).hexdigest()[:10]
        out = f"demo-{digest}"
    return out


def demo_trip_id_from_album(
    album_dir: Path,
    *,
    title: str,
    place: str,
    explicit: str | None = None,
) -> str:
    """Prefer --trip-id, else album folder name, else demo-{ascii(place-title)} or hash."""
    seed = f"{album_dir.name}:{title}:{place}"
    if explicit:
        return normalize_trip_id(explicit, fallback_seed=seed)
    folder = album_dir.name.strip().lower()
    if _TRIP_ID_RE.match(folder):
        return folder
    for candidate in (f"{place}-{title}", place, title, album_dir.name):
        ascii_slug = re.sub(r"[^a-z0-9]+", "-", candidate.strip().lower())
        ascii_slug = re.sub(r"-+", "-", ascii_slug).strip("-")
        if len(ascii_slug) >= 3:
            return normalize_trip_id(f"demo-{ascii_slug}", fallback_seed=seed)
    return normalize_trip_id("", fallback_seed=seed)
