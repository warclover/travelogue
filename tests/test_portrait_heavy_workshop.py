"""Second-album style: portrait-heavy ingest → screens render."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from PIL import Image, ImageDraw

from travelogue.curation.curate import run_curate
from travelogue.render.engine import render_trip_surfaces
from travelogue.services.trip_factory import create_trip
from travelogue.services.validate import validate_trip

import pytest

pytestmark = pytest.mark.integration


def _portrait_album(tmp_path: Path, n: int = 8) -> Path:
    album = tmp_path / "portrait-album"
    album.mkdir()
    stamp = time.time() - n * 90
    for i in range(n):
        path = album / f"v{i:02d}.jpg"
        size = (1200 + i * 80, 1800 + i * 50)
        img = Image.new("RGB", size, (20 + i * 35, 60 + i * 28, 100 + i * 18))
        draw = ImageDraw.Draw(img)
        for y in range(0, size[1], 36):
            draw.line(
                [(0, y), (size[0] - 1, y)],
                fill=((y // 36 + i * 17) % 255, (i * 23) % 255, 140),
                width=2,
            )
        img.save(path, quality=92)
        os.utime(path, (stamp + i * 90, stamp + i * 90))
    return album


def test_portrait_heavy_curate_and_dual_render(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("portrait-heavy", trips, title="竖图集")
    trip_dir = trips / "portrait-heavy"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    from travelogue.media.ingest import ingest_into_trip

    ingest_into_trip(trip, trip_dir, from_dir=_portrait_album(tmp_path), dedupe=False)
    run_curate(trip, export_layout="auto", layout_engine="screens", trip_dir=trip_dir)
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    validate_trip(trip)
    web, mobile, _present = render_trip_surfaces(
        trip_json, trip_dir, export_mode="draft", validate=False
    )
    assert web.is_file() and mobile.is_file()
    html = web.read_text(encoding="utf-8")
    assert "screen-plate" in html or "layout-screen" in html
