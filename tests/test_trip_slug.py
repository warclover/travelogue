"""tripId slug helpers."""

from pathlib import Path

from travelogue.util.trip_slug import demo_trip_id_from_album, normalize_trip_id


def test_normalize_trip_id_ascii():
    assert normalize_trip_id("demo-kyoto-2025") == "demo-kyoto-2025"


def test_normalize_trip_id_cjk_fallback():
    tid = normalize_trip_id("雨后京都", fallback_seed="雨后京都")
    assert tid.startswith("demo-")
    assert tid == tid.lower()
    assert "-" not in tid or tid.replace("-", "").isalnum()


def test_demo_trip_id_from_album_folder():
    tid = demo_trip_id_from_album(
        Path("D:/Photos/kyoto-2025"),
        title="雨后京都",
        place="京都",
    )
    assert tid == "kyoto-2025"


def test_demo_trip_id_explicit():
    tid = demo_trip_id_from_album(
        Path("album"),
        title="x",
        place="y",
        explicit="my-trip",
    )
    assert tid == "my-trip"
