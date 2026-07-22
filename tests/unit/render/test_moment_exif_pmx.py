"""PMX · moment EXIF 硬闸：timeOutlier / daySpan 矛盾不得上绝对年。"""

from travelogue.render.moment_exif import format_moment_exif_line


def test_time_outlier_suppresses_absolute_date() -> None:
    line = format_moment_exif_line(
        {
            "takenAt": "2015-03-12T09:30:00",
            "timeOutlier": True,
            "place": {"city": "珞珈山"},
        }
    )
    assert line is not None
    assert "2015" not in line
    assert "2015.03" not in line
    assert "珞珈山" in line
    assert "上午" in line


def test_day_span_contradiction_suppresses_year() -> None:
    line = format_moment_exif_line(
        {
            "takenAt": "2015-03-12T15:00:00",
            "place": {"city": "珞珈山"},
            "dateConfidence": "high",
        },
        day_span=["2024-05-20", "2024-05-22"],
    )
    assert line is not None
    assert "2015" not in line
    assert "珞珈山" in line
