"""M21 · Phase 5 Tier 1 differentiation tests."""

from __future__ import annotations

import copy

from travelogue.curation.breath_pauses import (
    insert_breath_screens_in_chapters,
    interleave_breath_items,
)
from travelogue.curation.longshot_filter import (
    chapters_for_longshot_render,
    select_longshot_screens,
)
from travelogue.render.context import build_epilogue_stats
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html


def _sample_screens(n: int) -> list[dict]:
    out = []
    for i in range(n):
        slots = [{"assetId": f"a{i}"}]
        if i % 3 == 2:
            slots = [{"assetId": f"a{i}-1"}, {"assetId": f"a{i}-2"}]
        out.append({"screenId": f"s{i}", "patternId": "screen-portrait-1", "slots": slots})
    return out


def test_longshot_filter_caps_screens():
    screens = _sample_screens(20)
    picked = select_longshot_screens(screens, max_screens=12)
    assert len(picked) <= 12
    assert picked[0]["screenId"] == "s0"


def test_longshot_filter_many_peak_screens_does_not_hang():
    """Gallery chapters may mark every screen as peak; must not trigger 2^n search."""
    import time

    screens = [
        {
            "screenId": f"s{i}",
            "patternId": "screen-portrait-1",
            "arcSegment": "peak",
            "slots": [{"assetId": f"a{i}"}],
        }
        for i in range(67)
    ]
    t0 = time.perf_counter()
    picked = select_longshot_screens(screens, max_screens=12, enable_mmr=False)
    elapsed = time.perf_counter() - t0
    assert len(picked) <= 12
    assert elapsed < 2.0


def test_longshot_filter_strips_breath_from_render():
    chapters = [
        {
            "id": "ch-1",
            "screens": _sample_screens(4)
            + [{"screenId": "b1", "patternId": "screen-breath-pause", "slots": []}],
        }
    ]
    filtered = chapters_for_longshot_render(chapters, max_screens=12)
    patterns = [sc["patternId"] for sc in filtered[0]["screens"]]
    assert "screen-breath-pause" not in patterns


def test_longshot_filter_uses_per_chapter_budget_not_global():
    """Short chapters must not be starved when another chapter has many screens."""

    def chapter(ch_id: str, n_content: int) -> dict:
        return {
            "id": ch_id,
            "screens": [
                {
                    "screenId": f"{ch_id}-s{i}",
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": f"{ch_id}-a{i}"}],
                }
                for i in range(n_content)
            ],
        }

    chapters = [chapter("c1", 22), chapter("c2", 6), chapter("c3", 14), chapter("c4", 29)]
    filtered = chapters_for_longshot_render(
        chapters,
        max_screens=12,
        enable_mmr=False,
        max_consecutive_same_pattern=99,
    )
    assert len(filtered[0]["screens"]) <= 12
    assert len(filtered[1]["screens"]) == 6
    assert len(filtered[2]["screens"]) <= 12
    assert len(filtered[3]["screens"]) <= 12


def test_insert_breath_screens_in_chapters():
    chapters = [{"id": "ch-1", "screens": _sample_screens(9)}]
    n = insert_breath_screens_in_chapters(chapters, interval=4)
    assert n >= 2
    assert any(sc.get("patternId") == "screen-breath-pause" for sc in chapters[0]["screens"])


def test_interleave_breath_items_for_longshot():
    items = [{"type": "media-card", "assetId": f"a{i}"} for i in range(9)]
    out = interleave_breath_items(items, interval=4)
    assert sum(1 for it in out if it.get("type") == "breath-pause") >= 2


def test_build_epilogue_stats_summary():
    trip = {
        "meta": {"place": "京都"},
        "assets": [{"id": "a1", "layoutEligible": True}, {"id": "a2", "layoutEligible": True}],
        "chapters": [
            {
                "curation": {
                    "daySpan": ["2024-04-01", "2024-04-02"],
                    "places": ["京都", "奈良"],
                }
            }
        ],
    }
    stats = build_epilogue_stats(trip)
    assert stats["photoCount"] == 2
    assert stats["dayCount"] == 2
    assert "2 天" in stats["summaryLine"]
    assert "张照片" in stats["summaryLine"]


def test_web_render_includes_chapter_separator_with_breath():
    trip = prepare_trip_web_screens(
        {
            "meta": {"title": "测试"},
            "assets": [{"id": "a1", "width": 1200, "height": 1600, "layoutEligible": True}],
            "chapters": [
                {
                    "id": "ch-01",
                    "index": 1,
                    "title": "第一日",
                    "screens": [
                        {
                            "screenId": "s1",
                            "patternId": "screen-portrait-1",
                            "slots": [{"assetId": "a1"}],
                        }
                    ],
                },
                {
                    "id": "ch-02",
                    "index": 2,
                    "title": "第二日",
                    "screens": [
                        {
                            "screenId": "s2",
                            "patternId": "screen-portrait-1",
                            "slots": [{"assetId": "a1"}],
                        }
                    ],
                },
            ],
        }
    )
    trip = copy.deepcopy(trip)
    trip.setdefault("export", {})["reading"] = {"profile": "default_hybrid"}
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
    )
    assert 'data-block="chapter-separator"' in html
    assert "第二日" in html


def test_longshot_render_includes_boundary_footer():
    trip = prepare_trip_web_screens(
        {
            "meta": {"title": "京都"},
            "assets": [{"id": "a1", "width": 1200, "height": 1600, "layoutEligible": True}],
            "chapters": [
                {
                    "id": "ch-01",
                    "index": 1,
                    "title": "第一日",
                    "screens": [
                        {
                            "screenId": "s1",
                            "patternId": "screen-portrait-1",
                            "slots": [{"assetId": "a1"}],
                        }
                    ],
                }
            ],
        }
    )
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="longshot",
    )
    assert 'data-block="longshot-boundary-footer"' in html
    assert "张照片" in html
