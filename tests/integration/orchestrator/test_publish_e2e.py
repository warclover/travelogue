"""End-to-end: album → trip.json → shareable zip."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from tests.studio_test_helpers import make_test_album as _album
from travelogue.demo.build import run_demo_from_album
from travelogue.orchestrator.run import run_trip

pytestmark = pytest.mark.integration


def _assert_share_zip(zip_path: Path) -> None:
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        assert "index.html" in names
        assert "journal.css" in names
        assert "preview.jpg" in names
        assert "longshot.js" in names
        assert "share.js" in names
        assert any(n.startswith("assets/") and n.endswith(".webp") for n in names)
        html = zf.read("index.html").decode("utf-8")
        assert 'data-export="share"' in html
        assert 'data-block="share-toolbar"' in html
        assert "share.js" in html
        assert 'data-editable' not in html


def test_demo_publish_produces_share_zip(tmp_path: Path) -> None:
    album = _album(tmp_path, 6)
    trips = tmp_path / "trips"
    result = run_demo_from_album(
        album,
        trips_dir=trips,
        trip_id="e2e-publish",
        title="端到端测试",
        place="测试城",
        dedupe=False,
        publish=True,
        confirm_privacy=True,
    )
    assert "ingest" in result.stages
    assert "curate" in result.stages
    assert "render" in result.stages
    assert "export" in result.stages
    assert result.zip_path is not None
    _assert_share_zip(result.zip_path)

    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip["pipeline"]["status"] == "exported"
    assert trip["privacy"]["confirmedAt"]
    assert trip["meta"]["hook"]
    assert (trip.get("epilogue") or "").strip()


def test_run_until_exported_from_existing_demo(tmp_path: Path) -> None:
    album = _album(tmp_path, 6)
    trips = tmp_path / "trips"
    preview = run_demo_from_album(
        album,
        trips_dir=trips,
        trip_id="e2e-run-export",
        title="运行导出",
        place="测试",
        dedupe=False,
    )
    run_result = run_trip(
        preview.trip_json,
        from_stage="lock_structure",
        until="exported",
        confirm_privacy=True,
        validate=False,
    )
    assert "lock_structure" in run_result.stages
    assert "narrate" in run_result.stages
    assert "export" in run_result.stages
    assert run_result.publish is not None
    _assert_share_zip(run_result.publish.zip_path)
