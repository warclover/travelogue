"""Detect trip-local journal-screens.css missing layout grid classes (AC-P16-11)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.curation.screen_planner import grid_class_for_pattern


def required_grid_classes_from_trip(data: dict[str, Any]) -> set[str]:
    classes: set[str] = set()
    for ch in data.get("chapters") or []:
        for screen in ch.get("screens") or []:
            geo = screen.get("layoutGeometry") or {}
            gc = str(geo.get("gridClass") or "").strip()
            if gc:
                classes.add(gc)
                continue
            pid = str(screen.get("patternId") or "").strip()
            if pid and pid != "screen-breath-pause":
                classes.add(grid_class_for_pattern(pid))
    return classes


def _screens_use_solid_geometry(data: dict[str, Any]) -> bool:
    """True when every layout screen has LTE geometry固化 (rerender optional, AC-P16-11)."""
    found = False
    for ch in data.get("chapters") or []:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "").strip()
            if not pid or pid == "screen-breath-pause":
                continue
            found = True
            geo = screen.get("layoutGeometry") or {}
            if not geo.get("cols") or not geo.get("rows"):
                return False
    return found


def trip_layout_css_stale(trip_dir: Path, data: dict[str, Any] | None = None) -> bool:
    """True when a copied trip CSS file lacks grid classes used by curated screens."""
    trip_json = trip_dir / "trip.json"
    if data is None:
        if not trip_json.is_file():
            return False
        try:
            data = json.loads(trip_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
    if _screens_use_solid_geometry(data):
        return False
    required = required_grid_classes_from_trip(data)
    if not required:
        return False
    trip_css = trip_dir / "journal-screens.css"
    if not trip_css.is_file():
        return False
    try:
        text = trip_css.read_text(encoding="utf-8")
    except OSError:
        return True
    return any(gc not in text for gc in required)


def trip_render_bundle_stale(trip_dir: Path, data: dict[str, Any] | None = None) -> bool:
    """True when trip.json is newer than index.html (LRG G-LRG-08 preview stale).

    Detects curate/copy edits that were not followed by ``render`` — the common cause
    of trip.json vs index.html screen-count drift in dogfood acceptance.
    """
    trip_json = trip_dir / "trip.json"
    index_html = trip_dir / "index.html"
    if not trip_json.is_file() or not index_html.is_file():
        return False
    if data is None:
        try:
            data = json.loads(trip_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    from travelogue.curation.algorithm_profile import _trip_updated_mtime

    trip_mtime = _trip_updated_mtime(trip_dir, data)
    try:
        return trip_mtime > index_html.stat().st_mtime + 0.5
    except OSError:
        return False
