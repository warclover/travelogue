"""ALG-V3 W3-C4 · VC-04 patternId streak telemetry (PL-VC04)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.curation.algo_v3_summary import build_algo_v3_summary
from travelogue.curation.layout_constraints import (
    DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
    max_consecutive_pattern_streak,
)


def _screen(pid: str, aid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": aid}]}


def test_max_consecutive_pattern_streak_counts_pattern_id() -> None:
    screens = [
        _screen("screen-a", "1"),
        _screen("screen-a", "2"),
        _screen("screen-a", "3"),
        _screen("screen-b", "4"),
    ]
    assert max_consecutive_pattern_streak(screens) == 3


def test_algo_v3_rhythm_uses_pattern_id_unit(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    trip = {
        "assets": [],
        "chapters": [
            {
                "id": "c1",
                "screens": [
                    _screen("screen-x", "a"),
                    _screen("screen-x", "b"),
                    _screen("screen-y", "c"),
                ],
            }
        ],
        "curation": {},
    }
    summary = build_algo_v3_summary(trip, cfg=AppConfig(llm=LlmConfig(capability="auto")))
    rhythm = summary["rhythm"]
    assert rhythm["vc04Unit"] == "patternId"
    assert rhythm["maxConsecutiveSamePattern"] == DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN
    assert rhythm["maxPatternIdStreakObserved"] == 2
