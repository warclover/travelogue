"""Geo event detection tests (Phase 3 M12)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from travelogue.curation.geo_events import detect_geo_events, gps_coverage_ratio, haversine_km
from travelogue.config import GeoClusterConfig

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "clustering"


def _asset(
    aid: str,
    taken_at: str,
    lat: float,
    lon: float,
    *,
    city: str | None = None,
) -> dict:
    out = {
        "id": aid,
        "type": "image",
        "takenAt": taken_at,
        "geo": {"lat": lat, "lon": lon},
    }
    if city:
        out["place"] = {"city": city}
    return out


def test_haversine_km_tokyo_kyoto_approx() -> None:
    # Tokyo ~ Kyoto ~370km
    d = haversine_km(35.681, 139.767, 35.011, 135.768)
    assert 350 < d < 400


def test_gps_coverage_ratio() -> None:
    assets = [
        _asset("a1", "2025-04-01T10:00:00Z", 35.0, 139.0),
        {"id": "a2", "type": "image", "takenAt": "2025-04-01T11:00:00Z"},
    ]
    assert gps_coverage_ratio(assets) == 0.5


def test_detect_geo_events_splits_distant_same_day() -> None:
    """Same calendar day but Tokyo afternoon + Kyoto evening → two events."""
    assets = [
        _asset("t1", "2025-04-01T09:00:00Z", 35.681, 139.767, city="东京"),
        _asset("t2", "2025-04-01T10:00:00Z", 35.682, 139.768, city="东京"),
        _asset("t3", "2025-04-01T11:00:00Z", 35.683, 139.769, city="东京"),
        _asset("k1", "2025-04-01T14:00:00Z", 35.011, 135.768, city="京都"),
        _asset("k2", "2025-04-01T15:00:00Z", 35.012, 135.769, city="京都"),
        _asset("k3", "2025-04-01T16:00:00Z", 35.013, 135.770, city="京都"),
    ]
    segs = detect_geo_events(assets, cfg=GeoClusterConfig(min_photos_per_event=3))
    assert len(segs) == 2
    assert {a for s in segs for a in s.asset_ids} == {a["id"] for a in assets}
    assert segs[0].start_date == date(2025, 4, 1)


def test_detect_geo_events_no_gps_returns_empty() -> None:
    assets = [
        {"id": "a1", "type": "image", "takenAt": "2025-04-01T10:00:00Z"},
        {"id": "a2", "type": "image", "takenAt": "2025-04-01T11:00:00Z"},
    ]
    assert detect_geo_events(assets) == []


def test_detect_geo_events_deterministic() -> None:
    assets = [
        _asset(f"a{i}", f"2025-05-{10 + i:02d}T12:00:00Z", 35.0 + i * 0.01, 139.0, city="测试")
        for i in range(6)
    ]
    a = detect_geo_events(assets)
    b = detect_geo_events(assets)
    assert [s.to_dict() for s in a] == [s.to_dict() for s in b]


def test_synthetic_fixture_manifest_if_present() -> None:
    manifest = FIXTURES / "synthetic-gps" / "assets-manifest.json"
    if not manifest.is_file():
        return
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    assets = raw["assets"] if isinstance(raw, dict) and "assets" in raw else raw
    segs = detect_geo_events(assets)
    golden_path = FIXTURES / "synthetic-gps" / "segments-golden.json"
    if not golden_path.is_file():
        assert len(segs) >= 1
        return
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert len(segs) == len(golden)
