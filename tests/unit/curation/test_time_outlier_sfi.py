"""SFI W1 · BE-SFI-07/08 time outlier + merge hard assert."""

from __future__ import annotations

from travelogue.curation.bucket_planning import (
    bucket_day_span,
    merge_small_buckets_with_segments,
)
from travelogue.curation.time_outlier import (
    apply_time_outlier_marks,
    detect_time_outlier_ids,
)
from travelogue.render.moment_exif import format_moment_exif_line


def test_detect_outlier_far_from_core() -> None:
    assets = []
    for i, day in enumerate(
        ["2024-05-01", "2024-05-02", "2024-05-03", "2024-05-04", "2024-05-05", "2020-11-30"]
    ):
        assets.append(
            {
                "id": f"a{i}",
                "takenAt": f"{day}T12:00:00Z",
                "layoutEligible": True,
            }
        )
    ids = detect_time_outlier_ids(assets, segments_count=1)
    assert "a5" in ids


def test_multi_segment_skips_auto_isolation() -> None:
    assets = [
        {"id": "a", "takenAt": "2020-01-01T12:00:00Z", "layoutEligible": True},
        {"id": "b", "takenAt": "2024-05-01T12:00:00Z", "layoutEligible": True},
        {"id": "c", "takenAt": "2024-05-02T12:00:00Z", "layoutEligible": True},
        {"id": "d", "takenAt": "2024-05-03T12:00:00Z", "layoutEligible": True},
    ]
    assert detect_time_outlier_ids(assets, segments_count=2) == []


def test_merge_refuses_cross_gap_small_bucket() -> None:
    assets_by_id = {
        "a": {"id": "a", "takenAt": "2024-05-01T12:00:00Z"},
        "b": {"id": "b", "takenAt": "2024-05-01T13:00:00Z"},
        "c": {"id": "c", "takenAt": "2024-05-01T14:00:00Z"},
        "x": {"id": "x", "takenAt": "2020-11-30T12:00:00Z"},
        "d": {"id": "d", "takenAt": "2024-05-03T12:00:00Z"},
        "e": {"id": "e", "takenAt": "2024-05-03T13:00:00Z"},
        "f": {"id": "f", "takenAt": "2024-05-03T14:00:00Z"},
    }
    buckets = [["a", "b", "c"], ["x"], ["d", "e", "f"]]
    segs = ["s1", "s2", "s3"]
    out, _, _ = merge_small_buckets_with_segments(
        buckets,
        segs,
        min_size=3,
        assets_by_id=assets_by_id,
        gap_days=14,
    )
    # Outlier singleton must not be swallowed
    assert any(b == ["x"] or "x" in b and len(b) == 1 for b in out) or any(
        "x" in b and set(b) == {"x"} for b in out
    )
    flat = [aid for b in out for aid in b]
    assert flat.count("x") == 1
    # Neighbor chapters stay separate from the 2020 singleton
    assert not any({"a", "x"}.issubset(set(b)) for b in out)
    assert not any({"d", "x"}.issubset(set(b)) for b in out)


def test_bucket_day_span_excludes_outlier() -> None:
    assets_by_id = {
        "a": {"id": "a", "takenAt": "2024-05-01T12:00:00Z"},
        "x": {"id": "x", "takenAt": "2020-11-30T12:00:00Z", "timeOutlier": True},
    }
    span = bucket_day_span(["a", "x"], assets_by_id)
    assert span == ["2024-05-01"]


def test_moment_exif_low_confidence_suppresses_year() -> None:
    line = format_moment_exif_line(
        {
            "takenAt": "2015-07-08T12:00:00Z",
            "dateConfidence": "low",
            "place": {"city": "武汉"},
        }
    )
    assert line is not None
    assert "2015" not in line
    assert "武汉" in line


def test_moment_exif_day_span_contradiction_suppresses_year() -> None:
    """D-SFI-06 · 图注日期与章 daySpan 矛盾时同样抑年。"""
    line = format_moment_exif_line(
        {
            "takenAt": "2015-07-08T15:00:00Z",
            "dateConfidence": "high",
            "place": {"city": "武汉"},
        },
        day_span=["2024-05-01", "2024-05-02"],
    )
    assert line is not None
    assert "2015" not in line
    assert "武汉" in line
    ok = format_moment_exif_line(
        {
            "takenAt": "2024-05-01T15:00:00Z",
            "dateConfidence": "high",
            "place": {"city": "武汉"},
        },
        day_span=["2024-05-01", "2024-05-02"],
    )
    assert ok is not None
    assert "2024" in ok


def test_apply_marks_writes_curation() -> None:
    trip = {
        "assets": [
            {"id": f"a{i}", "takenAt": f"2024-05-0{i+1}T12:00:00Z", "layoutEligible": True}
            for i in range(5)
        ]
        + [{"id": "old", "takenAt": "2018-01-01T12:00:00Z", "layoutEligible": True}],
        "curation": {},
    }
    ids = apply_time_outlier_marks(trip, segments_count=1)
    assert "old" in ids
    assert trip["assets"][-1]["timeOutlier"] is True
    assert "old" in trip["curation"]["excludedTimeOutlierAssetIds"]


def test_peel_and_appendix_title() -> None:
    from travelogue.curation.time_outlier import (
        appendix_title,
        peel_time_outliers_from_buckets,
    )

    assets_by_id = {
        "a": {"id": "a", "timeOutlier": False},
        "x": {"id": "x", "timeOutlier": True},
        "y": {"id": "y", "timeOutlier": True},
    }
    cleaned, outliers = peel_time_outliers_from_buckets(
        [["a", "x"], ["y"]], assets_by_id
    )
    assert cleaned == [["a"]]
    assert outliers == ["x", "y"]
    assert appendix_title(2) == "往年 · 旧照 · 2 张"


def test_exempt_skips_redetect() -> None:
    assets = [
        {"id": f"a{i}", "takenAt": f"2024-05-0{i+1}T12:00:00Z", "layoutEligible": True}
        for i in range(5)
    ] + [
        {
            "id": "old",
            "takenAt": "2018-01-01T12:00:00Z",
            "layoutEligible": True,
            "timeOutlierExempt": True,
        }
    ]
    assert detect_time_outlier_ids(assets, segments_count=1) == []
