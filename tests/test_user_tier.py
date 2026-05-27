"""userTier dual-folder ingest and curate weighting (PRD-EXPERIENCE E5)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from travelogue.curation.curate import run_curate
from travelogue.curation.curate_scoring import effective_cover_score, pick_cover_asset_id
from travelogue.config import get_config
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.user_tier import TIER_FEATURED, upgrade_asset_tier
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip


def _write_photo(path: Path, size: tuple[int, int] = (1600, 900), color=(120, 80, 40)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG")


def _dual_album(tmp_path: Path, featured_n: int = 2, material_n: int = 4) -> Path:
    root = tmp_path / "album"
    feat = root / "精选"
    mat = root / "素材上传"
    for i in range(featured_n):
        _write_photo(feat / f"feat-{i:02d}.jpg", color=(200, 100 + i * 10, 50))
    for i in range(material_n):
        _write_photo(mat / f"mat-{i:02d}.jpg", color=(80, 120 + i * 5, 160))
    return root


def _portrait_featured_album(tmp_path: Path, featured_n: int = 3, material_n: int = 4) -> Path:
    root = tmp_path / "album-portrait-feat"
    feat = root / "精选"
    mat = root / "素材上传"
    for i in range(featured_n):
        _write_photo(feat / f"feat-{i:02d}.jpg", size=(1200, 1600), color=(200, 90 + i * 8, 60))
    for i in range(material_n):
        _write_photo(mat / f"mat-{i:02d}.jpg", size=(1600, 900), color=(50, 110 + i * 6, 150))
    return root


def _ingest_dual_trip(
    tmp_path: Path,
    trip_id: str,
    album: Path,
    *,
    export_layout: str = "web",
    dedupe: bool = False,
) -> tuple[Path, dict, Path]:
    trips = tmp_path / "trips"
    trip_json = create_trip(trip_id, trips, title="tier", export_layout=export_layout)
    trip_dir = trips / trip_id
    trip = TripService().load(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=album,
        dedupe=dedupe,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    return trip_json, TripService().load(trip_json), trip_dir


def _asset_map(trip: dict) -> dict[str, dict]:
    return {a["id"]: a for a in trip.get("assets") or [] if a.get("id")}


def test_dual_folder_ingest_assigns_user_tier(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("tier-demo", trips, title="精选测试")
    trip_dir = trips / "tier-demo"
    trip = TripService().load(trip_json)
    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_dual_album(tmp_path),
        dedupe=False,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    featured = [a for a in trip["assets"] if a.get("userTier") == "featured"]
    material = [a for a in trip["assets"] if a.get("userTier", "material") == "material"]
    assert len(featured) == 2
    assert len(material) == 4
    assert result.stats["userTierSummary"]["featured"] == 2
    assert all(a.get("userTierSource") == "ingest" for a in featured)
    assert all(a.get("importSource") == "featured" for a in featured)
    assert all(a.get("importSource") == "material" for a in material)


def test_single_folder_ingest_uses_legacy_import_source(tmp_path: Path) -> None:
    root = tmp_path / "flat-album"
    root.mkdir()
    for i in range(4):
        _write_photo(root / f"photo-{i:02d}.jpg", color=(100 + i, 90, 80))

    trips = tmp_path / "trips"
    trip_json = create_trip("legacy-import", trips, title="legacy")
    trip_dir = trips / "legacy-import"
    trip = TripService().load(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=root,
        dedupe=False,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    assert len(trip["assets"]) == 4
    assert all(a.get("importSource") == "legacy" for a in trip["assets"])
    assert all(a.get("userTier") == "material" for a in trip["assets"])


def test_cross_folder_dedupe_preserves_material_import_source(tmp_path: Path) -> None:
    root = tmp_path / "album2"
    feat = root / "精选"
    mat = root / "素材"
    mat.mkdir(parents=True)
    feat.mkdir(parents=True)
    img = mat / "same.jpg"
    _write_photo(img)
    (feat / "same-copy.jpg").write_bytes(img.read_bytes())
    for i in range(3):
        _write_photo(feat / f"extra-{i}.jpg", color=(90 + i, 100, 110))

    trips = tmp_path / "trips"
    trip_json = create_trip("tier-dedupe-src", trips, title="dedupe src")
    trip_dir = trips / "tier-dedupe-src"
    trip = TripService().load(trip_json)
    ingest_cfg = replace(get_config().ingest, dedupe_burst=False)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=root,
        dedupe=True,
        generate_crops=False,
        cfg=ingest_cfg,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    upgraded = next(a for a in trip["assets"] if a.get("contentSig"))
    assert upgraded.get("userTier") == TIER_FEATURED
    assert upgraded.get("importSource") == "material"


def test_cross_folder_dedupe_upgrades_to_featured(tmp_path: Path) -> None:
    root = tmp_path / "album2"
    feat = root / "精选"
    mat = root / "素材"
    mat.mkdir(parents=True)
    feat.mkdir(parents=True)
    img = feat / "same.jpg"
    _write_photo(img)
    (mat / "same-copy.jpg").write_bytes(img.read_bytes())
    for i in range(3):
        _write_photo(mat / f"extra-{i}.jpg", color=(90 + i, 100, 110))

    trips = tmp_path / "trips"
    trip_json = create_trip("tier-dedupe", trips, title="dedupe")
    trip_dir = trips / "tier-dedupe"
    trip = TripService().load(trip_json)
    ingest_cfg = replace(get_config().ingest, dedupe_burst=False)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=root,
        dedupe=True,
        generate_crops=False,
        cfg=ingest_cfg,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    assert len(trip["assets"]) == 4
    featured = [a for a in trip["assets"] if a.get("userTier") == TIER_FEATURED]
    assert len(featured) == 1
    sig = featured[0]["contentSig"]
    assert sum(1 for a in trip["assets"] if a.get("contentSig") == sig) == 1


def test_resolve_import_source_unit() -> None:
    from travelogue.media.user_tier import resolve_import_source

    assert resolve_import_source(tier=TIER_FEATURED, dual_ingest=True) == "featured"
    assert resolve_import_source(tier="material", dual_ingest=True) == "material"
    assert resolve_import_source(tier=TIER_FEATURED, dual_ingest=False) == "legacy"


def test_ingest_import_source_passes_schema(tmp_path: Path) -> None:
    from travelogue.services.validate import validate_trip

    trips = tmp_path / "trips"
    trip_json = create_trip("tier-schema", trips, title="schema")
    trip_dir = trips / "tier-schema"
    trip = TripService().load(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_dual_album(tmp_path),
        dedupe=False,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert errs == []


def test_preserve_user_tier_on_replace_keeps_featured() -> None:
    from travelogue.media.user_tier import (
        TIER_FEATURED,
        TIER_MATERIAL,
        TIER_SOURCE_USER,
        preserve_user_tier_on_replace,
        preserve_user_tier_source_on_replace,
    )

    old = {"userTier": TIER_FEATURED, "userTierSource": TIER_SOURCE_USER}
    tier = preserve_user_tier_on_replace(old, TIER_MATERIAL)
    assert tier == TIER_FEATURED
    assert preserve_user_tier_source_on_replace(old, tier) == TIER_SOURCE_USER


def test_preserve_user_tier_on_replace_upgrades_incoming_featured() -> None:
    from travelogue.media.user_tier import (
        TIER_FEATURED,
        TIER_MATERIAL,
        preserve_user_tier_on_replace,
    )

    old = {"userTier": TIER_MATERIAL}
    assert preserve_user_tier_on_replace(old, TIER_FEATURED) == TIER_FEATURED


def test_upgrade_asset_tier_unit() -> None:
    assets = [
        {
            "id": "a1",
            "contentSig": "sig1",
            "userTier": "material",
            "importSource": "material",
        }
    ]
    assert upgrade_asset_tier(assets, "sig1", tier=TIER_FEATURED) is True
    assert assets[0]["userTier"] == TIER_FEATURED
    assert assets[0]["importSource"] == "material"


def test_featured_cover_weight_prefers_featured() -> None:
    assets = [
        {
            "id": "mat",
            "type": "image",
            "width": 1600,
            "height": 900,
            "aspectKind": "landscape",
            "userTier": "material",
            "quality": {"sharpness": 500},
        },
        {
            "id": "feat",
            "type": "image",
            "width": 1500,
            "height": 850,
            "aspectKind": "landscape",
            "userTier": "featured",
            "quality": {"sharpness": 400},
        },
    ]
    cover_id = pick_cover_asset_id(assets, export_layout="web", featured_weight=1.35)
    assert cover_id == "feat"
    assert effective_cover_score(assets[1], "web", featured_weight=1.35) > effective_cover_score(
        assets[0], "web", featured_weight=1.35
    )


def test_curate_writes_user_tier_summary(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("tier-curate", trips, title="curate tier")
    trip_dir = trips / "tier-curate"
    trip = TripService().load(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_dual_album(tmp_path, 2, 6),
        dedupe=False,
        generate_crops=False,
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    run_curate(trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    summary = (trip.get("curation") or {}).get("userTierSummary") or {}
    assert summary.get("featured") == 2
    assert summary.get("featuredInLayout", 0) >= 1


def test_screen_planner_hero_prefers_featured() -> None:
    from travelogue.curation.screen_planner import _pick_chapter_hero
    from travelogue.media.image_ops import AspectKind

    aspects: dict[str, AspectKind] = {"mat": "landscape", "feat": "landscape"}
    assets = {
        "mat": {
            "id": "mat",
            "width": 1600,
            "height": 900,
            "aspectKind": "landscape",
            "userTier": "material",
            "quality": {"sharpness": 500},
        },
        "feat": {
            "id": "feat",
            "width": 1600,
            "height": 900,
            "aspectKind": "landscape",
            "userTier": "featured",
            "quality": {"sharpness": 500},
        },
    }
    hero = _pick_chapter_hero(["mat", "feat"], aspects, assets, featured_weight=1.35)
    assert hero is not None
    assert hero[0] == "feat"


def test_screenplay_featured_only_filter() -> None:
    from travelogue.paths import SCREENPLAY_JS

    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "featuredOnlyEnabled" in js
    assert 'data-featured") === "true"' in js


# --- AC-DF automated subset (PRD appendix A · P1-3) ---


def test_ac_df_01_dual_ingest_user_tier_summary(tmp_path: Path) -> None:
    """AC-DF-01: dual ingest counts match curation.userTierSummary."""
    trip_json, trip, trip_dir = _ingest_dual_trip(tmp_path, "ac-df-01", _dual_album(tmp_path))
    result = run_curate(
        trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)
    summary = (trip.get("curation") or {}).get("userTierSummary") or {}
    assert summary.get("featured") == 2
    assert summary.get("material") == 4
    assert result.warnings is not None


def test_ac_df_02_web_cover_from_featured_with_top_score(tmp_path: Path) -> None:
    """AC-DF-02: web cover ∈ featured and has highest S_cover_eff among featured pool."""
    from travelogue.curation.curate import layout_eligible_assets
    from travelogue.curation.curate_scoring import (
        cover_asset_pool,
        effective_cover_score,
    )

    trip_json, trip, trip_dir = _ingest_dual_trip(tmp_path, "ac-df-02", _dual_album(tmp_path))
    for asset in trip["assets"]:
        if asset.get("userTier") == "material":
            asset.setdefault("quality", {})["sharpness"] = 900
        else:
            asset.setdefault("quality", {})["sharpness"] = 350
    run_curate(trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)

    cover_id = trip["coverAssetId"]
    assets_by_id = _asset_map(trip)
    cover = assets_by_id[cover_id]
    assert cover.get("userTier") == "featured"

    layout_assets = layout_eligible_assets(trip)
    pool = cover_asset_pool(layout_assets, export_layout="web")
    featured_scored = [
        a
        for a in pool
        if a.get("userTier") == "featured"
        and effective_cover_score(a, "web", featured_weight=1.35) > 0
    ]
    assert featured_scored
    best = max(
        featured_scored,
        key=lambda a: effective_cover_score(a, "web", featured_weight=1.35),
    )
    assert cover_id == best["id"]
    assert cover_id in (trip.get("curation") or {}).get("featuredCoverPool") or []


def test_ac_df_03_chapter_hero_prefers_featured_in_curate(tmp_path: Path) -> None:
    """AC-DF-03: featuredHeroByChapter heroes are featured when landscape heroes exist."""
    trip_json, trip, trip_dir = _ingest_dual_trip(tmp_path, "ac-df-03", _dual_album(tmp_path, 2, 5))
    run_curate(trip, export_layout="web", layout_engine="screens", apply_layout=True, trip_dir=trip_dir)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)

    heroes = (trip.get("curation") or {}).get("featuredHeroByChapter") or {}
    assert heroes
    assets_by_id = _asset_map(trip)
    featured_ids = {a["id"] for a in trip["assets"] if a.get("userTier") == "featured"}
    assert featured_ids
    # Multi-chapter trips may assign material heroes where a bucket has no eligible featured.
    assert any(assets_by_id[hid].get("userTier") == "featured" for hid in heroes.values())


def test_ac_df_04_no_featured_skips_tier_curation_fields(tmp_path: Path) -> None:
    """AC-DF-04: legacy single-folder ingest — no featured tier curation block."""
    root = tmp_path / "flat"
    root.mkdir()
    for i in range(5):
        _write_photo(root / f"p-{i:02d}.jpg")

    trips = tmp_path / "trips"
    trip_json = create_trip("ac-df-04", trips, title="legacy", export_layout="web")
    trip_dir = trips / "ac-df-04"
    trip = TripService().load(trip_json)
    ingest_into_trip(trip, trip_dir, from_dir=root, dedupe=False, generate_crops=False)
    run_curate(trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)

    curation = trip.get("curation") or {}
    assert "userTierSummary" not in curation
    assert "featuredCoverPool" not in curation
    assert all(a.get("userTier", "material") == "material" for a in trip["assets"])


def test_ac_df_05_cross_folder_dedupe_upgrades_to_featured(tmp_path: Path) -> None:
    """AC-DF-05: alias of cross-folder contentSig dedupe → userTier featured."""
    test_cross_folder_dedupe_upgrades_to_featured(tmp_path)


def test_ac_df_06_portrait_featured_web_cover_fallback_warns(tmp_path: Path) -> None:
    """AC-DF-06: all featured portrait → web cover from material + WARN."""
    trip_json, trip, trip_dir = _ingest_dual_trip(
        tmp_path, "ac-df-06", _portrait_featured_album(tmp_path)
    )
    result = run_curate(
        trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir
    )
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)

    cover = _asset_map(trip)[trip["coverAssetId"]]
    assert cover.get("userTier") == "material"
    warnings = (trip.get("curation") or {}).get("warnings") or result.warnings or []
    assert any("竖图" in w and "回退" in w for w in warnings)


def test_ac_df_07_schema_with_import_source(tmp_path: Path) -> None:
    """AC-DF-07: alias of schema validation with importSource."""
    test_ingest_import_source_passes_schema(tmp_path)


def test_ac_df_08_legacy_assets_without_user_tier_field(tmp_path: Path) -> None:
    """AC-DF-08: trips without userTier metadata still curate (regression)."""
    root = tmp_path / "legacy-no-tier"
    root.mkdir()
    for i in range(5):
        _write_photo(root / f"p-{i:02d}.jpg")

    trips = tmp_path / "trips"
    trip_json = create_trip("ac-df-08", trips, title="old", export_layout="web")
    trip_dir = trips / "ac-df-08"
    trip = TripService().load(trip_json)
    ingest_into_trip(trip, trip_dir, from_dir=root, dedupe=False, generate_crops=False)
    for asset in trip["assets"]:
        asset.pop("userTier", None)
        asset.pop("userTierSource", None)
        asset.pop("importSource", None)
    result = run_curate(
        trip, export_layout="web", layout_engine="screens", apply_layout=False, trip_dir=trip_dir
    )
    assert result.chapter_count >= 1
    assert "userTierSummary" not in (trip.get("curation") or {})


def test_ac_df_ingest_warns_when_featured_count_above_limit(tmp_path: Path) -> None:
    """Appendix A §3 rule 5: featured count above threshold → tier_warnings (no hard reject)."""
    root = tmp_path / "many-featured"
    feat = root / "精选"
    mat = root / "素材上传"
    for i in range(4):
        _write_photo(mat / f"mat-{i:02d}.jpg")
    for i in range(6):
        _write_photo(feat / f"feat-{i:02d}.jpg", color=(180 + i, 70, 50))

    trips = tmp_path / "trips"
    trip_json = create_trip("ac-df-warn", trips, title="warn")
    trip_dir = trips / "ac-df-warn"
    trip = TripService().load(trip_json)
    ingest_cfg = replace(get_config().ingest, warn_featured_count_above=5)
    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=root,
        dedupe=False,
        generate_crops=False,
        cfg=ingest_cfg,
        max_photos=20,
    )
    assert result.stats["userTierSummary"]["featured"] == 6
    assert any("超过建议上限" in w for w in result.stats.get("tier_warnings") or [])


def test_g2_serve_promote_asset_to_featured() -> None:
    """P5 · G2 serve tier: material → featured with userTierSource=user."""
    from travelogue.media.user_tier import TIER_MATERIAL, TIER_SOURCE_USER, promote_assets_to_featured

    trip = {
        "assets": [
            {"id": "a1", "userTier": TIER_MATERIAL},
            {"id": "a2", "userTier": TIER_MATERIAL},
        ],
        "curation": {},
    }
    promoted = promote_assets_to_featured(trip, ["a1", "missing"])
    assert promoted == ["a1"]
    assert trip["assets"][0]["userTier"] == "featured"
    assert trip["assets"][0]["userTierSource"] == TIER_SOURCE_USER
    summary = trip["curation"]["userTierSummary"]
    assert summary["featured"] == 1
    assert summary["material"] == 1


def test_tier_patch_via_serve_api_shape() -> None:
    from travelogue.web.tier_patch import TierPatchError, apply_tier_promotions

    trip = {"assets": [{"id": "x1", "userTier": "material"}]}
    promoted = apply_tier_promotions(trip, ["x1"])
    assert promoted == ["x1"]
    with pytest.raises(TierPatchError):
        apply_tier_promotions(trip, ["nope"])
