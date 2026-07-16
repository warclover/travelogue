"""AC-MRS-08′ · share zip must not leak local absolute album paths."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from travelogue.export.packager import export_trip
from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.engine import render_trip

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
LEAK_MARKER = "LeakProbeAlbumRoot"


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    leak_root = tmp_path / LEAK_MARKER / "photos"
    leak_abs = str(leak_root.resolve())
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        asset["sourceRef"] = {
            "kind": "filesystem",
            "path": f"{leak_abs}\\{asset.get('id', 'x')}.jpg",
            "albumRoot": leak_abs,
            "relativePath": f"{asset.get('id', 'x')}.jpg",
        }
    trip["media"] = {"storageMode": "referenced", "albumRoots": [leak_abs]}

    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_export_zip_excludes_trip_json_and_absolute_paths(trip_workspace: Path) -> None:
    trip_json = trip_workspace / "trip.json"
    render_trip(trip_json, validate=False)
    zip_path = export_trip(trip_json, confirm_privacy=True, validate=False)
    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "trip.json" not in names
        assert not any(n.startswith("source/") for n in names)
        for name in names:
            if not name.endswith((".html", ".js", ".css", ".json", ".map")):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            assert LEAK_MARKER not in text, f"leak marker in {name}"
            assert "sourceRef" not in text, f"sourceRef leaked into {name}"


def test_assess_source_missing_for_referenced(tmp_path: Path) -> None:
    from travelogue.media.source_resolve import assess_source_availability

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    trip = {
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "sourceRef": {
                    "kind": "filesystem",
                    "path": str(tmp_path / "gone" / "a.jpg"),
                },
            }
        ],
        "media": {"storageMode": "referenced"},
    }
    health = assess_source_availability(trip, trip_dir)
    assert health["sourceMissing"] is True
    assert health["missingCount"] == 1
