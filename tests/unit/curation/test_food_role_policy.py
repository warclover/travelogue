"""FRP · Food Role Policy acceptance tests (AC-FRP-01..12)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from travelogue.config import config_override, get_config
from travelogue.config.moment import MomentConfig
from travelogue.cover_engine.closing.pick import pick_closing_with_meta
from travelogue.cover_engine.lock import set_closing_locked, set_opening_locked
from travelogue.curation.curate import sync_trip_covers
from travelogue.curation.curate_scoring import (
    effective_cover_score,
    pick_cover_asset_id,
    pick_cover_asset_id_with_meta,
)
from travelogue.curation.food_policy import is_food_asset
from travelogue.curation.moment_scoring import build_moment_pool, peak_moment_score
from travelogue.layout_engine.planner.screen_planner import (
    FOOD_GRID_LAYOUT_HINT,
    _pick_chapter_hero,
    plan_screens_for_chapter,
)
from travelogue.services.moment_curation import (
    apply_moment_signature,
    validate_moment_asset_id,
)


def _img(
    aid: str,
    *,
    food: bool = False,
    w: int = 1600,
    h: int = 900,
    sharp: float = 200.0,
    tags: list[str] | None = None,
) -> dict:
    asset: dict = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": w,
        "height": h,
        "mediaClass": "photo",
        "quality": {"sharpness": sharp, "overall": 0.8},
        "userTier": "material",
    }
    if food:
        asset["tags"] = tags or ["food"]
        asset["subjectClass"] = "food"
        asset["subjectConfidence"] = 0.9
    else:
        asset["tags"] = tags or ["landscape"]
        asset["subjectClass"] = "landscape"
        asset["subjectConfidence"] = 0.9
    return asset


def _with_food_role(**kwargs):
    cfg = get_config()
    role = replace(cfg.curate.food_role, **kwargs)
    return replace(cfg, curate=replace(cfg.curate, food_role=role))


def test_ac_frp_01_cover_demotes_high_score_food() -> None:
    food = _img("food", food=True, sharp=900.0)
    land = _img("land", food=False, sharp=120.0)
    with config_override(_with_food_role(cover_policy="demote", cover_multiplier=0.15)):
        cover_id, meta = pick_cover_asset_id_with_meta([food, land], export_layout="web")
    assert cover_id == "land"
    assert (meta.get("foodPolicy") or {}).get("cover") == "demote"
    assert effective_cover_score(food, "web") < effective_cover_score(land, "web")


def test_ac_frp_02_all_food_cover_fallback() -> None:
    assets = [_img(f"f{i}", food=True, sharp=300.0 + i) for i in range(3)]
    with config_override(_with_food_role(cover_policy="exclude")):
        cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="web")
    assert cover_id.startswith("f")
    assert meta.get("coverFoodFallback") is True
    assert (meta.get("foodPolicy") or {}).get("cover") == "fallback"


def test_ac_frp_03_opening_lock_preserves_food_cover() -> None:
    """Locked web opening must survive sync_trip_covers (override > demote)."""
    assets = [
        _img("food", food=True, sharp=900.0),
        _img("land", food=False, sharp=50.0),
    ]
    trip = {
        "exportLayout": "web",
        "coverAssetId": "food",
        "assets": assets,
        "curation": {"coverByLayout": {"web": "food"}},
    }
    set_opening_locked(trip, True)
    with config_override(_with_food_role(cover_policy="demote", cover_multiplier=0.15)):
        cover_id = sync_trip_covers(trip, export_layout="web", assets=assets)
    assert cover_id == "food"
    assert trip["coverAssetId"] == "food"
    assert (trip.get("curation") or {}).get("foodPolicy", {}).get("cover") == "override"


def test_ac_frp_04_closing_demotes_food() -> None:
    trip = {
        "coverAssetId": "cover",
        "assets": [
            _img("cover", food=False),
            _img("food", food=True, sharp=900.0),
            _img("land", food=False, sharp=100.0),
        ],
        "chapters": [
            {
                "screens": [
                    {"slots": [{"assetId": "food"}]},
                    {"slots": [{"assetId": "land"}]},
                ]
            }
        ],
        "curation": {},
    }
    with config_override(_with_food_role(closing_policy="demote", closing_multiplier=0.15)):
        result = pick_closing_with_meta(trip, prefer_landscape=True, require_hard=False)
    assert result["closing_asset_id"] == "land"
    assert (trip.get("curation") or {}).get("foodPolicy", {}).get("closing") == "demote"


def test_ac_frp_04b_closing_lock_marks_override() -> None:
    from travelogue.cover_engine.api import resolve_closing

    trip = {
        "coverAssetId": "cover",
        "assets": [
            _img("cover", food=False),
            _img("food", food=True, sharp=900.0),
            _img("land", food=False, sharp=100.0),
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "land"}]}]}],
        "curation": {"closingAssetId": "food"},
    }
    set_closing_locked(trip, True)
    decision = resolve_closing(trip, layout="web", force=False, persist=False)
    assert decision.closing_asset_id == "food"
    assert (trip.get("curation") or {}).get("foodPolicy", {}).get("closing") == "override"


def test_ac_frp_05_chapter_hero_skips_food() -> None:
    assets = {
        "food": _img("food", food=True, w=2000, h=1000, sharp=900.0),
        "land": _img("land", food=False, w=1800, h=1000, sharp=100.0),
    }
    aspects = {"food": "landscape", "land": "landscape"}
    with config_override(_with_food_role(hero_policy="skip")):
        picked = _pick_chapter_hero(["food", "land"], aspects, assets)
    assert picked is not None
    assert picked[0] == "land"


def test_ac_frp_06_food_excluded_from_moment_pool() -> None:
    trip = {"coverAssetId": "cover"}
    assets = (
        [_img("cover", food=False)]
        + [_img(f"a{i}", food=False, sharp=0.5 + i * 0.01) for i in range(20)]
        + [_img("food", food=True, sharp=0.99)]
    )
    for a in assets:
        a["quality"]["sharpness"] = float(a["quality"]["sharpness"])
    cfg = MomentConfig(auto_disable_small_trip=False, min_score=0.0)
    with config_override(_with_food_role(allow_food_in_moment=False)):
        pool = build_moment_pool(trip, assets, cfg=cfg)
    assert "food" not in pool
    assert (trip.get("curation") or {}).get("foodPolicy", {}).get("moment") == "excluded"


def test_ac_frp_06b_moment_score_soft_demotes_food() -> None:
    """§4.4 double-insurance: food_moment_score_multiplier applies in scoring."""
    from travelogue.curation.moment_scoring import _build_score_ctx

    food = _img("food", food=True, sharp=0.9)
    land = _img("land", food=False, sharp=0.9)
    assets = [food, land]
    trip: dict = {}
    cfg = MomentConfig()
    with config_override(
        _with_food_role(allow_food_in_moment=True, moment_multiplier=0.05)
    ):
        ctx = _build_score_ctx(
            cfg=cfg,
            layout_assets=assets,
            chapters=None,
            trip=trip,
            arc_profile="dynamic",
            include_on_screen=False,
            featured_weight=1.0,
            aesthetic_enabled=False,
            meta_places=None,
            memory_anchors=None,
            hero_asset_ids=set(),
        )
        food_score = peak_moment_score(food, ctx)
        land_score = peak_moment_score(land, ctx)
    assert food_score < land_score


def test_ac_frp_07_studio_can_override_food_moment() -> None:
    trip = {
        "assets": [_img("food", food=True), _img("a1", food=False)],
        "curation": {"momentPoolIds": ["a1"]},
    }
    assert validate_moment_asset_id(trip, "food") is None
    apply_moment_signature(trip, "food")
    assert trip["momentAssetId"] == "food"
    assert "food" in (trip["curation"].get("momentPoolIds") or [])
    assert trip["curation"].get("momentFoodOverride") is True


def test_ac_frp_08_grids_decision_logged() -> None:
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    ids = ["f1", "f2"]
    assets = {
        aid: {
            **_img(aid, food=True),
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    aspects = {aid: "square" for aid in ids}
    trip: dict = {"curation": {}}
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        trip=trip,
    )
    assert any(sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT for sc in screens)
    grids = (trip.get("curation") or {}).get("foodPolicy", {}).get("grids") or []
    assert len(grids) >= 1
    assert set(grids[0]["assetIds"]) == {"f1", "f2"}
    assert grids[0]["layoutHint"] == FOOD_GRID_LAYOUT_HINT


def test_ac_frp_10_single_food_not_grid_cover_or_moment() -> None:
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    food = {
        **_img("f1", food=True, sharp=50.0),
        "takenAt": base.isoformat().replace("+00:00", "Z"),
    }
    lands = []
    for i in range(20):
        a = _img(f"l{i}", food=False, sharp=200.0 + i)
        a["takenAt"] = (base + timedelta(seconds=i + 1)).isoformat().replace("+00:00", "Z")
        lands.append(a)
    assets_map = {food["id"]: food, **{a["id"]: a for a in lands}}
    aspects = {aid: ("square" if aid == "f1" else "landscape") for aid in assets_map}
    layout_assets = [food, *lands]
    for a in layout_assets:
        a["quality"]["sharpness"] = float(a["quality"]["sharpness"])

    screens = plan_screens_for_chapter(
        list(assets_map.keys()),
        aspects,
        assets=assets_map,
        include_chapter_hero=False,
    )
    assert not any(sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT for sc in screens)

    with config_override(_with_food_role(cover_policy="demote", cover_multiplier=0.15)):
        cover_id = pick_cover_asset_id(layout_assets, export_layout="web")
    assert cover_id != "f1"
    assert not is_food_asset(next(a for a in layout_assets if a["id"] == cover_id))

    trip = {"coverAssetId": cover_id}
    cfg = MomentConfig(auto_disable_small_trip=False, min_score=0.0)
    with config_override(_with_food_role(allow_food_in_moment=False)):
        pool = build_moment_pool(trip, layout_assets, cfg=cfg)
    assert "f1" not in pool


def test_ac_frp_11_legacy_thresholds_when_configured() -> None:
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    ids = ["f1", "f2"]
    assets = {
        aid: {
            **_img(aid, food=True),
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i, aid in enumerate(ids)
    }
    aspects = {aid: "square" for aid in ids}
    legacy = _with_food_role(
        cover_policy="off",
        grid_min_items=3,
        grid_max_interruptions=1,
    )
    with config_override(legacy):
        screens = plan_screens_for_chapter(
            ids,
            aspects,
            assets=assets,
            include_chapter_hero=False,
            app_config=legacy,
        )
        cover = pick_cover_asset_id(
            [_img("food", food=True, sharp=900.0), _img("land", food=False, sharp=50.0)],
            export_layout="web",
        )
    assert not any(sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT for sc in screens)
    assert cover == "food"


def test_ac_frp_12_tags_only_food_still_demoted() -> None:
    food = _img("food", food=False, sharp=900.0, tags=["meal"])
    food.pop("subjectClass", None)
    food.pop("subjectConfidence", None)
    land = _img("land", food=False, sharp=100.0)
    assert is_food_asset(food)
    with config_override(_with_food_role(cover_policy="demote", cover_multiplier=0.15)):
        cover_id = pick_cover_asset_id([food, land], export_layout="web")
    assert cover_id == "land"
