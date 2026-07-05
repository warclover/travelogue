"""T-LRG-03: LRG dogfood acceptance report (docs/PRD-LAYOUT-READER-REGRESSION-GUARD.md §3.3.4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lrg_dogfood_report import build_dogfood_report

_HTML = """
<html><body>
<section class="layout-screen" data-pattern="screen-landscape-1"></section>
<section class="breath-pause-screen"></section>
<section class="layout-screen" data-pattern="screen-portrait-2">
  <p class="moment-exif-bar">EXIF</p>
</section>
<section class="chapter-separator chapter-separator--ticket" data-block="chapter-separator"></section>
<section class="layout-screen" data-pattern="screen-landscape-4"></section>
</body></html>
"""


def _asset(aid: str, *, kind: str, taken_at: str) -> dict:
    return {"id": aid, "aspectKind": kind, "takenAt": taken_at}


def _trip_fixture() -> dict:
    assets = [
        _asset("a1", kind="portrait", taken_at="2026-01-01T00:00:00Z"),
        _asset("a2", kind="landscape", taken_at="2026-01-01T00:00:02Z"),
        _asset("a3", kind="landscape", taken_at="2026-01-01T00:00:04Z"),
        _asset("a4", kind="landscape", taken_at="2026-01-01T00:00:06Z"),
        _asset("a5", kind="landscape", taken_at="2026-01-01T00:00:08Z"),
    ]
    return {
        "tripId": "fixture-trip",
        "assets": assets,
        "curation": {
            "displayedAssetIds": [a["id"] for a in assets],
            "mosaicDecisionLog": [
                {"windowSize": 4, "winnerPatternId": "screen-landscape-4", "fallbackUsed": False},
                {"windowSize": 5, "winnerPatternId": None, "fallbackUsed": True},
            ],
        },
        "chapters": [
            {
                "screens": [
                    {"screenId": "s1", "patternId": "screen-landscape-1"},
                    {"screenId": "b1", "patternId": "screen-breath-pause"},
                    {"screenId": "s2", "patternId": "screen-portrait-2"},
                ]
            },
            {
                "screens": [
                    {"screenId": "s3", "patternId": "screen-landscape-4"},
                ]
            },
        ],
    }


@pytest.fixture
def trip_dir(tmp_path: Path) -> Path:
    """Isolated tmp_path trip dir — never touches real trips/*/trip.json."""
    d = tmp_path / "fixture-trip"
    d.mkdir()
    (d / "trip.json").write_text(json.dumps(_trip_fixture()), encoding="utf-8")
    (d / "index.html").write_text(_HTML, encoding="utf-8")
    return d


@pytest.mark.unit
def test_screen_count_excludes_breath_pause_and_matches_html(trip_dir: Path) -> None:
    report = build_dogfood_report(trip_dir, burst_seconds=900.0)
    assert report["tripId"] == "fixture-trip"
    # 3 layout-screen patternIds (landscape-1, portrait-2, landscape-4); breath-pause excluded.
    assert report["screenCount"] == 3
    assert report["htmlLayoutScreenCount"] == 3
    assert report["screenCount"] == report["htmlLayoutScreenCount"]
    assert report["warnings"] == []


@pytest.mark.unit
def test_pattern_histogram_includes_breath_pause(trip_dir: Path) -> None:
    report = build_dogfood_report(trip_dir, burst_seconds=900.0)
    assert report["patternHistogram"] == {
        "screen-breath-pause": 1,
        "screen-landscape-1": 1,
        "screen-landscape-4": 1,
        "screen-portrait-2": 1,
    }


@pytest.mark.unit
def test_moment_exif_and_ticket_counts_from_html(trip_dir: Path) -> None:
    report = build_dogfood_report(trip_dir, burst_seconds=900.0)
    assert report["momentExifBarCount"] == 1
    assert report["chapterSeparatorTicketCount"] == 1


@pytest.mark.unit
def test_mosaic_decision_summary_and_window_exposure(trip_dir: Path) -> None:
    report = build_dogfood_report(trip_dir, burst_seconds=900.0)
    assert report["mosaicDecisionSummary"]["4"] == {
        "decisions": 1,
        "success": 1,
        "fallback": 0,
        "patterns": ["screen-landscape-4"],
    }
    assert report["mosaicDecisionSummary"]["5"]["fallback"] == 1
    assert report["windowExposure"] == {"4": 1, "5": 1, "6": 0, "9": 0}


@pytest.mark.unit
def test_burst_pass_rate_for_1p4l_window(trip_dir: Path) -> None:
    """5-asset window is 1 portrait + 4 landscape, all within burst_seconds=900."""
    report = build_dogfood_report(trip_dir, burst_seconds=900.0)
    assert report["burstPassRateDetail"]["5"]["geometryWindows"] == 1
    assert report["burstPassRateDetail"]["5"]["burstPassWindows"] == 1
    assert report["burstPassRate"] == 1.0


@pytest.mark.unit
def test_burst_pass_rate_zero_when_window_too_slow(trip_dir: Path) -> None:
    report = build_dogfood_report(trip_dir, burst_seconds=1.0)
    assert report["burstPassRateDetail"]["5"]["burstPassWindows"] == 0
    assert report["burstPassRate"] == 0.0


@pytest.mark.unit
def test_missing_trip_json_degrades_gracefully(tmp_path: Path) -> None:
    """AC-LRG spirit: never fabricate data when trip.json is unavailable (e.g. gitignored)."""
    d = tmp_path / "no-source-trip"
    d.mkdir()
    (d / "index.html").write_text(_HTML, encoding="utf-8")

    report = build_dogfood_report(d)
    assert report["tripId"] == "no-source-trip"
    assert report["screenCount"] is None
    assert report["htmlLayoutScreenCount"] == 3
    assert report["burstPassRate"] is None
    assert any("trip.json not found" in w for w in report["warnings"])


@pytest.mark.unit
def test_missing_html_degrades_gracefully(tmp_path: Path) -> None:
    d = tmp_path / "no-render-trip"
    d.mkdir()
    (d / "trip.json").write_text(json.dumps(_trip_fixture()), encoding="utf-8")

    report = build_dogfood_report(d)
    assert report["htmlLayoutScreenCount"] is None
    assert report["screenCount"] == 3
    assert any("index.html not found" in w for w in report["warnings"])


@pytest.mark.unit
def test_screen_count_mismatch_produces_warning(tmp_path: Path) -> None:
    d = tmp_path / "mismatch-trip"
    d.mkdir()
    (d / "trip.json").write_text(json.dumps(_trip_fixture()), encoding="utf-8")
    # HTML with only 1 layout-screen while trip.json expects 3 (G-LRG-05 violation).
    (d / "index.html").write_text('<section class="layout-screen"></section>', encoding="utf-8")

    report = build_dogfood_report(d)
    assert report["screenCount"] == 3
    assert report["htmlLayoutScreenCount"] == 1
    assert any("screenCount" in w and "htmlLayoutScreenCount" in w for w in report["warnings"])
