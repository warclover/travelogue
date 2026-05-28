"""M14 · chapter explain + trip migration."""

from __future__ import annotations

from travelogue.curation.chapter_explain import attach_chapter_explain, build_chapter_explain
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
