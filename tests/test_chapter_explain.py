"""M14 · chapter explain + trip migration."""

from __future__ import annotations

from travelogue.curation.chapter_explain import (
    attach_chapter_explain,
    build_chapter_explain,
    build_layout_explain,
)
from travelogue.curation.trip_migration import strip_legacy_curation_fields


def test_build_chapter_explain_geo_segments() -> None:
    trip = {
        "chapters": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}],
        "curation": {
            "clustering": {
                "segmentMode": "geo_event",
                "segments": [
                    {"name": "东京", "assetIds": ["a1"]},
                    {"name": "京都", "assetIds": ["a2"]},
                ],
            }
        },
    }
    out = build_chapter_explain(trip)
    assert "2 段行程" in out["summary"]
    assert "东京" in out["summary"]
    assert out["chapterCount"] == 3


def test_build_chapter_explain_date_fallback() -> None:
    trip = {
        "chapters": [{"id": "c1"}],
        "curation": {"clustering": {"segmentMode": "date_fallback", "segments": []}},
    }
    out = build_chapter_explain(trip)
    assert "按日期" in out["summary"]
    assert any("缺少位置" in d for d in out["details"])


def test_attach_chapter_explain_writes_user_summary() -> None:
    trip = {
        "chapters": [{"id": "c1"}],
        "curation": {"clustering": {"segmentMode": "date_fallback"}},
    }
    attach_chapter_explain(trip)
    summary = trip["curation"]["clustering"]["userSummary"]
    assert summary["summary"]


def test_strip_legacy_insights() -> None:
    trip = {"curation": {"insights": {"old": True}, "clustering": {}}}
    strip_legacy_curation_fields(trip)
    assert "insights" not in trip["curation"]
    assert "clustering" in trip["curation"]


def test_build_layout_explain_degraded() -> None:
    out = build_layout_explain({"degradationReason": "insufficient_layout_eligible"})
    assert out is not None
    assert out["mode"] == "degraded"
    assert "经典排版" in out["summary"]
    assert any("较少" in line for line in out["details"])


def test_build_layout_explain_beam_pick() -> None:
    curation = {
        "layoutDecisionLog": [
            {
                "chapterId": "day-bucket-1",
                "events": [
                    {
                        "type": "beam_pick",
                        "variant": "with_hero",
                        "candidateCount": 4,
                        "changed": True,
                        "score": {
                            "total": 0.82,
                            "layout_rhythm": 0.9,
                            "diversity": 0.7,
                            "aspect_match": 0.5,
                        },
                    }
                ],
            }
        ],
        "layoutSearchBudget": {"evaluations": 12},
    }
    out = build_layout_explain(curation)
    assert out is not None
    assert out["mode"] == "beam"
    assert "优化了 1 处屏序" in out["summary"]
    assert any("版面节奏" in line for line in out["details"])
    assert any("12" in line for line in out["details"])


def test_build_layout_explain_none_for_legacy() -> None:
    assert build_layout_explain({}) is None
    assert build_layout_explain({"clustering": {}}) is None


def test_build_chapter_explain_includes_layout_explain() -> None:
    trip = {
        "chapters": [{"id": "c1"}],
        "curation": {
            "clustering": {"segmentMode": "date_fallback", "segments": []},
            "degradationReason": "insufficient_aspect_diversity",
        },
    }
    out = build_chapter_explain(trip)
    assert out["layoutExplain"] is not None
    assert out["layoutExplain"]["mode"] == "degraded"
