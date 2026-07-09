"""PRD §7.1 mosaic win score percentiles."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.metrics import (
    compute_mosaic_metrics,
    mosaic_win_score_percentiles,
)


def test_win_score_percentiles():
    logs = [
        {"winnerScore": 0.4, "fallbackUsed": False},
        {"winnerScore": 0.6, "fallbackUsed": False},
        {"winnerScore": 0.8, "fallbackUsed": False},
        {"winnerScore": 0.1, "fallbackUsed": True},
    ]
    p = mosaic_win_score_percentiles(logs)
    assert p["layout.mosaic5.win_score_p50"] == 0.6
    assert p["layout.mosaic5.win_score_p90"] == 0.8


def test_compute_mosaic_metrics_includes_percentiles():
    ch = [{"screens": [{"patternId": "screen-mosaic-5-main-portrait-3land"}]}]
    logs = [{"winnerScore": 0.5, "fallbackUsed": False}]
    m = compute_mosaic_metrics(ch, mosaic_logs=logs)
    assert m["layout.mosaic5.win_score_p50"] == 0.5
