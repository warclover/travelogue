"""E-07: export zip size smoke for multi-photo trips."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from travelogue.demo.build import run_demo_from_album
from tests.test_ingest import _album


def test_share_zip_within_config_budget(tmp_path: Path) -> None:
    """12 photos → zip builds; oversized trips record curation warning."""
    album = _album(tmp_path, 12)
    trips = tmp_path / "trips"
    result = run_demo_from_album(
        album,
        trips_dir=trips,
        trip_id="zip-budget",
        title="体积测试",
        place="测试",
        dedupe=False,
        publish=True,
        confirm_privacy=True,
    )
    assert result.zip_path and result.zip_path.is_file()
    size_mb = result.zip_path.stat().st_size / (1024 * 1024)
    assert size_mb > 0.01
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    warnings = (trip.get("curation") or {}).get("warnings") or []
    if size_mb > 25:
        assert any("zip" in w or "MB" in w for w in warnings)
    with zipfile.ZipFile(result.zip_path) as zf:
        assert "index.html" in zf.namelist()
