"""PIS W2 · 作品集辑封默认只写张数（assemble S-04 覆盖）。"""

from __future__ import annotations

from travelogue.render.portfolio_chapters import overlay_portfolio_epilogue_stats


def test_overlay_keeps_photo_count_drops_days() -> None:
    out = overlay_portfolio_epilogue_stats(
        {},
        {"photoCount": 88, "daySpan": 4, "summaryLine": "88 张照片 · 4 天"},
    )
    assert out["summaryLine"] == "88 张照片"
    assert "天" not in out["summaryLine"]
    assert out["daySpan"] == 4


def test_overlay_prefers_photos_placed() -> None:
    out = overlay_portfolio_epilogue_stats(
        {"studio": {"portfolio": {"photosPlaced": 77}}},
        {"photoCount": 80, "daySpan": 1},
    )
    assert out["summaryLine"] == "77 张照片"


def test_zhuhai_span_must_not_collapse_to_one_day() -> None:
    """珠海 meta 跨日；禁止夹名/闭区间把 daySpan 改成 1。"""
    shared = {"photoCount": 88, "daySpan": 4, "summaryLine": "88 张照片 · 4 天"}
    out = overlay_portfolio_epilogue_stats(
        {
            "meta": {"dateStart": "2025-04-20", "dateEnd": "2025-04-23", "title": "珠海东澳岛一日游"},
        },
        shared,
    )
    assert out["daySpan"] == 4
    assert "1 天" not in out["summaryLine"]
    assert "4 天" not in out["summaryLine"]
    assert out["summaryLine"] == "88 张照片"
