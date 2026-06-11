"""P19 screen sampler reproducibility."""

from __future__ import annotations

from travelogue.eval.screen_sampler import sample_screen_indices, screens_signature


def _chapters() -> list[dict]:
    return [
        {
            "id": "ch-1",
            "screens": [
                {"patternId": "screen-portrait-2", "slots": [{"assetId": "a1"}, {"assetId": "a2"}]},
                {"patternId": "screen-mosaic-5-2p3l-equal", "slots": [{"assetId": "b1"}]},
                {"patternId": "breath-pause", "slots": []},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "c1"}]},
            ],
        },
        {
            "id": "ch-2",
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "d1"}]},
            ],
        },
    ]


def test_screens_signature_stable() -> None:
    ch = _chapters()
    assert screens_signature(ch, trip_id="demo-2025") == screens_signature(ch, trip_id="demo-2025")


def test_sample_indices_reproducible_and_bounded() -> None:
    ch = _chapters()
    a = sample_screen_indices(ch, trip_id="demo-2025", max_screens=12)
    b = sample_screen_indices(ch, trip_id="demo-2025", max_screens=12)
    assert a == b
    assert len(a) <= 12
    assert all(0 <= i < 4 for i in a)
