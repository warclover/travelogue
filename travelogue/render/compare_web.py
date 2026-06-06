"""Compare legacy vs screens Web layout for the same trip (cross-platform)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.render.engine import render_trip
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.layout import apply_layout_to_trip


@dataclass
class CompareWebResult:
    trip_dir: Path
    legacy_html: Path
    screens_html: Path


def compare_web_layout(
    trip_path: Path | str,
    *,
    out_dir: Path | str | None = None,
) -> CompareWebResult:
    """
    Render index-legacy.html and index-screens.html for A/B review.

    Mirrors scripts/compare-web-layout.ps1 without shelling out.
    """
    trip_file = Path(trip_path).resolve()
    if not trip_file.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_file}")
    trip_dir = trip_file.parent if out_dir is None else Path(out_dir)
    trip_dir.mkdir(parents=True, exist_ok=True)

    svc = app_context_for_trip_json(trip_file).trip_service()
    trip = svc.load(trip_file)
    apply_layout_to_trip(trip, export_layout="web", layout_engine="screens")
    svc.save(trip, trip_file)

    render_trip(
        trip_file,
        trip_dir,
        validate=False,
        layout_engine="legacy",
        export_layout_override="web",
        index_name="index-legacy.html",
    )
    render_trip(
        trip_file,
        trip_dir,
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        index_name="index-screens.html",
    )

    legacy_path = trip_dir / "index-legacy.html"
    screens_path = trip_dir / "index-screens.html"
    return CompareWebResult(
        trip_dir=trip_dir,
        legacy_html=legacy_path,
        screens_html=screens_path,
    )
