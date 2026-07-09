"""Curate threshold constants and small-album chapter caps (P5-C3)."""

from __future__ import annotations

from datetime import date

import pytest

from travelogue.curation.bucket_planning import normalize_bucket_counts
from travelogue.curation.curate import CurateError, _date_span_warning, run_curate
from travelogue.curation.curate_limits import (
    COMPACT_ALBUM_PHOTO_CAP,
    MIN_CURATE_ASSETS,
    SEGMENT_LABEL_PREVIEW_LIMIT,
    SMALL_ALBUM_PHOTO_CAP,
)


def _asset(aid: str, day: int = 1) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": 1600,
        "height": 900,
        "aspectKind": "landscape",
        "takenAt": f"2025-04-{day:02d}T12:00:00Z",
        "layoutEligible": True,
    }


def _trip_with_assets(n: int) -> dict:
    return {
        "tripId": "limits-test",
        "assets": [_asset(f"a{i}", day=(i % 5) + 1) for i in range(n)],
        "meta": {"title": "test", "place": "test"},
        "pipeline": {"status": "ingest_ready"},
    }


def test_curate_limits_constants() -> None:
    assert MIN_CURATE_ASSETS == 4
    assert SMALL_ALBUM_PHOTO_CAP == 15
    assert COMPACT_ALBUM_PHOTO_CAP == 8
    assert SEGMENT_LABEL_PREVIEW_LIMIT == 4


def test_run_curate_rejects_below_min_assets() -> None:
    trip = _trip_with_assets(MIN_CURATE_ASSETS - 1)
    with pytest.raises(CurateError) as exc:
        run_curate(trip, export_layout="mobile", apply_layout=False)
    assert exc.value.code == "E_CURATE_TOO_FEW"


def test_small_album_caps_chapters_at_three() -> None:
    trip = _trip_with_assets(SMALL_ALBUM_PHOTO_CAP)
    run_curate(trip, export_layout="mobile", apply_layout=False)
    assert len(trip["chapters"]) <= 3


def test_compact_album_bucket_cap_merges_to_two() -> None:
    buckets = [[f"a{i}"] for i in range(COMPACT_ALBUM_PHOTO_CAP)]
    norm = normalize_bucket_counts(
        buckets,
        None,
        max_chapters=2,
        min_chapters=1,
        min_bucket_size=2,
    )
    assert len(norm.buckets) <= 2


def test_small_album_curate_fewer_chapters_than_large_album() -> None:
    small = _trip_with_assets(SMALL_ALBUM_PHOTO_CAP)
    run_curate(small, export_layout="mobile", apply_layout=False)
    large = _trip_with_assets(24)
    for i, a in enumerate(large["assets"]):
        a["takenAt"] = f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T12:00:00Z"
    run_curate(large, export_layout="mobile", apply_layout=False)
    assert len(small["chapters"]) <= len(large["chapters"])


def test_segment_label_preview_truncates() -> None:
    from travelogue.curation.time_segments import TimeSegment

    segments = [
        TimeSegment(
            id=f"s{i}",
            label=f"段{i}",
            date_start=date(2025, 4, i),
            date_end=date(2025, 4, i),
            asset_ids=[f"a{i}"],
        )
        for i in range(1, 7)
    ]
    msg = _date_span_warning([], segments=segments)
    assert msg is not None
    assert f"等{len(segments)}段" in msg
    assert "段5" not in msg
