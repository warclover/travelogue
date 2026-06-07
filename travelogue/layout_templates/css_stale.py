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
