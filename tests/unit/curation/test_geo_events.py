"""Geo event detection tests (Phase 3 M12)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from travelogue.config import GeoClusterConfig
from travelogue.curation.geo_events import (
    _adaptive_gap_threshold_hours,
    detect_geo_events,
    gps_coverage_ratio,
    haversine_km,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "clustering"


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


def test_adaptive_gap_bimodal_when_p75_is_zero() -> None:
    """Uniform short gaps: p75=0 but p90>0 should still pick upper-mode threshold."""
    base = datetime(2025, 6, 1, 10, 0, 0)
    timestamps = [base + timedelta(minutes=i * 5) for i in range(20)]
    timestamps.append(base + timedelta(hours=8))
    chosen = _adaptive_gap_threshold_hours(timestamps, fallback_hours=4.0)
    assert chosen >= 4.0


def test_orphan_inside_long_segment_not_short_neighbor() -> None:
    """Photo inside a long segment must not attach to a shorter same-day segment."""
    assets = []
    for i in range(5):
        assets.append(
            _asset(
                f"long{i}",
                f"2025-05-01T{9 + i:02d}:00:00Z",
                35.68 + i * 0.001,
                139.76,
                city="东京",
            )
        )
    for i in range(3):
        assets.append(
            _asset(
                f"short{i}",
                "2025-05-01T20:00:00Z",
                35.01 + i * 0.001,
                135.76,
                city="京都",
            )
        )
    assets.append(
        _asset("orphan", "2025-05-05T12:00:00Z", 35.685, 139.765, city="东京")
    )
    segs, _ = detect_geo_events(
        assets,
        cfg=GeoClusterConfig(min_photos_per_event=3, event_gap_mode="fixed"),
        event_time_gap_hours=72.0,
    )
    long_seg = next(s for s in segs if "long0" in s.asset_ids)
    assert "orphan" in long_seg.asset_ids


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
    segs, _meta = detect_geo_events(assets, cfg=GeoClusterConfig(min_photos_per_event=3))
    assert len(segs) == 2
    assert {a for s in segs for a in s.asset_ids} == {a["id"] for a in assets}
    assert segs[0].start_date == date(2025, 4, 1)


def test_detect_geo_events_no_gps_returns_empty() -> None:
    assets = [
        {"id": "a1", "type": "image", "takenAt": "2025-04-01T10:00:00Z"},
        {"id": "a2", "type": "image", "takenAt": "2025-04-01T11:00:00Z"},
    ]
    segs, _meta = detect_geo_events(assets)
    assert segs == []


def test_detect_geo_events_deterministic() -> None:
    assets = [
        _asset(f"a{i}", f"2025-05-{10 + i:02d}T12:00:00Z", 35.0 + i * 0.01, 139.0, city="测试")
        for i in range(6)
    ]
    a, _ = detect_geo_events(assets)
    b, _ = detect_geo_events(assets)
    assert [s.to_dict() for s in a] == [s.to_dict() for s in b]


def test_adaptive_gap_threshold_from_distribution() -> None:
    timestamps = [
        datetime(2025, 4, 1, 10, 0),
        datetime(2025, 4, 1, 10, 5),
        datetime(2025, 4, 1, 10, 10),
        datetime(2025, 4, 1, 18, 0),
        datetime(2025, 4, 1, 18, 5),
    ]
    gap = _adaptive_gap_threshold_hours(timestamps, fallback_hours=4.0)
    assert 4.0 <= gap <= 8.5


def test_adaptive_gap_prefers_upper_mode_for_lunch_break() -> None:
    timestamps = [
        datetime(2025, 6, 1, 9, 0),
        datetime(2025, 6, 1, 10, 0),
        datetime(2025, 6, 1, 11, 0),
        datetime(2025, 6, 1, 17, 0),
        datetime(2025, 6, 1, 18, 0),
        datetime(2025, 6, 1, 19, 0),
    ]
    gap = _adaptive_gap_threshold_hours(timestamps, fallback_hours=4.0)
    assert gap >= 5.5


def test_gap_edge_fixture_auto_beats_fixed_agreement() -> None:
    from travelogue.curation.cluster_eval import geo_segment_agreement_rate, segments_to_eval_dict

    manifest = FIXTURES / "golden-gap-edge" / "assets-manifest.json"
    golden_path = FIXTURES / "golden-gap-edge" / "segments-golden.json"
    if not manifest.is_file() or not golden_path.is_file():
        return
    assets = json.loads(manifest.read_text(encoding="utf-8"))["assets"]
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    eval_kw = dict(event_time_gap_hours=4, merge_time_gap_hours=0, min_photos_per_event=3)
    fixed, _ = detect_geo_events(assets, cfg=GeoClusterConfig(event_gap_mode="fixed", **eval_kw))
    auto, _ = detect_geo_events(assets, cfg=GeoClusterConfig(event_gap_mode="auto", **eval_kw))
    base = geo_segment_agreement_rate(golden, segments_to_eval_dict(fixed))
    cand = geo_segment_agreement_rate(golden, segments_to_eval_dict(auto))
    assert base < cand
    assert cand == 1.0


def test_detect_geo_events_auto_mode_writes_meta() -> None:
    assets = [
        _asset(f"a{i}", f"2025-05-{10 + i:02d}T12:00:00Z", 35.0 + i * 0.01, 139.0, city="测试")
        for i in range(6)
    ]
    segs, meta = detect_geo_events(assets, cfg=GeoClusterConfig(event_gap_mode="auto"))
    assert segs
    assert meta["gapMode"] in ("auto", "fixed")
    assert meta["thresholdHours"] > 0


def test_synthetic_fixture_manifest_if_present() -> None:
    manifest = FIXTURES / "synthetic-gps" / "assets-manifest.json"
    if not manifest.is_file():
        return
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    assets = raw["assets"] if isinstance(raw, dict) and "assets" in raw else raw
    segs, _meta = detect_geo_events(assets)
    golden_path = FIXTURES / "synthetic-gps" / "segments-golden.json"
    if not golden_path.is_file():
        assert len(segs) >= 1
        return
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert len(segs) == len(golden)
