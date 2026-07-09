"""Unit tests for cluster_eval."""

from __future__ import annotations

from travelogue.curation.cluster_eval import geo_segment_agreement_rate


def test_geo_segment_agreement_perfect() -> None:
    golden = [{"assetIds": ["a", "b", "c"]}]
    detected = [{"assetIds": ["a", "b", "c"]}]
    assert geo_segment_agreement_rate(golden, detected) == 1.0


def test_geo_segment_agreement_partial() -> None:
    golden = [
        {"assetIds": ["a", "b"]},
        {"assetIds": ["c", "d"]},
    ]
    detected = [
        {"assetIds": ["a", "b"]},
        {"assetIds": ["c", "d", "e"]},
    ]
    # {c,d} vs {c,d,e} Jaccard = 2/3 < 0.7 → only first golden segment matches
    rate = geo_segment_agreement_rate(golden, detected, threshold=0.7)
    assert rate == 0.5


def test_geo_segment_agreement_with_lower_threshold() -> None:
    golden = [{"assetIds": ["c", "d"]}]
    detected = [{"assetIds": ["c", "d", "e"]}]
    assert geo_segment_agreement_rate(golden, detected, threshold=0.65) == 1.0


def test_geo_segment_agreement_zero_when_no_algo() -> None:
    assert geo_segment_agreement_rate([{"assetIds": ["a"]}], []) == 0.0
