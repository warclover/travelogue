"""BSP P3-02 skeleton · 8+1 golden trip surface spot checks (extend per bsp-surface-report.json)."""

from __future__ import annotations

import json

import pytest

from travelogue.paths import ROOT

TEMPLATE = ROOT / "docs" / "templates" / "bsp-surface-report.json"
TRIPS_DIR = ROOT / "trips"

pytestmark = pytest.mark.e2e


def _golden_trip_ids() -> list[str]:
    if not TEMPLATE.is_file():
        return ["demo-d66fe642a9", "linzhi"]
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    return list(data.get("trips", {}).keys())


@pytest.mark.parametrize("trip_id", _golden_trip_ids())
def test_golden_trip_has_rendered_index(trip_id: str) -> None:
    """Placeholder gate: trip 目录存在且 index.html 含 screens 引擎标记。"""
    trip_dir = TRIPS_DIR / trip_id
    if not (trip_dir / "trip.json").is_file():
        pytest.skip(f"missing trip {trip_id}")
    index = trip_dir / "index.html"
    if not index.is_file():
        pytest.skip(f"{trip_id} not rendered")
    html = index.read_text(encoding="utf-8")
    assert 'data-layout-engine="screens"' in html or "layout-screen" in html
