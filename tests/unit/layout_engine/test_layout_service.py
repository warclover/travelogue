"""Layout service: apply_layout_to_trip and CLI-facing helpers."""

from __future__ import annotations

from travelogue.media.image_ops import classify_aspect
from travelogue.services.layout import (
    apply_layout_from_album_build,
    apply_layout_to_trip,
    extract_ordered_asset_ids,
)
from travelogue.services.validate import validate_trip


def _asset(aid: str, w: int, h: int) -> dict:
    return {
        "id": aid,
        "type": "image",
        "sourceFile": f"source/{aid}.jpg",
        "displayFile": f"assets/{aid}.webp",
        "width": w,
        "height": h,
        "aspectKind": classify_aspect(w, h),
    }


def _trip_with_assets(
    specs: list[tuple[int, int]],
    *,
    export_layout: str = "mobile",
    cover_index: int = 0,
) -> dict:
    assert len(specs) >= 5, "need >=5 assets for layout tests (4+ body after cover)"
    assets = [_asset(f"a{i}", w, h) for i, (w, h) in enumerate(specs)]
    cover = assets[cover_index]["id"]
    body_ids = [a["id"] for a in assets if a["id"] != cover]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    chapters, summary_dict, _ = apply_layout_from_album_build(
        body_ids,
        assets,
        aspects,
        export_layout=export_layout,
    )
    return {
        "version": "0.2",
        "tripId": "layout-test",
        "templateId": "visual-journal",
        "exportLayout": export_layout,
        "meta": {
            "title": "排版测试",
            "dateStart": "2025-01-01",
            "dateEnd": "2025-01-02",
            "places": ["测试"],
            "tone": "relaxed",
        },
        "coverAssetId": cover,
        "assets": assets,
        "chapters": chapters,
        "curation": {"orientationSummary": summary_dict},
        "epilogue": "",
        "privacy": {"level": "private", "stripExifOnExport": True, "confirmedAt": None},
        "pipeline": {"status": "structure_draft", "locks": {"structure": False, "copy": False}, "runs": []},
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
    }


def _all_items(trip: dict) -> list[dict]:
    out: list[dict] = []
    for ch in trip["chapters"]:
        out.extend(ch["items"])
    return out


def test_extract_ordered_asset_ids_dedupes():
    trip = {
        "chapters": [
            {
                "items": [
                    {"type": "media-card", "assetId": "a"},
                    {"type": "media-row", "assetIds": ["b", "c"]},
                    {"type": "media-card", "assetId": "a"},
                ]
            }
        ]
    }
    assert extract_ordered_asset_ids(trip) == ["a", "b", "c"]


def test_apply_layout_mobile_landscape_stacks_in_one_column():
    # Mobile 横版改为「一列纵向拼图」：连续横图组成 landscape-triple/-pair（窄屏 CSS
    # 强制单列纵向叠放），三列优先。除封面 a0 外有 7 张横图 → 三联 + 三联 + 尾部单卡。
    specs = [(1200, 800)] * 8
    trip = _trip_with_assets(specs, export_layout="mobile")
    rows = [it for it in _all_items(trip) if it.get("type") == "media-row"]
    assert [it.get("rowLayout") for it in rows] == ["landscape-triple", "landscape-triple"]
    cards = [it for it in _all_items(trip) if it.get("type") == "media-card"]
    assert len(cards) == 1


def test_apply_layout_web_portrait_mosaic():
    # MCS unified planner: web export uses screens engine; mixed 3P+2L windows
    # land in product-default MCS patterns (3P2L hero-quad under experiments).
    from dataclasses import replace

    from travelogue.config import get_config
    from travelogue.config.mosaic import TemplateContractConfig
    from travelogue.layout_engine.mosaic.constants import (
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
    )
    from travelogue.layout_engine.mosaic.runtime import (
        reset_mosaic_config_override,
        set_mosaic_config_override,
    )

    specs = [
        (1200, 800),
        (900, 1600),
        (900, 1600),
        (900, 1600),
        (1200, 800),
        (1200, 800),
    ]
    # Isolate from local config.yaml template_contract dogfood.
    set_mosaic_config_override(
        replace(
            get_config().mosaic,
            template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        )
    )
    try:
        trip = _trip_with_assets(specs, export_layout="web", cover_index=0)
        result = apply_layout_to_trip(trip, export_layout="web")
        assert result.orientation_summary["export_layout"] == "web"
        screens = [sc for ch in trip["chapters"] for sc in ch.get("screens") or []]
        mcs_ids = {
            "screen-portrait-3",
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
            PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
        }
        assert any(sc.get("patternId") in mcs_ids for sc in screens)
        placed = {sl.get("assetId") for sc in screens for sl in sc.get("slots") or []}
        assert {"a1", "a2", "a3"} <= placed
    finally:
        reset_mosaic_config_override()


def test_apply_layout_panorama_not_in_triple():
    specs = [
        (1200, 800),
        (3000, 1000),
        (1200, 800),
        (1200, 800),
        (1200, 800),
        (900, 1600),
    ]
    trip = _trip_with_assets(specs, export_layout="mobile", cover_index=0)
    items = _all_items(trip)
    triples = [it for it in items if it.get("rowLayout") == "landscape-triple"]
    for row in triples:
        assert "a1" not in row.get("assetIds", [])
    pano_cards = [
        it
        for it in items
        if it.get("type") == "media-card" and (it.get("layout") or {}).get("slot") == "panorama"
    ]
    assert pano_cards
    assert any(it.get("assetId") == "a1" for it in pano_cards)


def test_apply_layout_preserves_chapter_titles():
    trip = _trip_with_assets([(1200, 800)] * 16, export_layout="mobile")
    for i, ch in enumerate(trip["chapters"]):
        ch["title"] = f"T{i + 1}"
    apply_layout_to_trip(trip, export_layout="mobile", preserve_titles=True)
    titles = [ch["title"] for ch in trip["chapters"]]
    assert len(titles) >= 3
    assert titles[0] == "T1"
    assert trip["curation"]["layoutPlanVersion"] == "0.2.0"


def test_validate_rejects_unknown_row_layout():
    trip = _trip_with_assets([(1200, 800)] * 8, export_layout="web")
    for ch in trip["chapters"]:
        for it in ch["items"]:
            if it.get("type") == "media-row":
                it["rowLayout"] = "invalid-grid"
    errs = validate_trip(trip, level="manifest")
    assert any("rowLayout" in e for e in errs)


def test_layout_trip_passes_schema():
    trip = _trip_with_assets([(1200, 800)] * 16, export_layout="mobile")
    apply_layout_to_trip(trip, export_layout="mobile")
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert not errs, errs
