"""Beam consecutive-pattern soft fallback telemetry (M6)."""

from __future__ import annotations

from tests._golden.helpers import build_portrait_heavy_trip, plan_legacy_screens
from travelogue.curation.degradation import assess_degradation
from travelogue.curation.layout_scoring import PHASE2_WEIGHTS
from travelogue.layout_engine.decision_log import ingest_beam_logs
from travelogue.layout_engine.planner.layout_search import maybe_replan_chapters


def _screen(pid: str, aid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": aid}]}


def _beam_picks(logs: list[dict]) -> list[dict]:
    picks: list[dict] = []
    for entry in logs:
        for event in entry.get("events") or []:
            if event.get("type") == "beam_pick":
                picks.append(event)
    return picks


def test_consecutive_bypass_sets_fallback_telemetry(monkeypatch) -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    violating = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-1", "a2"),
        _screen("screen-portrait-1", "a3"),
    ]

    def _fake_candidates(*_args, **_kwargs):
        return [("violating", violating)]

    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_search.generate_day_bucket_candidates",
        _fake_candidates,
    )
    _, meta = maybe_replan_chapters(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
        max_consecutive_same_pattern=2,
    )
    picks = _beam_picks(meta.get("decisionLogs") or [])
    assert picks
    pick = picks[0]
    assert pick["fallbackUsed"] is True
    assert pick["fallbackReason"] == "CONSECUTIVE_PATTERN_UNSATISFIABLE"
    assert pick["consecutivePatternFilterBypassed"] is True
    assert pick["filteredCandidateCount"] == 0
    assert pick["maxConsecutiveStreak"] == 2


def test_consecutive_filter_satisfied_no_fallback(monkeypatch) -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    ok = [
        _screen("screen-portrait-1", "a1"),
        _screen("screen-portrait-2", "a2"),
        _screen("screen-portrait-3", "a3"),
    ]

    def _fake_candidates(*_args, **_kwargs):
        return [("ok", ok)]

    monkeypatch.setattr(
        "travelogue.layout_engine.planner.layout_search.generate_day_bucket_candidates",
        _fake_candidates,
    )
    _, meta = maybe_replan_chapters(
        legacy,
        buckets=buckets,
        aspects=aspects,  # type: ignore[arg-type]
        assets=assets,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=assess_degradation(assets, aspects, min_layout_eligible=3),
        orientation_summary={"portrait": 6, "landscape": 0},
        trip_photo_total=len(assets),
        max_consecutive_same_pattern=2,
    )
    pick = _beam_picks(meta.get("decisionLogs") or [])[0]
    assert pick["fallbackUsed"] is False
    assert pick["fallbackReason"] is None
    assert pick["consecutivePatternFilterBypassed"] is False
    assert pick["filteredCandidateCount"] == 1
    assert pick["maxConsecutiveStreak"] is None


def test_ingest_beam_logs_projects_consecutive_fallback_meta() -> None:
    logs = [
        {
            "chapterId": "day-bucket-1",
            "events": [
                {
                    "type": "beam_pick",
                    "variant": "legacy",
                    "plannerPath": "beam",
                    "score": {"total": 0.5},
                    "candidateCount": 2,
                    "fallbackUsed": True,
                    "fallbackReason": "CONSECUTIVE_PATTERN_UNSATISFIABLE",
                    "consecutivePatternFilterBypassed": True,
                    "filteredCandidateCount": 0,
                    "maxConsecutiveStreak": 2,
                }
            ],
        }
    ]
    events = ingest_beam_logs(logs)
    meta = events[0]["meta"]
    assert meta["fallbackUsed"] is True
    assert meta["fallbackReason"] == "CONSECUTIVE_PATTERN_UNSATISFIABLE"
    assert meta["consecutivePatternFilterBypassed"] is True
    assert meta["filteredCandidateCount"] == 0
    assert meta["maxConsecutiveStreak"] == 2
