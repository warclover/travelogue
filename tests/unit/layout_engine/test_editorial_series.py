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
    (tmp_path / "magazine-8-standard.yaml").write_text(
        (FIXTURE_DIR / "magazine-8-standard.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    loaded = load_official_series(series_dir=tmp_path)
    assert [row["id"] for row in loaded] == ["magazine-8-standard"]
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


def test_official_catalog_p0_magazine_16() -> None:
    rows = load_official_series()
    assert [row["id"] for row in rows] == ["magazine-16-standard"]
    series = rows[0]
    assert series["pageCount"] == 16
    assert series["density"] == "standard"
    assert series["photo_span"] == [48, 80]
    assert len(series["sequence"]) == 16
    bands = [int(p["slotBand"]) for p in series["sequence"]]
    assert bands == [1, 1, 2, 6, 4, 3, 5, 1, 4, 3, 6, 3, 5, 2, 6, 1]
    assert all(not str(row["id"]).startswith("folio-") for row in rows)


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


def test_ac_pfm_10_dense_page_degrades_when_group_too_small() -> None:
    """AC-PFM-10 · 槽 ≥5 且组规模不足 → 降级少槽，不硬塞。"""
    groups = [{"id": "g-scene", "kind": "scene", "asset_ids": ["a1", "a2", "a3"]}]
    sequence = [
        {"role": "dense", "slotBand": 5, "patternId": "page-5-3p2l-center"},
        {"role": "trio", "slotBand": 3, "patternId": "page-3-port"},
    ]
    placed = place_groups(groups, sequence)
    assert placed.dropped_roles == ["dense"]
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


def test_select_series_upgrades_when_span_misses() -> None:
    catalog = _fixture_catalog()
    choice = select_series(catalog, kept_n=20)
    assert choice is not None
    assert choice.series["id"] == "magazine-16-standard"
    assert choice.upgraded is True
    assert choice.capped is False
    assert choice.cap == 20


def test_select_series_caps_after_max_tier() -> None:
    catalog = _fixture_catalog()
    choice = select_series(catalog, kept_n=80, max_pages=32)
    assert choice is not None
    assert choice.series["id"] == "magazine-32-standard"
    assert choice.upgraded is True
    assert choice.capped is True
    assert choice.cap == 64
    assert choice.overflow_resolution == "tier_upgraded_then_capped"


def test_select_series_user_pin_does_not_upgrade() -> None:
    catalog = _fixture_catalog()
    choice = select_series(
        catalog,
        kept_n=20,
        page_count=8,
        page_count_source="user",
    )
    assert choice is not None
    assert choice.series["id"] == "magazine-8-standard"
    assert choice.upgraded is False
    assert choice.capped is True
    assert choice.cap == 16


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
    assert len(placed) == 64
    assert _item_ids(out) <= set(placed)
    overflow = meta["overflow"]
    assert overflow["count"] == 16
    assert overflow["resolution"] == "tier_upgraded_then_capped"
    assert trip["studio"]["portfolio"]["photosPlaced"] == 64
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
    assert meta["seriesId"] in {"magazine-8-standard", "magazine-16-standard"}
    assert SERIES_DIR.resolve() != FIXTURE_DIR.resolve()
    official = load_official_series()
    assert [row["id"] for row in official] == ["magazine-16-standard"]
    assert official[0]["photo_span"] == [48, 80]


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
    assert min_photo_span_lo(load_official_series()) == 48

