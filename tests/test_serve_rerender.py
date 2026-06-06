"""Serve inline save triggers draft re-render."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from travelogue.render.engine import render_trip


def test_rerender_draft_after_copy_patch(tmp_path: Path) -> None:
    demo = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        import pytest

        pytest.skip("demo assets not present")
    ws = tmp_path / "serve-trip"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = json.loads(
        (Path(__file__).resolve().parents[1] / "schemas" / "fixtures" / "trip.render_golden.json").read_text(
            encoding="utf-8"
        )
    )
    trip["layoutEngine"] = "screens"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")

    index = ws / "index.html"
    from travelogue.services.trip import TripService
    from travelogue.web.copy_patch import apply_copy_patches
    from travelogue.web.rerender import rerender_draft_trip

    apply_copy_patches(trip, [{"path": "meta.hook", "value": "改后的 hook"}])
    TripService().save(trip, ws / "trip.json")
    rendered = rerender_draft_trip(ws / "trip.json")
    after = index.read_text(encoding="utf-8")
    assert "改后的 hook" in after
    assert "index.html" in rendered
