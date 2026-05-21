"""Materialize trips/_golden-reference from render_golden fixture + template assets."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip
from travelogue.render.golden_regression import GOLDEN_TRIP_FIXTURE

GOLDEN_REFERENCE_DIR_NAME = "_golden-reference"
GOLDEN_REFERENCE_TRIP_ID = "render-golden-demo"
DEMO_ASSETS_SRC = TEMPLATE_VISUAL_JOURNAL / "assets"


@dataclass
class GoldenReferenceResult:
    trip_dir: Path
    created: bool
    message: str


def golden_reference_dir(trips_root: Path | None = None) -> Path:
    root = trips_root or (ROOT / "trips")
    return root / GOLDEN_REFERENCE_DIR_NAME / GOLDEN_REFERENCE_TRIP_ID


def materialize_golden_reference(
    trips_root: Path | None = None,
    *,
    force: bool = False,
) -> GoldenReferenceResult:
    """
    Write ``trips/_golden-reference/render-golden-demo/`` with trip.json, demo assets, index.html.

    Same data contract as ``templates/visual-journal/golden.html`` (via fixture).
    """
    if not GOLDEN_TRIP_FIXTURE.is_file():
        raise FileNotFoundError(GOLDEN_TRIP_FIXTURE)
    if not DEMO_ASSETS_SRC.is_dir():
        raise FileNotFoundError(DEMO_ASSETS_SRC)

    trips_root = (trips_root or (ROOT / "trips")).resolve()
    ws = golden_reference_dir(trips_root)
    created = not ws.is_dir()

    if ws.exists() and force:
        shutil.rmtree(ws)
        created = True

    ws.mkdir(parents=True, exist_ok=True)
    trip = json.loads(GOLDEN_TRIP_FIXTURE.read_text(encoding="utf-8"))
    (ws / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    assets_dest = ws / "assets"
    if assets_dest.exists():
        shutil.rmtree(assets_dest)
    shutil.copytree(DEMO_ASSETS_SRC, assets_dest)

    demo = assets_dest / "demo"
    demo.mkdir(parents=True, exist_ok=True)
    (demo / "placeholder.m4a").write_bytes(b"")
    (demo / "video.mp4").write_bytes(b"")

    render_trip(ws / "trip.json", validate=False, update_pipeline=False)

    msg = f"reference trip: {ws}"
    if created:
        msg = f"materialized {msg}"
    else:
        msg = f"refreshed {msg}"
    return GoldenReferenceResult(trip_dir=ws, created=created, message=msg)
