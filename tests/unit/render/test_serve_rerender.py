"""Serve inline save triggers draft re-render."""



from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests._repo_root import repo_root
from travelogue.render.engine import render_trip


def test_rerender_draft_after_copy_patch(tmp_path: Path) -> None:
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        import pytest

        pytest.skip("demo assets not present")
    ws = tmp_path / "serve-trip"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = json.loads(
        (repo_root(__file__) / "schemas" / "fixtures" / "trip.render_golden.json").read_text(
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
    # Stale longshot must be overwritten (not merely listed as present).
    longshot = ws / "index-longshot.html"
    longshot.write_text("<html>STALE-LONGSHOT-MARKER</html>", encoding="utf-8")
    rendered = rerender_draft_trip(ws / "trip.json")
    after = index.read_text(encoding="utf-8")
    assert "改后的 hook" in after
    assert "index.html" in rendered
    assert "index-longshot.html" in rendered
    assert "STALE-LONGSHOT-MARKER" not in longshot.read_text(encoding="utf-8")
    assert "改后的 hook" in longshot.read_text(encoding="utf-8")


def test_rerender_draft_refreshes_mobile_when_export_layout_web(tmp_path: Path) -> None:
    """exportLayout=web 时也必须刷新 index-mobile.html，避免 AI/改文案后漂移。"""
    demo = repo_root(__file__) / "templates" / "visual-journal" / "assets"
    if not demo.is_dir():
        import pytest

        pytest.skip("demo assets not present")
    ws = tmp_path / "serve-trip-web"
    ws.mkdir()
    shutil.copytree(demo, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    trip = json.loads(
        (repo_root(__file__) / "schemas" / "fixtures" / "trip.render_golden.json").read_text(
            encoding="utf-8"
        )
    )
    trip["layoutEngine"] = "screens"
    trip["exportLayout"] = "web"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, layout_engine="screens")
    mobile = ws / "index-mobile.html"
    mobile.write_text("<html>STALE-MOBILE-MARKER</html>", encoding="utf-8")

    from travelogue.services.trip import TripService
    from travelogue.web.copy_patch import apply_copy_patches
    from travelogue.web.rerender import rerender_draft_trip

    apply_copy_patches(trip, [{"path": "meta.hook", "value": "移动端也要更新"}])
    TripService().save(trip, ws / "trip.json")
    rendered = rerender_draft_trip(ws / "trip.json")
    assert "index-mobile.html" in rendered
    body = mobile.read_text(encoding="utf-8")
    assert "STALE-MOBILE-MARKER" not in body
    assert "移动端也要更新" in body
