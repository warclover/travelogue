"""Layout density preference (PRD-FINE-CRAFT-LAYOUT-DENSITY)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AppConfig, LayoutConfig
from travelogue.curation.layout_density import (
    MIN_PHOTOS_COLLAGE_FULL_EFFECT,
    layout_density_effect,
    layout_density_params,
    nine_quota_adjusted,
    normalize_layout_density,
    resolve_import_layout_density,
)
from travelogue.layout_contract.planner_state import (
    ScreenLayoutPlannerState,
    nine_grid_limits_for_trip,
    pattern_slot_count,
)
from travelogue.layout_engine.intent_hints import apply_editorial_intent_hints
from travelogue.layout_engine.planner.screen_planner import attach_screens_to_chapters
from travelogue.services.trip import apply_intent
from travelogue.services.validate import validate_trip
from travelogue.web.studio_intent_telemetry import build_studio_intent_telemetry

PP_THRESHOLD = 0.10


def test_normalize_layout_density_invalid() -> None:
    from travelogue.config.errors import ConfigError
    import pytest

    assert normalize_layout_density("hero_first") == "hero_first"
    assert normalize_layout_density(None) == "balanced"
    assert normalize_layout_density("") == "balanced"
    with pytest.raises(ConfigError, match="layoutDensity"):
        normalize_layout_density("foo")


def test_resolve_import_layout_density_modes() -> None:
    from travelogue.config.errors import ConfigError
    import pytest

    assert resolve_import_layout_density("hero_first", import_mode="fine_craft") == "hero_first"
    assert resolve_import_layout_density("hero_first", import_mode="quick_share") is None
    with pytest.raises(ConfigError, match="layoutDensity"):
        resolve_import_layout_density("foo", import_mode="fine_craft")


def test_apply_intent_layout_density() -> None:
    from travelogue.config.errors import ConfigError
    import pytest

    trip: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip, layout_density="collage_first")
    assert trip["intent"]["layoutDensity"] == "collage_first"
    with pytest.raises(ConfigError, match="layoutDensity"):
        apply_intent(trip, layout_density="not-valid")
    assert trip["intent"]["layoutDensity"] == "collage_first"
    apply_intent(trip, layout_density=None)
    assert "layoutDensity" not in trip["intent"]


def test_quick_share_clears_layout_density() -> None:
    trip: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip, layout_density="hero_first")
    cleared = resolve_import_layout_density(None, import_mode="quick_share")
    apply_intent(trip, layout_density=cleared)
    assert "layoutDensity" not in trip["intent"]
    assert layout_density_params(trip).density == "balanced"


def test_nine_quota_hero_first_lower_than_balanced() -> None:
    base_lo, base_hi = nine_grid_limits_for_trip(80)
    hero = layout_density_params({"intent": {"layoutDensity": "hero_first"}})
    h_lo, h_hi = hero.adjust_nine_limits(base_lo, base_hi)
    assert h_lo <= base_lo
    assert h_hi <= base_hi


def test_nine_quota_collage_first_higher_than_balanced() -> None:
    base_lo, base_hi = nine_grid_limits_for_trip(80)
    collage = layout_density_params({"intent": {"layoutDensity": "collage_first"}})
    c_lo, c_hi = collage.adjust_nine_limits(base_lo, base_hi)
    assert c_lo >= base_lo
    assert c_hi >= base_hi


def test_layout_density_effect_limited() -> None:
    assert (
        layout_density_effect(20, "collage_first", import_mode="fine_craft") == "limited"
    )
    assert layout_density_effect(20, "collage_first", import_mode="quick_share") == "ignored_quick"


def test_ac_ld_13_layout_density_disabled_via_config() -> None:
    cfg = replace(
        AppConfig(),
        layout=replace(LayoutConfig(), layout_density_enabled=False),
    )
    trip = {"intent": {"layoutDensity": "hero_first"}}
    assert layout_density_params(trip, app_cfg=cfg).density == "balanced"


def test_intent_hints_schema_accepts_layout_fields() -> None:
    trip = {
        "version": 1,
        "tripId": "ld-hints",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "coverAssetId": "a001",
        "chapters": [],
        "privacy": {"visibility": "private"},
        "pipeline": {"status": "structure_draft"},
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
        "meta": {
            "title": "测",
            "places": ["旅途"],
            "dateStart": "2025-01-01",
            "dateEnd": "2025-01-02",
            "tone": "warm",
        },
        "intent": {"layoutDensity": "hero_first"},
        "assets": [],
    }
    apply_editorial_intent_hints(trip)
    hints = (trip.get("curation") or {}).get("intentHints") or {}
    assert hints.get("layoutDensity") == "hero_first"
    assert hints.get("preferMosaic") is False
    errors = [e for e in validate_trip(trip, level="schema") if "intentHints" in e]
    assert errors == [], errors


def _synthetic_landscape_chapter(n_assets: int = 50) -> tuple[list[dict], dict[str, str], list[dict]]:
    aspects = {f"a{i:03d}": "landscape" for i in range(1, n_assets + 1)}
    asset_ids = list(aspects.keys())
    chapters = [
        {
            "id": "ch-01",
            "index": 1,
            "patternId": "open",
            "title": "测试",
            "lead": "",
            "items": [{"type": "media-card", "assetId": aid} for aid in asset_ids],
            "curation": {},
        }
    ]
    assets = [
        {"id": aid, "takenAt": f"2025-04-02T10:{i % 60:02d}:00Z"}
        for i, aid in enumerate(asset_ids)
    ]
    return chapters, aspects, assets


def _screen_slot_ratios(chapters: list[dict]) -> tuple[float, float, int]:
    single = dense = total = 0
    for ch in chapters:
        for sc in ch.get("screens") or []:
            total += 1
            n = pattern_slot_count(str(sc.get("patternId") or "")) or len(
                sc.get("slots") or []
            )
            if n <= 1:
                single += 1
            if n >= 4:
                dense += 1
    if total == 0:
        return 0.0, 0.0, 0
    return single / total, dense / total, total


def _plan_density(density: str, n_assets: int = 50) -> list[dict]:
    chapters, aspects, assets = _synthetic_landscape_chapter(n_assets)
    return attach_screens_to_chapters(
        [dict(chapters[0])],
        aspects,
        assets=assets,
        plan_scope="chapter",
        trip_photo_total=n_assets,
        layout_density=density,
    )


# Density preferences: hero_first down-weights dense quota (LTN C2 still attempts
# MCS); collage_first reorders MCS windows to avoid stranding trailing singles.
def test_ac_ld_06_hero_first_single_slot_ratio_up_10pp() -> None:
    balanced = _plan_density("balanced", 80)
    hero = _plan_density("hero_first", 80)
    b_single, _, b_total = _screen_slot_ratios(balanced)
    h_single, _, h_total = _screen_slot_ratios(hero)
    assert b_total >= 4 and h_total >= 4
    assert h_single - b_single >= PP_THRESHOLD


def test_ac_ld_07_collage_first_dense_ratio_up_10pp() -> None:
    # 全横图 synthetic：44 张(≥MIN_PHOTOS_COLLAGE_FULL_EFFECT)时 balanced 贪婪打包遗留
    # 2 个单槽屏(landscape-1)，collage 把尾窗补成 landscape-4 密集屏。50 张恰好 5×9+1×5
    # 完美打包、balanced 已满密度，无法体现分化，故改用 44。
    balanced = _plan_density("balanced", 44)
    collage = _plan_density("collage_first", 44)
    _, b_dense, b_total = _screen_slot_ratios(balanced)
    _, c_dense, c_total = _screen_slot_ratios(collage)
    assert b_total >= 4 and c_total >= 4
    assert round(c_dense - b_dense, 4) >= PP_THRESHOLD


def test_ac_ld_mcs_density_divergence_three_way() -> None:
    """MCS path: hero_first ↑ singles, collage_first ↑ dense, balanced in between."""
    # 44 张：避开 50 张完美打包退化点（见 test_ac_ld_07）。
    b_single, b_dense, _ = _screen_slot_ratios(_plan_density("balanced", 44))
    h_single, _h_dense, _ = _screen_slot_ratios(_plan_density("hero_first", 44))
    _c_single, c_dense, _ = _screen_slot_ratios(_plan_density("collage_first", 44))
    assert h_single - b_single >= PP_THRESHOLD
    assert round(c_dense - b_dense, 4) >= PP_THRESHOLD


def test_ac_ld_04_quick_share_equivalent_to_balanced() -> None:
    """Without intent field, planner matches explicit balanced."""
    with_intent = _plan_density("balanced", 40)
    trip_cleared: dict = {"meta": {"places": ["旅途"]}}
    apply_intent(trip_cleared, layout_density=None)
    assert "layoutDensity" not in trip_cleared.get("intent", {})
    chapters, aspects, assets = _synthetic_landscape_chapter(40)
    no_intent = attach_screens_to_chapters(
        [dict(chapters[0])],
        aspects,
        assets=assets,
        plan_scope="chapter",
        trip_photo_total=40,
        layout_density=layout_density_params(trip_cleared).density,
    )

    def patterns(chs: list[dict]) -> list[str]:
        out: list[str] = []
        for ch in chs:
            for sc in ch.get("screens") or []:
                out.append(str(sc.get("patternId") or ""))
        return out

    assert patterns(no_intent) == patterns(with_intent)


def test_ac_ld_08_planner_state_hero_suppresses_prefer_nine() -> None:
    state = ScreenLayoutPlannerState.from_trip_total(80, density="hero_first")
    base = ScreenLayoutPlannerState.from_trip_total(80, density="balanced")
    if base.needs_nine_quota():
        assert state.should_prefer_nine() is False


def test_ac_ld_10_small_album_collage_limited_effect() -> None:
    n = MIN_PHOTOS_COLLAGE_FULL_EFFECT - 1
    assert layout_density_effect(n, "collage_first", import_mode="fine_craft") == "limited"
    assert layout_density_effect(n, "hero_first", import_mode="fine_craft") == "full"


def test_nine_quota_adjusted_collage_first() -> None:
    adj = nine_quota_adjusted(80, "collage_first")
    assert adj == {"min": 3, "max": 6, "baseMin": 2, "baseMax": 5}


def test_ac_ld_09_telemetry_includes_nine_quota_adjusted() -> None:
    trip = {
        "tripId": "ld-tel",
        "assets": [{"id": "a1"}] * 40,
        "intent": {"layoutDensity": "collage_first"},
        "chapters": [],
    }
    payload = build_studio_intent_telemetry(
        trip, import_mode="fine_craft", layout_density="collage_first"
    )
    assert payload["nineQuotaAdjusted"] == nine_quota_adjusted(40, "collage_first")


def test_ac_ld_08_chapter_hero_and_face_contain_three_densities() -> None:
    from tests._golden.helpers import (
        build_chapter_hero_layout_trip,
        build_person_portrait_layout_trip,
        plan_legacy_screens,
    )
    from travelogue.curation.asset_subject import asset_has_person

    def chapter_openings(chapters: list[dict]) -> dict[str, str]:
        out: dict[str, str] = {}
        for ch in chapters:
            screens = ch.get("screens") or []
            if screens:
                out[str(ch.get("id") or "")] = str(screens[0].get("patternId") or "")
        return out

    hero_buckets, hero_aspects, hero_assets = build_chapter_hero_layout_trip()
    hero_openings: dict[str, dict[str, str]] = {}
    for density in ("balanced", "hero_first", "collage_first"):
        chapters = plan_legacy_screens(
            hero_buckets, hero_aspects, hero_assets, layout_density=density
        )
        hero_openings[density] = chapter_openings(chapters)
    assert (
        hero_openings["balanced"]
        == hero_openings["hero_first"]
        == hero_openings["collage_first"]
    )
    assert hero_openings["balanced"].get("ch-01") == "screen-landscape-1"

    p_buckets, p_aspects, p_assets = build_person_portrait_layout_trip()
    assets_map = {a["id"]: a for a in p_assets}
    person_fits: list[str] = []
    for density in ("balanced", "hero_first", "collage_first"):
        chapters = plan_legacy_screens(
            p_buckets, p_aspects, p_assets, layout_density=density
        )
        for ch in chapters:
            for sc in ch.get("screens") or []:
                for slot in sc.get("slots") or []:
                    aid = slot.get("assetId")
                    if aid and asset_has_person(assets_map.get(aid)):
                        person_fits.append(str(slot.get("fit") or ""))
    assert person_fits and all(f == "contain" for f in person_fits)


def test_demo_day_equivalent_fixture_at_least_35_photos() -> None:
    """CI stand-in when trips/demo-day-3 is not in the repo."""
    from tests._golden.helpers import build_layout_density_golden_trip

    _, _, assets = build_layout_density_golden_trip()
    assert len(assets) >= MIN_PHOTOS_COLLAGE_FULL_EFFECT
