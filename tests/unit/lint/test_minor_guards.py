"""Guards for rank_screens tie-break and cover_candidates featured backfill."""

from __future__ import annotations

from unittest.mock import patch

from travelogue.curation.curate_scoring import cover_candidates
from travelogue.curation.layout_scoring import ScoreBreakdown, rank_screens


def test_rank_screens_tie_break_uses_input_order_not_dict_equality() -> None:
    first = {"patternId": "screen-landscape-3", "slots": [{"assetId": "a1", "slot": 0}]}
    second = {"patternId": "screen-landscape-3", "slots": [{"assetId": "a2", "slot": 0}]}
    screens = [first, second]
    tie = ScoreBreakdown(total=0.5)

    with patch(
        "travelogue.curation.layout_scoring.score_screen",
        side_effect=[tie, tie],
    ):
        ranked = rank_screens(
            screens,
            aspects={},
            assets_by_id={},
            weights=__import__("travelogue.curation.layout_scoring", fromlist=["ScoringWeights"]).ScoringWeights(),
        )

    assert [s for s, _ in ranked] == [first, second]


def test_cover_candidates_featured_backfill_replaces_tail_without_duplicate() -> None:
    assets = [
        {
            "id": "cover",
            "type": "image",
            "userTier": "featured",
            "width": 3000,
            "height": 2000,
            "takenAt": "2025-06-01T10:00:00Z",
            "quality": {"sharpness": 0.9},
        },
        {
            "id": "alt-1",
            "type": "image",
            "width": 3000,
            "height": 2000,
            "takenAt": "2025-06-02T10:00:00Z",
            "quality": {"sharpness": 0.8},
        },
        {
            "id": "alt-2",
            "type": "image",
            "width": 3000,
            "height": 2000,
            "takenAt": "2025-06-03T10:00:00Z",
            "quality": {"sharpness": 0.7},
        },
        {
            "id": "feat-2",
            "type": "image",
            "userTier": "featured",
            "width": 3000,
            "height": 2000,
            "takenAt": "2025-06-04T10:00:00Z",
            "quality": {"sharpness": 0.95},
        },
        {
            "id": "feat-3",
            "type": "image",
            "userTier": "featured",
            "width": 3000,
            "height": 2000,
            "takenAt": "2025-06-05T10:00:00Z",
            "quality": {"sharpness": 0.85},
        },
    ]
    out = cover_candidates(
        assets,
        "cover",
        export_layout="web",
        limit=3,
        featured_min=3,
        enable_phase6_cover_factors=False,
    )
    assert len(out) == 3
    assert len(set(out)) == 3
    assert out[0] == "cover"
    assert out.count("cover") == 1
    assert "feat-2" in out or "feat-3" in out
