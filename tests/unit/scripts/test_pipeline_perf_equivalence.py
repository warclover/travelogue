"""AC-PPF-07a · fingerprint helpers + light E-A self-check."""

from __future__ import annotations

from pathlib import Path

from scripts.pipeline_perf_equivalence_check import (
    diff_fingerprints,
    ea_fingerprint,
    run_self_check,
)


def test_ea_fingerprint_stable_keys() -> None:
    trip = {
        "coverAssetId": "a1",
        "curation": {"closingAssetId": "z9"},
        "assets": [
            {
                "id": "a1",
                "contentSig": "sig",
                "mediaClass": "photo",
                "layoutEligible": True,
                "quality": {
                    "aesthetic": {
                        "overall": 0.7,
                        "signals": {"learnedAesthetic": 0.8, "learnedMetric": "nima"},
                    }
                },
            }
        ],
        "chapters": [
            {
                "id": "c1",
                "items": [{"assetId": "a1"}],
                "screens": [{"patternId": "single", "slots": [{"assetId": "a1"}]}],
            }
        ],
    }
    fp = ea_fingerprint(trip)
    assert fp["coverAssetId"] == "a1"
    assert fp["closingAssetId"] == "z9"
    assert fp["assets"][0]["learnedAesthetic"] == 0.8
    assert fp["chapters"][0]["screens"][0]["assetIds"] == ["a1"]


def test_diff_fingerprints_reports_change() -> None:
    a = {"coverAssetId": "x", "assets": []}
    b = {"coverAssetId": "y", "assets": []}
    diffs = diff_fingerprints(a, b)
    assert any("coverAssetId" in d for d in diffs)


def test_ea_self_check_deferred_parity(tmp_path: Path) -> None:
    report = run_self_check(tmp_path)
    assert report.ok, report.diffs[:20]
