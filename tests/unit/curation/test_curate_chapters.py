"""Curate v2: day buckets, merge small chapters, title suffixes."""

from __future__ import annotations

from travelogue.curation.curate import (
    _chapter_titles,
    _group_assets_by_day,
    _merge_small_buckets,
    _normalize_bucket_counts,
    _title_for_bucket_span,
    run_curate,
)
from travelogue.services.manifest_limits import chapter_limits


def _assets_for_days(days: list[str], *, prefix: str = "a") -> list[dict]:
    out: list[dict] = []
    for i, day in enumerate(days):
        out.append(
            {
                "id": f"{prefix}{i}",
                "type": "image",
                "width": 1200,
                "height": 800,
                "takenAt": f"{day}T12:00:00Z",
            }
        )
    return out


def test_cap_book_buckets_limits_multi_segment_chapters() -> None:
    buckets = [[f"a{i}"] for i in range(11)]
    seg_ids = ["seg-01"] * 3 + ["seg-02"] * 2 + ["seg-03"] * 1 + ["seg-04"] * 3 + ["seg-05"] * 2
    norm = _normalize_bucket_counts(buckets, seg_ids)
    min_c, max_c = chapter_limits()
    assert min_c <= len(norm.buckets) <= max_c
    assert len(norm.primary_segment_ids) == len(norm.buckets)
    assert len(norm.segment_ids_per_bucket) == len(norm.buckets)
    assert sum(len(b) for b in norm.buckets) == 11


def test_normalize_primary_segment_by_asset_weight() -> None:
    norm = _normalize_bucket_counts(
        [["a1", "a2", "a3"], ["b1"]],
        ["seg-a", "seg-b"],
    )
    assert norm.primary_segment_ids[0] == "seg-a"


def test_chapter_title_cross_year_span() -> None:
    title = _title_for_bucket_span(["2010-07-11", "2026-05-20"])
    assert title == "2010–2026"


def test_chapter_titles_cross_year_in_bucket() -> None:
    assets = [
        {"id": "o", "takenAt": "2010-07-11T12:00:00Z"},
        {"id": "n", "takenAt": "2026-05-20T12:00:00Z"},
    ]
    titles = _chapter_titles([["o", "n"]], assets, {"places": ["京都"]})
    assert titles[0].startswith("京都")


def test_chapter_titles_cross_year_trip_prefixes_year() -> None:
    """D-SFP-08② · 跨年混拍册单日章名带年份。"""
    assets = [
        {"id": "a", "takenAt": "2024-08-14T12:00:00Z"},
        {"id": "b", "takenAt": "2025-01-16T12:00:00Z"},
    ]
    titles = _chapter_titles(
        [["a"], ["b"]],
        assets,
        {
            "places": ["武汉"],
            "dateStart": "2024-01-20",
            "dateEnd": "2025-01-16",
        },
    )
    assert titles[0].startswith("武汉")
    assert titles[1].startswith("第二程") or titles[1].startswith("武汉")
    assert all("·二" not in t and "·三" not in t for t in titles)


def test_merge_small_buckets_combines_pairs() -> None:
    buckets = [["a", "b", "c"], ["d"], ["e", "f", "g"]]
    merged = _merge_small_buckets(buckets, min_size=3)
    assert len(merged) == 2
    assert all(len(b) >= 3 for b in merged)
    assert sorted(merged[0] + merged[1]) == ["a", "b", "c", "d", "e", "f", "g"]


def test_chapter_balance_merges_sparse_travel_days() -> None:
    """Sparse day buckets merge into neighbors when below adaptive threshold."""
    from travelogue.curation.bucket_planning import normalize_bucket_counts

    # 4 sparse travel days + 1 heavy day → balance merges d1–d4 into fewer chapters
    buckets = [["a1"], ["a2"], ["a3"], ["a4"], ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]]
    norm = normalize_bucket_counts(
        buckets,
        None,
        min_bucket_size=3,
        chapter_balance_enabled=True,
        chapter_balance_ratio=0.55,
    )
    assert len(norm.buckets) < len(buckets)
    assert sum(len(b) for b in norm.buckets) == 12
    assert max(len(b) for b in norm.buckets) - min(len(b) for b in norm.buckets) <= 8


def test_group_by_day_keeps_calendar_buckets_not_flatten_years() -> None:
    assets: list[dict] = []
    for day in ("2010-07-11", "2026-05-20"):
        for j in range(4):
            assets.append(
                {
                    "id": f"{day}-{j}",
                    "type": "image",
                    "width": 1200,
                    "height": 800,
                    "takenAt": f"{day}T{10 + j}:00:00Z",
                }
            )
    buckets = _group_assets_by_day(assets, cover_id="")
    assert len(buckets) >= 2
    years = set()
    for b in buckets:
        for aid in b:
            a = next(x for x in assets if x["id"] == aid)
            years.add(a["takenAt"][:4])
    assert "2010" in years
    assert "2026" in years


def test_chapter_titles_same_day_suffix() -> None:
    assets = _assets_for_days(["2025-04-02", "2025-04-02", "2025-04-03"], prefix="x")
    buckets = [["x0"], ["x1"], ["x2"]]
    titles = _chapter_titles(buckets, assets, {"places": ["京都"]})
    assert titles[0].startswith("京都")
    # SFP D-SFP-01：禁「日期续」/「（N）」/「·二」；同日后续用地点撞车后第N程
    assert "续" not in titles[1]
    assert "（" not in titles[1] and "）" not in titles[1]
    assert "·二" not in titles[1] and "·三" not in titles[1]
    assert titles[1].startswith("京都") or "程" in titles[1]


def test_chapter_titles_prefer_span_over_multi_seg_labels() -> None:
    """多日桶优先日期跨度，避免 label 硬截断出双间隔号。"""
    from travelogue.curation.chapter_titles import chapter_titles

    assets = [
        {"id": "a", "takenAt": "2024-02-09T12:00:00Z"},
        {"id": "b", "takenAt": "2024-02-12T12:00:00Z"},
        {"id": "c", "takenAt": "2024-04-04T12:00:00Z"},
    ]
    titles = chapter_titles(
        [["a", "b", "c"]],
        assets,
        {"places": ["旅途"]},
        bucket_segment_ids_all=[["s1", "s2"]],
        segment_labels={
            "s1": "2月9–12日·春游",
            "s2": "4月4日·清明",
        },
    )
    assert titles[0].startswith("第一程") or titles[0] == "2月9–4月4日"
    assert "··" not in titles[0]


def test_chapter_titles_clean_long_segment_label() -> None:
    from travelogue.curation.chapter_titles import chapter_titles

    assets = [{"id": "a", "takenAt": "2025-01-16T12:00:00Z"}]
    titles = chapter_titles(
        [["a"]],
        assets,
        {"places": ["旅途"]},
        bucket_segment_ids=["seg"],
        segment_labels={"seg": "1月16日·夏睿彤年度精选"},
    )
    # Album-marketing tails must not become scene shorts；无地点时用第N程
    assert "精选" not in titles[0]
    assert "夏睿彤" not in titles[0]
    assert titles[0].startswith("第一程") or titles[0].startswith("1月16日")


def test_run_curate_auto_attaches_screens() -> None:
    assets = _assets_for_days(
        ["2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04", "2025-04-05", "2025-04-06"]
    )
    trip = {
        "tripId": "auto-screens",
        "exportLayout": "auto",
        "meta": {"places": ["京都"], "title": "测试"},
        "assets": assets,
        "chapters": [],
        "pipeline": {},
    }
    run_curate(trip, export_layout="auto", layout_engine="screens")
    assert trip["exportLayout"] == "auto"
    assert any(ch.get("screens") for ch in trip["chapters"])
    assert all(ch.get("curation", {}).get("daySpan") for ch in trip["chapters"])
