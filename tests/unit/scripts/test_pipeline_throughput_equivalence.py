"""Live L-struct equivalence helper tests."""

from __future__ import annotations

from scripts.pipeline_throughput_equivalence_check import compare_structure, structure_fingerprint


def test_structure_fingerprint_stable() -> None:
    trip = {
        "coverAssetId": "asset-001",
        "assets": [
            {
                "id": "asset-001",
                "takenAt": "2025-01-01T00:00:00Z",
                "burstGroupId": "burst-001",
                "dedupeGroupId": "dhash:abc",
                "contentSig": "1:x",
            }
        ],
        "chapters": [{"id": "ch-01"}],
        "curation": {"excludedLowResAssetIds": []},
    }
    fp = structure_fingerprint(trip)
    assert fp["assetIds"] == ["asset-001"]
    assert fp["chapterIds"] == ["ch-01"]


def test_compare_structure_detects_mismatch() -> None:
    a = {"assets": [{"id": "asset-001", "takenAt": "t1"}], "chapters": []}
    b = {"assets": [{"id": "asset-002", "takenAt": "t1"}], "chapters": []}
    result = compare_structure(a, b)
    assert result["matched"] is False
    assert result["structure_hash_rate_fixed"] == 0.0
    assert "assetIds" in result["mismatchedKeys"]


def test_compare_structure_match() -> None:
    trip = {
        "assets": [{"id": "a", "takenAt": "t", "burstGroupId": None, "dedupeGroupId": "d", "contentSig": "s"}],
        "chapters": [{"id": "c"}],
        "coverAssetId": "a",
        "curation": {},
    }
    result = compare_structure(trip, trip)
    assert result["matched"] is True
    assert result["structure_hash_rate_fixed"] == 1.0
