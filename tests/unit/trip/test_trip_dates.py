"""Trip meta date range (multi-year albums)."""

from __future__ import annotations

from travelogue.media.trip_dates import apply_meta_dates_from_assets, trip_meta_date_range


def test_meta_range_spans_years_not_single_day() -> None:
    assets = [
        {"takenAt": "2010-03-01T00:00:00Z", "dateSource": "exif", "dateConfidence": "high"},
        {"takenAt": "2024-10-30T00:00:00Z", "dateSource": "exif", "dateConfidence": "high"},
        {"takenAt": "2026-05-21T00:00:00Z", "dateSource": "mtime", "dateConfidence": "low"},
    ]
    d0, d1 = trip_meta_date_range(assets)
    assert d0 is not None and d1 is not None
    assert d0.year == 2010
    assert d1.year >= 2024

    trip = {"meta": {"title": "t", "places": ["x"], "tone": "relaxed"}, "assets": assets}
    apply_meta_dates_from_assets(trip)
    assert trip["meta"]["dateStart"] == "2010-03-01"
    assert trip["meta"]["dateEnd"] in ("2026-05-21", "2024-10-30")
