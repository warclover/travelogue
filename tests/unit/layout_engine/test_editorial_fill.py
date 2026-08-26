"""MSP · fill groups (AC-MSP-19) and sparse detection (OQ-MSP-14)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from travelogue.layout_engine.editorial_series.fill import (
    fill_groups_from_assets,
    is_sparse_collection,
    pack_thin_fill_groups,
)

pytestmark = pytest.mark.unit

T0 = datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc)


def _asset(i: int, *, shot: str = "", minutes: int = 0, seg: str = "seg-01") -> dict:
    ts = T0 + timedelta(minutes=minutes)
    return {
        "id": f"a{i:03d}",
        "shotGroupId": shot,
        "shotGroupKind": "scene",
        "takenAt": ts.isoformat().replace("+00:00", "Z"),
        "_seg": seg,
    }


def _trip(assets: list[dict]) -> dict:
    by_seg: dict[str, list[str]] = {}
    for a in assets:
        by_seg.setdefault(a["_seg"], []).append(a["id"])
    return {
        "curation": {
            "segments": [
                {"id": sid, "assetIds": ids} for sid, ids in by_seg.items()
            ]
        }
    }


def test_keeps_existing_shot_groups_intact() -> None:
    assets = [
        _asset(1, shot="g-a", minutes=0),
        _asset(2, shot="g-a", minutes=1),
        _asset(3, shot="g-a", minutes=2),
        _asset(4, shot="", minutes=3),
    ]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert [g["id"] for g in groups][0] == "g-a"
    assert groups[0]["asset_ids"] == ["a001", "a002", "a003"]
    assert len(groups[1]["asset_ids"]) == 1


def test_does_not_merge_across_segments() -> None:
    assets = [
        _asset(1, minutes=0, seg="seg-a"),
        _asset(2, minutes=1, seg="seg-b"),
    ]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert len(groups) == 2


def test_does_not_merge_when_gap_over_10_min() -> None:
    assets = [_asset(1, minutes=0), _asset(2, minutes=11)]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert len(groups) == 2


def test_pack_thin_fill_groups_same_chapter() -> None:
    assets = [_asset(i, minutes=i * 15) for i in range(1, 9)]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert len(groups) == 8
    packed = pack_thin_fill_groups(groups)
    assert len(packed) == 2
    assert [len(g["asset_ids"]) for g in packed] == [4, 4]
    assert packed[0]["id"].startswith("pack-")


def test_splits_when_run_span_exceeds_45_min() -> None:
    assets = [_asset(i, minutes=i * 9) for i in range(1, 8)]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert len(groups) >= 2
    assert all(len(g["asset_ids"]) < 7 for g in groups)


def test_merges_adjacent_solos_within_guard() -> None:
    assets = [_asset(i, minutes=i) for i in range(1, 5)]
    groups = fill_groups_from_assets(assets, trip=_trip(assets))
    assert len(groups) == 1
    assert groups[0]["asset_ids"] == ["a001", "a002", "a003", "a004"]


def test_compose_merged_solos_fill_multi_slot_page() -> None:
    from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip

    assets = [_asset(i, minutes=i) for i in range(1, 5)]
    trip = _trip(assets)
    trip["studio"] = {"edition": "portfolio"}
    series = [
        {
            "id": "magazine-1-pair",
            "pageCount": 1,
            "density": "standard",
            "version": 1,
            "capacity": 4,
            "sequence": [
                {
                    "i": 1,
                    "role": "p1",
                    "program": "grid",
                    "slotBand": 4,
                    "patternId": "page-4-grid-land",
                }
            ],
        }
    ]
    chapters = [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": a["id"]} for a in assets],
            "screens": [],
        }
    ]
    out, meta = compose_portfolio_trip(
        chapters, assets=assets, series=series, trip=trip
    )
    screens = out[0]["screens"]
    assert len(screens) == 1
    assert screens[0]["patternId"] == "page-4-grid-land"
    assert [s["assetId"] for s in screens[0]["slots"]] == [
        "a001",
        "a002",
        "a003",
        "a004",
    ]
    fulfill = meta["sequenceFulfillment"]
    assert fulfill["demotedPages"] == 0
    assert fulfill["plannedPages"] == 1
    assert fulfill["renderedPages"] == 1


def test_user_pin_is_not_rewritten_when_hollow() -> None:
    from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip

    assets = [_asset(i, minutes=i * 20) for i in range(1, 9)]
    trip = _trip(assets)
    trip["studio"] = {
        "edition": "portfolio",
        "portfolio": {"pageCountSource": "user", "pageCount": 8},
    }
    series = [
        {
            "id": "magazine-8-standard",
            "pageCount": 8,
            "density": "standard",
            "version": 1,
            "capacity": 16,
            "sequence": [
                {
                    "i": i,
                    "role": f"p{i}",
                    "program": "grid",
                    "slotBand": 2,
                    "patternId": "page-2-pair-land",
                }
                for i in range(1, 9)
            ],
        },
        {
            "id": "magazine-4-standard",
            "pageCount": 4,
            "density": "standard",
            "version": 1,
            "capacity": 8,
            "sequence": [
                {
                    "i": i,
                    "role": f"p{i}",
                    "program": "hero",
                    "slotBand": 1,
                    "patternId": "page-1-hero-land-wide",
                }
                for i in range(1, 5)
            ],
        },
    ]
    chapters = [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": a["id"]} for a in assets],
            "screens": [],
        }
    ]
    _out, meta = compose_portfolio_trip(
        chapters, assets=assets, series=series, trip=trip
    )
    assert meta["seriesId"] == "magazine-8-standard"
    hint = trip["studio"]["portfolio"]["match"].get("pageCountHint") or ""
    density = trip["studio"]["portfolio"]["match"].get("densityHint") or ""
    assert "没排满" not in hint
    assert "更饱满" not in hint
    assert "没排满" in density


def test_sparse_collection_median_over_60_min() -> None:
    assets = [_asset(i, minutes=i * 90) for i in range(1, 6)]
    assert is_sparse_collection(assets) is True
    tight = [_asset(i, minutes=i) for i in range(1, 6)]
    assert is_sparse_collection(tight) is False


def _catalog_with_synthetic_24() -> list[dict]:
    from travelogue.layout_engine.editorial_series.catalog import load_official_series
    from travelogue.layout_engine.editorial_series.match import series_capacity

    catalog = [dict(row) for row in load_official_series()]
    twenty = next(row for row in catalog if row["id"] == "magazine-20-standard")
    extra = [
        {
            "i": 21,
            "role": "synth-hero",
            "program": "hero",
            "slotBand": 1,
            "patternId": "page-1-hero-port",
        },
        {
            "i": 22,
            "role": "synth-pair",
            "program": "mosaic",
            "slotBand": 2,
            "patternId": "page-2-pair-land",
        },
        {
            "i": 23,
            "role": "synth-trio",
            "program": "grid",
            "slotBand": 3,
            "patternId": "page-3-land",
        },
        {
            "i": 24,
            "role": "synth-quad",
            "program": "mosaic",
            "slotBand": 4,
            "patternId": "page-4-grid-land",
        },
    ]
    twenty_four = dict(twenty)
    twenty_four["id"] = "magazine-24-standard"
    twenty_four["pageCount"] = 24
    twenty_four["sequence"] = list(twenty["sequence"]) + extra
    twenty_four["capacity"] = series_capacity(twenty_four)
    catalog.append(twenty_four)
    return catalog


def test_ac_msp_16_tier_sequences_explained_by_fulfillment() -> None:
    from travelogue.layout_engine.editorial_series.match import select_series
    from travelogue.layout_engine.editorial_series.place import place_groups

    assets = [_asset(i, minutes=i) for i in range(1, 73)]
    trip = _trip(assets)
    groups = fill_groups_from_assets(assets, trip=trip)
    catalog = _catalog_with_synthetic_24()
    rendered: dict[int, tuple[str, ...]] = {}
    for pages in (8, 12, 24):
        choice = select_series(
            catalog,
            kept_n=72,
            page_count=pages,
            page_count_source="user",
        )
        assert choice is not None
        placed = place_groups(groups, choice.series.get("sequence") or [], cap=choice.cap)
        demoted = sum(
            1
            for p in placed.pages
            if p.planned_pattern_id and p.pattern_id != p.planned_pattern_id
        )
        assert demoted == placed.demoted_pages
        consumed = len(placed.pages) + len(placed.dropped_roles)
        planned_n = len(choice.series.get("sequence") or [])
        assert consumed <= planned_n
        rendered[pages] = tuple(p.pattern_id for p in placed.pages)
    assert rendered[8] != rendered[12]
    assert rendered[8] != rendered[24]
    assert rendered[12] != rendered[24]


@pytest.mark.pipeline_isolation
def test_ac_msp_21_journal_still_rejects_cross_shot_group() -> None:
    from pathlib import Path

    from travelogue.layout_engine import api as layout_api
    from travelogue.layout_engine.mosaic import trip as mosaic_trip
    from travelogue.layout_engine.mosaic.shot_group_gate import (
        hard_reject_cross_shot_group,
    )

    assets = {
        "a": {"shotGroupId": "sg-1"},
        "b": {"shotGroupId": "sg-2"},
        "c": {"shotGroupId": "sg-1"},
    }
    assert hard_reject_cross_shot_group(
        "screen-mosaic-4-2l2p-weighted",
        ["a", "b", "c"],
        assets,
    )
    journal_src = Path(mosaic_trip.__file__).read_text(encoding="utf-8")
    api_src = Path(layout_api.__file__).read_text(encoding="utf-8")
    assert "fill_groups" not in journal_src
    assert "editorial_series.fill" not in journal_src
    assert "editorial_series.fill" not in api_src
    assert "compose_trip" in api_src
