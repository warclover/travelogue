"""PFM · editorial_series catalog, matcher fixtures, overflow, items sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config.edition import E_PORTFOLIO_UNAVAILABLE, PortfolioUnavailableError
from travelogue.layout_contract.chapter_items import item_asset_ids
from travelogue.layout_engine.editorial_series.catalog import (
    SERIES_DIR,
    assert_not_reserve_path,
    load_official_series,
    official_series_dir,
)
from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip
from travelogue.layout_engine.editorial_series.match import (
    select_series,
    snap_user_page_count,
)
from travelogue.layout_engine.editorial_series.place import (
    PlacedPage,
    attach_screens_to_chapters,
    place_groups,
    refuse_cross_group_screen,
)
from travelogue.paths import ROOT

pytestmark = pytest.mark.unit

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "editorial_series"


def _magazine_32() -> dict:
    bands = [1, 2, 3, 4, 3, 2, 1, 2] * 4
    sequence = [
        {
            "i": i,
            "role": f"p{i}",
            "program": "grid" if band >= 3 else "hero",
            "slotBand": band,
            "patternId": f"page-grid-{band}",
        }
        for i, band in enumerate(bands, 1)
    ]
    return {
        "id": "magazine-32-standard",
        "kind": "series",
        "version": 1,
        "pageCount": 32,
        "density": "standard",
        "photo_span": [24, 64],
        "sequence": sequence,
    }


def _fixture_catalog() -> list[dict]:
    rows = load_official_series(series_dir=FIXTURE_DIR)
    rows.append(_magazine_32())
    return rows


def _assets_from_groups(spec: list[tuple[str, str, int]]) -> list[dict]:
    assets: list[dict] = []
    n = 0
    for gid, kind, count in spec:
        for _ in range(count):
            n += 1
            assets.append(
                {
                    "id": f"a{n:03d}",
                    "shotGroupId": gid,
                    "shotGroupKind": kind,
                }
            )
    return assets


def _one_chapter(assets: list[dict]) -> list[dict]:
    return [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": a["id"]} for a in assets],
            "screens": [],
        }
    ]


def _screen_ids(chapters: list[dict]) -> list[str]:
    ids: list[str] = []
    for ch in chapters:
        for sc in ch.get("screens") or []:
            for slot in sc.get("slots") or []:
                aid = slot.get("assetId")
                if aid:
                    ids.append(str(aid))
    return ids


def _item_ids(chapters: list[dict]) -> set[str]:
    ids: set[str] = set()
    for ch in chapters:
        for item in ch.get("items") or []:
            ids.update(item_asset_ids(item))
    return ids


def test_official_series_dir_is_not_reserve() -> None:
    reserve = (ROOT / "docs" / "templates" / "reserve").resolve()
    runtime = official_series_dir().resolve()
    assert runtime == SERIES_DIR.resolve()
    with pytest.raises(ValueError):
        runtime.relative_to(reserve)


def test_load_official_series_empty_dir_is_empty(tmp_path: Path) -> None:
    assert load_official_series(series_dir=tmp_path) == []


def test_load_official_series_skips_folio_prefix(tmp_path: Path) -> None:
    (tmp_path / "folio-16-trial.yaml").write_text(
        "id: folio-16-trial\npageCount: 16\n", encoding="utf-8"
    )
    (tmp_path / "magazine-8-sparse.yaml").write_text(
        (FIXTURE_DIR / "magazine-8-sparse.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    loaded = load_official_series(series_dir=tmp_path)
    assert [row["id"] for row in loaded] == ["magazine-8-sparse"]
    assert loaded[0]["sequence"][0]["slotBand"] == 1


def test_assert_not_reserve_path_rejects_atelier() -> None:
    reserve_file = ROOT / "docs" / "templates" / "reserve" / "catalog.yaml"
    with pytest.raises(ValueError, match="must not read"):
        assert_not_reserve_path(reserve_file)
    assert_not_reserve_path(SERIES_DIR)


def test_load_official_series_rejects_reserve_dir() -> None:
    reserve = ROOT / "docs" / "templates" / "reserve" / "series"
    with pytest.raises(ValueError, match="must not read"):
        load_official_series(series_dir=reserve)


def test_compose_portfolio_trip_empty_catalog_hard_fails() -> None:
    with pytest.raises(PortfolioUnavailableError) as exc:
        compose_portfolio_trip([], series=[])
    assert exc.value.code == E_PORTFOLIO_UNAVAILABLE


def test_compose_portfolio_trip_empty_assets_hard_fails() -> None:
    with pytest.raises(PortfolioUnavailableError) as exc:
        compose_portfolio_trip([])
    assert exc.value.code == E_PORTFOLIO_UNAVAILABLE


W1A_OFFICIAL_IDS = {
    "magazine-8-standard",
    "magazine-12-standard",
    "magazine-16-standard",
    "magazine-20-standard",
    "magazine-28-standard",
}


def test_official_catalog_p0_magazine_16() -> None:
    rows = load_official_series()
    assert {row["id"] for row in rows} == W1A_OFFICIAL_IDS
    series = next(row for row in rows if row["id"] == "magazine-16-standard")
    assert series["pageCount"] == 16
    assert series["density"] == "standard"
    assert series["photo_span"] == [48, 80]
    assert len(series["sequence"]) == 16
    bands = [int(p["slotBand"]) for p in series["sequence"]]
    assert bands == [1, 1, 2, 6, 4, 3, 5, 1, 4, 3, 6, 3, 5, 2, 6, 1]
    assert series["capacity"] == 53
    assert all(not str(row["id"]).startswith("folio-") for row in rows)
    assert {row["id"]: row["capacity"] for row in rows} == {
        "magazine-8-standard": 27,
        "magazine-12-standard": 36,
        "magazine-16-standard": 53,
        "magazine-20-standard": 72,
        "magazine-28-standard": 81,
    }


def test_compose_from_official_magazine_16() -> None:
    """One scene group per page, sized to the P0 sequence slotBand."""
    bands = [1, 1, 2, 6, 4, 3, 5, 1, 4, 3, 6, 3, 5, 2, 6, 1]
    assets = _assets_from_groups(
        [(f"g{i}", "scene", band) for i, band in enumerate(bands, 1)]
    )
    chapters = _one_chapter(assets)
    trip: dict = {"studio": {"edition": "portfolio"}}
    out, meta = compose_portfolio_trip(chapters, assets=assets, trip=trip)
    assert meta["seriesId"] == "magazine-16-standard"
    placed = _screen_ids(out)
    assert len(placed) == 53
    assert _item_ids(out) <= set(placed)
    assert trip["studio"]["portfolio"]["photosPlaced"] == 53
    assert trip["studio"]["portfolio"]["photosKept"] == 53
    screens = [sc for ch in out for sc in (ch.get("screens") or [])]
    assert len(screens) == 16
    assert screens[0]["patternId"] == "page-1-hero-land-wide"
    assert screens[3]["patternId"] == "page-6-grid-land"
    assert screens[10]["patternId"] == "page-6-1l5l-wide-right"
    assert screens[15]["patternId"] == "page-1-hero-land-wide"
    fulfill = trip["studio"]["portfolio"]["sequenceFulfillment"]
    assert fulfill["plannedPages"] == 16
    assert fulfill["renderedPages"] == 16
    assert fulfill["demotedPages"] == 0
    assert "patternId" not in fulfill


def test_curate_fork_source_contract() -> None:
    from travelogue.curation import curate as curate_mod

    src = Path(curate_mod.__file__).read_text(encoding="utf-8")
    assert "is_portfolio_trip" in src
    assert "compose_portfolio_trip" in src
    assert "from travelogue.layout_engine.api import compose_trip" in src
    assert "禁止静默" in src


def test_refuse_cross_group_screen() -> None:
    refuse_cross_group_screen(["g-a", "g-a"])
    with pytest.raises(ValueError, match="two shot groups"):
        refuse_cross_group_screen(["g-a", "g-b"])


def test_place_groups_never_mixes_shot_groups() -> None:
    groups = [
        {"id": "g-a", "kind": "scene", "asset_ids": ["a1", "a2", "a3"]},
        {"id": "g-b", "kind": "scene", "asset_ids": ["b1", "b2", "b3"]},
    ]
    sequence = [
        {"role": "wide", "slotBand": 4, "patternId": "page-grid-4"},
        {"role": "wide2", "slotBand": 4, "patternId": "page-grid-4"},
    ]
    placed = place_groups(groups, sequence)
    assert len(placed.pages) == 2
    assert placed.pages[0].asset_ids == ["a1", "a2", "a3"]
    assert placed.pages[0].shot_group_id == "g-a"
    assert placed.pages[1].asset_ids == ["b1", "b2", "b3"]
    assert placed.pages[1].shot_group_id == "g-b"
    for page in placed.pages:
        refuse_cross_group_screen([page.shot_group_id] * len(page.asset_ids))


def test_underfilled_multi_slot_page_falls_back_to_hero() -> None:
    groups = [{"id": "solo-a", "kind": "scene", "asset_ids": ["a1"]}]
    sequence = [
        {"role": "grid4", "slotBand": 4, "patternId": "page-4-grid-land-wide"},
    ]
    land = place_groups(groups, sequence, aspect_kinds={"a1": "landscape"})
    assert len(land.pages) == 1
    assert land.pages[0].pattern_id == "page-1-hero-land-wide"
    assert land.pages[0].asset_ids == ["a1"]

    port = place_groups(
        [{"id": "solo-b", "kind": "scene", "asset_ids": ["b1"]}],
        sequence,
        aspect_kinds={"b1": "portrait"},
    )
    assert port.pages[0].pattern_id == "page-1-hero-port"


def test_ac_pfm_10_dense_page_degrades_when_group_too_small() -> None:
    """AC-PFM-10 · 槽 ≥5 且组规模不足 → 降级少槽，不硬塞。"""
    groups = [{"id": "g-scene", "kind": "scene", "asset_ids": ["a1", "a2", "a3"]}]
    sequence = [
        {"role": "dense", "slotBand": 5, "patternId": "page-5-3p2l-center"},
        {"role": "trio", "slotBand": 3, "patternId": "page-3-port"},
    ]
    placed = place_groups(groups, sequence)
    assert placed.dropped_roles == ["dense"]
    assert placed.used_roles == ["trio"]
    assert len(placed.pages) == 1
    assert placed.pages[0].slot_band == 3
    assert placed.pages[0].asset_ids == ["a1", "a2", "a3"]
    assert placed.leftover_ids == []


def test_dense_page_skipped_for_burst() -> None:
    groups = [{"id": "g-burst", "kind": "burst", "asset_ids": [f"b{i}" for i in range(6)]}]
    sequence = [
        {"role": "dense", "slotBand": 5, "patternId": "page-grid-5"},
        {"role": "trio", "slotBand": 3, "patternId": "page-grid-3"},
        {"role": "trio2", "slotBand": 3, "patternId": "page-grid-3"},
    ]
    placed = place_groups(groups, sequence)
    assert placed.dropped_roles == ["dense"]
    assert all(p.slot_band < 5 for p in placed.pages)
    assert [p.shot_group_id for p in placed.pages] == ["g-burst", "g-burst"]


def test_select_series_fill_rate_prefers_window() -> None:
    catalog = _fixture_catalog()
    choice = select_series(catalog, kept_n=36)
    assert choice is not None
    assert choice.series["id"] == "magazine-16-standard"
    assert choice.upgraded is False
    assert choice.capped is False
    assert choice.cap == 36


def test_select_series_caps_after_max_tier() -> None:
    catalog = _fixture_catalog()
    choice = select_series(catalog, kept_n=80, max_pages=32)
    assert choice is not None
    assert choice.series["id"] == "magazine-32-standard"
    assert choice.upgraded is True
    assert choice.capped is True
    assert choice.cap == 72
    assert choice.overflow_resolution == "tier_upgraded_then_capped"


def test_select_series_user_pin_does_not_upgrade() -> None:
    catalog = _fixture_catalog()
    choice = select_series(
        catalog,
        kept_n=20,
        page_count=8,
        page_count_source="user",
        density="sparse",
    )
    assert choice is not None
    assert choice.series["id"] == "magazine-8-sparse"
    assert choice.upgraded is False
    assert choice.capped is False
    assert choice.cap == 20


def test_catalog_page_count_chips_only_official_skus() -> None:
    from travelogue.layout_engine.editorial_series.catalog import load_official_series
    from travelogue.layout_engine.editorial_series.match import catalog_page_count_chips

    assert catalog_page_count_chips([]) == []
    assert catalog_page_count_chips(_fixture_catalog()) == [8, 16, 32]
    assert catalog_page_count_chips(load_official_series()) == [8, 12, 16, 20, 28]


def test_snap_44_falls_to_catalog_sku() -> None:
    used, hint = snap_user_page_count(
        44,
        [{"pageCount": 16}, {"pageCount": 28}, {"pageCount": 36}],
        max_pages=48,
    )
    assert used == 36
    assert hint == "非标准页数 · 按 36 页靠档"


def test_snap_18_to_16_hint() -> None:
    used, hint = snap_user_page_count(18, [{"pageCount": 16}])
    assert used == 16
    assert hint == "非标准页数 · 按 16 页靠档"


def test_snap_missing_sku_to_nearest_catalog() -> None:
    used, hint = snap_user_page_count(8, [{"pageCount": 16}])
    assert used == 16
    assert hint == "非标准页数 · 按 16 页靠档"


def test_compose_user_pin_18_snaps_on_official() -> None:
    bands = [1, 1, 2, 6, 4, 3, 5, 1, 4, 3, 6, 3, 5, 2, 6, 1]
    assets = _assets_from_groups(
        [(f"g{i}", "scene", band) for i, band in enumerate(bands, 1)]
    )
    chapters = _one_chapter(assets)
    trip = {
        "studio": {
            "edition": "portfolio",
            "portfolio": {"pageCountSource": "user", "pageCount": 18},
        }
    }
    _out, meta = compose_portfolio_trip(chapters, assets=assets, trip=trip)
    assert meta["seriesId"] == "magazine-16-standard"
    block = trip["studio"]["portfolio"]
    assert block["pageCount"] == 16
    assert block["pageCountSource"] == "user"
    assert block["match"]["pageCountRequested"] == 18
    assert block["match"]["pageCountHint"] == "非标准页数 · 按 16 页靠档"


def test_compose_fixture_upgrades_and_syncs_items() -> None:
    assets = _assets_from_groups([("g1", "scene", 10), ("g2", "scene", 10)])
    chapters = _one_chapter(assets)
    trip = {"studio": {"edition": "portfolio", "portfolio": {"pageCountSource": "auto"}}}
    out, meta = compose_portfolio_trip(
        chapters,
        assets=assets,
        trip=trip,
        series=_fixture_catalog(),
    )
    assert meta["seriesId"] == "magazine-16-standard"
    placed = _screen_ids(out)
    kept = {a["id"] for a in assets}
    assert set(placed) <= kept
    assert _item_ids(out) <= set(placed)
    assert len(placed) == 20
    groups_on_pages = []
    for ch in out:
        for sc in ch.get("screens") or []:
            gids = {sc.get("shotGroupId")}
            assert len(gids) == 1
            groups_on_pages.append(sc.get("shotGroupId"))
    assert "g1" in groups_on_pages and "g2" in groups_on_pages
    block = trip["studio"]["portfolio"]
    assert block["photosPlaced"] == 20
    assert block["photosKept"] == 20
    assert "overflow" not in block or not block.get("overflow")


def test_compose_fixture_overflow_cap() -> None:
    assets = _assets_from_groups([("g1", "scene", 80)])
    chapters = _one_chapter(assets)
    trip: dict = {"studio": {"edition": "portfolio"}}
    out, meta = compose_portfolio_trip(
        chapters,
        assets=assets,
        trip=trip,
        series=_fixture_catalog(),
    )
    placed = _screen_ids(out)
    assert len(placed) == 72
    assert _item_ids(out) <= set(placed)
    overflow = meta["overflow"]
    assert overflow["count"] == 8
    assert overflow["resolution"] == "tier_upgraded_then_capped"
    assert trip["studio"]["portfolio"]["photosPlaced"] == 72
    assert trip["studio"]["portfolio"]["photosKept"] == 80


def test_compose_items_match_screens_when_stub_can_cover() -> None:
    """D-PFM-27 · 屏数未超 items 上限时，实收集合与 items 一致。"""
    series = [
        {
            "id": "magazine-8-standard",
            "pageCount": 8,
            "density": "standard",
            "version": 1,
            "photo_span": [8, 16],
            "sequence": [
                {
                    "i": i,
                    "role": f"p{i}",
                    "program": "hero",
                    "slotBand": 1,
                    "patternId": "page-hero-1",
                }
                for i in range(1, 9)
            ],
        }
    ]
    assets = _assets_from_groups([("g1", "scene", 8)])
    chapters = _one_chapter(assets)
    out, _meta = compose_portfolio_trip(chapters, assets=assets, series=series)
    placed = _screen_ids(out)
    assert len(placed) == 8
    assert set(placed) == _item_ids(out)
    assert set(placed) == {a["id"] for a in assets}


def test_compose_from_fixture_dir_not_runtime() -> None:
    assets = _assets_from_groups([("g1", "scene", 12)])
    chapters = _one_chapter(assets)
    out, meta = compose_portfolio_trip(
        chapters,
        assets=assets,
        series_dir=FIXTURE_DIR,
    )
    assert meta["seriesId"] in {"magazine-8-sparse", "magazine-16-standard"}
    assert SERIES_DIR.resolve() != FIXTURE_DIR.resolve()
    official = load_official_series()
    assert {row["id"] for row in official} == W1A_OFFICIAL_IDS
    gold = next(row for row in official if row["id"] == "magazine-16-standard")
    assert gold["photo_span"] == [48, 80]


def test_intake_rejects_folio_and_pagecount_mismatch() -> None:
    from travelogue.layout_engine.editorial_series.intake import (
        SeriesIntakeError,
        accept_series_document,
        normalize_series_document,
        slot_band_from_role,
    )

    assert accept_series_document({"id": "folio-16-standard"}) is None
    with pytest.raises(SeriesIntakeError, match="pageCount"):
        normalize_series_document(
            {
                "id": "magazine-24-standard",
                "pageCount": 32,
                "density": "standard",
                "photo_span": [72, 120],
                "sequence": [{"role": "hero", "program": "hero"}] * 32,
            }
        )
    assert slot_band_from_role("hero-land") == 1
    assert slot_band_from_role("grid-6-land") == 6
    assert (
        slot_band_from_role(
            "land-hero-l", {"faceHint": "page-3-2l1p-hero-left"}
        )
        == 3
    )


def test_intake_normalizes_tdv_promote_yaml_without_slot_band(tmp_path: Path) -> None:
    yaml_text = """
id: magazine-8-standard
kind: series
status: promote-ready
pageCount: 8
density: standard
photo_span: [8, 16]
sequence:
  - { i: 1, role: hero-land, program: hero, faceHint: page-1-hero-land }
  - { i: 2, role: pair-port, program: mosaic, faceHint: page-2-pair-port }
  - { i: 3, role: row-port-3, program: grid, faceHint: page-3-port }
  - { i: 4, role: grid-4-land, program: grid, faceHint: page-4-grid-land }
  - { i: 5, role: trio, program: grid, faceHint: page-grid-3 }
  - { i: 6, role: pair-port, program: mosaic, faceHint: page-2-pair-port }
  - { i: 7, role: row-port-3, program: grid, faceHint: page-3-port }
  - { i: 8, role: hero-land, program: hero, faceHint: page-1-hero-land }
"""
    path = tmp_path / "magazine-8-standard.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    loaded = load_official_series(series_dir=tmp_path)
    assert len(loaded) == 1
    seq = loaded[0]["sequence"]
    assert seq[0]["slotBand"] == 1
    assert seq[1]["slotBand"] == 2
    assert seq[2]["slotBand"] == 3
    assert seq[3]["slotBand"] == 4
    assert seq[0]["patternId"] == "page-1-hero-land"


def test_min_photo_span_lo_from_fixture_catalog() -> None:
    from travelogue.layout_engine.editorial_series.catalog import min_photo_span_lo

    assert min_photo_span_lo(_fixture_catalog()) == 8
    assert min_photo_span_lo([]) is None
    assert min_photo_span_lo(load_official_series()) == 24


def test_select_series_fill_rate_official_w1a() -> None:
    catalog = load_official_series()
    by_kept = {
        20: "magazine-8-standard",
        50: "magazine-16-standard",
        82: "magazine-28-standard",
    }
    for kept, sid in by_kept.items():
        choice = select_series(catalog, kept_n=kept)
        assert choice is not None
        assert choice.series["id"] == sid, kept
    overflow = select_series(catalog, kept_n=82)
    assert overflow is not None
    assert overflow.overflow_count == 1
    assert overflow.capped is True


def test_compose_82_overflow_is_explicit() -> None:
    assets = _assets_from_groups([("g-all", "scene", 82)])
    chapters = _one_chapter(assets)
    trip: dict = {"studio": {"edition": "portfolio"}}
    _out, meta = compose_portfolio_trip(chapters, assets=assets, trip=trip)
    assert meta["seriesId"] == "magazine-28-standard"
    overflow = trip["studio"]["portfolio"]["overflow"]
    assert overflow["count"] == 1
    assert overflow["resolution"]


def test_photo_span_mutation_leaves_four_paths_unchanged() -> None:
    from travelogue.layout_engine.editorial_series.catalog import min_capacity

    catalog = load_official_series()
    mutated = []
    for row in catalog:
        copy = dict(row)
        copy["photo_span"] = [1, 999]
        mutated.append(copy)
    for kept in (20, 50, 82, 90):
        a = select_series(catalog, kept_n=kept)
        b = select_series(mutated, kept_n=kept)
        assert a is not None and b is not None
        assert a.series["id"] == b.series["id"]
        assert a.cap == b.cap
        assert a.overflow_count == b.overflow_count
        assert a.overflow_resolution == b.overflow_resolution
    assert min_capacity(catalog) == min_capacity(mutated) == 27


def test_select_series_ignores_photo_span_for_cap() -> None:
    catalog = load_official_series()
    mutated = []
    for row in catalog:
        copy = dict(row)
        copy["photo_span"] = [1, 999]
        mutated.append(copy)
    a = select_series(catalog, kept_n=50)
    b = select_series(mutated, kept_n=50)
    assert a is not None and b is not None
    assert a.series["id"] == b.series["id"] == "magazine-16-standard"
    assert a.cap == b.cap == 50


def test_min_capacity_from_official_catalog() -> None:
    from travelogue.layout_engine.editorial_series.catalog import min_capacity

    assert min_capacity(_fixture_catalog()) == 21
    assert min_capacity([]) is None
    assert min_capacity(load_official_series()) == 27


def test_attach_prefers_buckets_over_stale_items() -> None:
    chapters = [
        {
            "id": "ch-01",
            "items": [{"type": "media-card", "assetId": "a1"}],
            "screens": [{"patternId": "stale"}],
        },
        {
            "id": "ch-02",
            "items": [{"type": "media-row", "assetIds": ["old-x", "old-y"]}],
            "screens": [],
        },
    ]
    pages = [
        PlacedPage(
            role="h1",
            program="hero",
            slot_band=1,
            pattern_id="page-1-hero-land-wide",
            asset_ids=["a1"],
            shot_group_id="g1",
        ),
        PlacedPage(
            role="h2",
            program="hero",
            slot_band=1,
            pattern_id="page-1-hero-land-wide",
            asset_ids=["b2"],
            shot_group_id="g2",
        ),
    ]
    attach_screens_to_chapters(chapters, pages, buckets=[["a1"], ["b2", "old-x"]])
    assert [s["slots"][0]["assetId"] for s in chapters[0]["screens"]] == ["a1"]
    assert [s["slots"][0]["assetId"] for s in chapters[1]["screens"]] == ["b2"]


def _hero_series(pages: int) -> list[dict]:
    return [
        {
            "id": f"magazine-{pages}-standard",
            "pageCount": pages,
            "density": "standard",
            "version": 1,
            "photo_span": [pages, 200],
            "capacity": pages,
            "sequence": [
                {
                    "i": i,
                    "role": f"p{i}",
                    "program": "hero",
                    "slotBand": 1,
                    "patternId": "page-1-hero-land-wide",
                }
                for i in range(1, pages + 1)
            ],
        }
    ]


def test_compose_reserves_pages_for_later_chapters() -> None:
    early = _assets_from_groups([("g-early", "scene", 40)])
    mid = _assets_from_groups([("g-mid", "scene", 8)])
    late = _assets_from_groups([("g-late", "scene", 8)])
    # Unique ids across groups (helper restarts at a001).
    mid = [{**a, "id": f"m{a['id'][1:]}"} for a in mid]
    late = [{**a, "id": f"z{a['id'][1:]}"} for a in late]
    assets = early + mid + late
    buckets = [
        [a["id"] for a in early],
        [a["id"] for a in mid],
        [a["id"] for a in late],
    ]
    chapters = [
        {
            "id": f"ch-{i:02d}",
            "items": [{"type": "media-card", "assetId": buckets[i - 1][0]}],
            "screens": [],
        }
        for i in range(1, 4)
    ]
    chapters[1]["items"] = [
        {"type": "media-row", "assetIds": ["ghost-a", "ghost-b"]},
    ]
    trip = {
        "studio": {
            "edition": "portfolio",
            "portfolio": {"pageCountSource": "user", "pageCount": 6},
        }
    }
    out, _meta = compose_portfolio_trip(
        chapters,
        assets=assets,
        buckets=buckets,
        trip=trip,
        series=_hero_series(6),
    )
    counts = [len(ch.get("screens") or []) for ch in out]
    assert counts[0] >= 1
    assert counts[1] >= 1
    assert counts[2] >= 1
    assert sum(counts) == 6
    assert not any(
        it.get("type") == "media-row" for it in (out[1].get("items") or [])
    )
    assert all((ch.get("screens") or ch.get("items") == []) for ch in out)
    for ch in out:
        for sc in ch.get("screens") or []:
            assert str(sc.get("patternId") or "").startswith("page-")


def test_portfolio_empty_chapter_does_not_render_journal_items() -> None:
    from travelogue.render.assemble import build_render_context

    trip = {
        "tripId": "folio-ch-fallback",
        "layoutEngine": "screens",
        "exportLayout": "web",
        "studio": {"edition": "portfolio"},
        "meta": {"title": "测"},
        "assets": [
            {
                "id": "a1",
                "width": 1600,
                "height": 900,
                "aspectKind": "landscape",
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "一",
                "screens": [
                    {
                        "patternId": "page-1-hero-land-wide",
                        "slots": [{"assetId": "a1", "slot": 0, "fit": "cover"}],
                        "layoutGeometry": {
                            "stageAspect": "16:9",
                            "gridClass": "layout-screen__grid--page-1-hero-land-wide",
                        },
                    }
                ],
                "items": [],
            },
            {
                "id": "ch-02",
                "index": 2,
                "title": "二",
                "screens": [],
                "items": [
                    {"type": "media-row", "assetIds": ["a1"]},
                    {"type": "media-card", "assetId": "a1"},
                ],
            },
        ],
    }
    ctx = build_render_context(trip, export_mode="draft", export_layout_override="web")
    ids = [ch["id"] for ch in ctx["chapters"]]
    assert ids == ["ch-01"]
    assert all(ch.get("hideChapterChrome") for ch in ctx["chapters"])
    assert ctx["hasTripIndex"] is False

