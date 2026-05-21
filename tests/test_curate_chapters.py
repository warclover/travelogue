"""Curate v2: day buckets, merge small chapters, title suffixes."""

from __future__ import annotations

from travelogue.curation.curate import _chapter_titles, _group_assets_by_day, _merge_small_buckets, run_curate


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


def test_merge_small_buckets_combines_pairs() -> None:
    buckets = [["a", "b", "c"], ["d"], ["e", "f", "g"]]
    merged = _merge_small_buckets(buckets, min_size=3)
    assert len(merged) == 2
    assert all(len(b) >= 3 for b in merged)
    assert sorted(merged[0] + merged[1]) == ["a", "b", "c", "d", "e", "f", "g"]


def test_group_by_day_keeps_calendar_buckets_not_flatten_years() -> None:
    assets: list[dict] = []
    for day in ("2010-07-11", "2026-05-20"):
        for j in range(3):
            assets.append(
                {
                    "id": f"{day}-{j}",
                    "type": "image",
                    "width": 1200,
                    "height": 800,
                    "takenAt": f"{day}T{10 + j}:00:00Z",
                }
            )
    buckets = _group_assets_by_day(assets, cover_id=assets[0]["id"])
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
    assert titles[0].startswith("4月2日")
    assert "·二" in titles[1] or titles[1].endswith("·二")


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
