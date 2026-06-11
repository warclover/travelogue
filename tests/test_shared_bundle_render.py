"""Studio shared bundle refs (A-14 · R-P2-04)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.bundle_serve import BUNDLE_ASSET_PREFIX, bundle_asset_root
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_bundle_asset_root_visual_journal() -> None:
    assert bundle_asset_root("visual-journal") == f"{BUNDLE_ASSET_PREFIX}visual-journal/"


def test_shared_bundle_refs_skips_js_copy(trip_workspace: Path) -> None:
    render_trip(
        trip_workspace / "trip.json",
        validate=False,
        export_mode="draft",
        shared_bundle_refs=True,
    )
    html = (trip_workspace / "index.html").read_text(encoding="utf-8")
    assert BUNDLE_ASSET_PREFIX in html
    assert "copy-toggle.js" in html
    assert not (trip_workspace / "copy-toggle.js").is_file()
    assert not (trip_workspace / "longshot-bridge.js").is_file()
    assert (trip_workspace / "journal.css").is_file()


def test_default_render_still_materializes_bundle_files(trip_workspace: Path) -> None:
    render_trip(trip_workspace / "trip.json", validate=False, export_mode="draft")
    assert (trip_workspace / "journal.css").is_file()
    assert (trip_workspace / "copy-toggle.js").is_file()
