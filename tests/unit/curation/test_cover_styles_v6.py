"""Cover Styles V6 · Engine registry, resolve/legacy, Studio options (M1)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.cover_engine import (
    assignable_style_ids,
    get_default_style_id,
    get_style,
    is_assignable,
    legacy_map,
    list_assignable_styles,
    list_preview_matrix,
    resolve_cover_opening_style,
    resolve_style_id,
    studio_style_options,
)
from travelogue.render.assemble import build_render_context
from travelogue.render.golden_regression import load_golden_trip
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_entry import build_entry


def test_assignable_styles_are_v6_five() -> None:
    ids = assignable_style_ids()
    assert ids == (
        "veil-footer",
        "folio-overlap",
        "band-cut",
        "cameo-aperture",
        "type-monument",
    )
    assert all(is_assignable(i) for i in ids)
    assert not is_assignable("card-br")
    assert not is_assignable("split-mat")


def test_default_style_is_veil_footer() -> None:
    assert get_default_style_id() == "veil-footer"


def test_legacy_map_table() -> None:
    assert legacy_map("card-br") == "veil-footer"
    assert legacy_map("split-mat") == "folio-overlap"
    assert legacy_map("magazine-head") == "folio-overlap"
    assert legacy_map("veil-footer") is None
    assert legacy_map("") is None


def test_resolve_style_id_legacy_and_default() -> None:
    assert resolve_style_id(None) == "veil-footer"
    assert resolve_style_id("") == "veil-footer"
    assert resolve_style_id("nope") == "veil-footer"
    assert resolve_style_id("card-br") == "veil-footer"
    assert resolve_style_id("split-mat") == "folio-overlap"
    assert resolve_style_id("magazine-head") == "folio-overlap"
    assert resolve_style_id("band-cut") == "band-cut"


def test_resolve_cover_opening_style_from_trip() -> None:
    assert resolve_cover_opening_style({}) == "veil-footer"
    assert resolve_cover_opening_style({"meta": {"coverOpeningStyle": "card-br"}}) == "veil-footer"
    assert (
        resolve_cover_opening_style({"meta": {"coverOpeningStyle": "type-monument"}})
        == "type-monument"
    )


def test_studio_style_options_active_only_with_blurb() -> None:
    opts = studio_style_options()
    assert [o["id"] for o in opts] == list(assignable_style_ids())
    for o in opts:
        assert o["label"]
        assert o["blurb"]
        assert "sort_order" in o
    # A/G disambiguation labels
    by_id = {o["id"]: o for o in opts}
    assert by_id["veil-footer"]["label"] == "沉浸题签"
    assert by_id["type-monument"]["label"] == "海报巨字"


def test_preview_matrix_each_active_has_fixture() -> None:
    rows = list_preview_matrix()
    assert len(rows) == 5
    for row in rows:
        assert row["fixture_ref"]
        assert row["blurb"]


def test_profiles_exist_for_active() -> None:
    for rec in list_assignable_styles():
        assert get_style(rec.id) is not None
        assert rec.profile.title_max_lines >= 2
    assert get_style("type-monument").profile.title_max_lines == 3


def test_create_trip_placeholder_veil_footer(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    trip_json = create_trip("csv-v6-new", trips_dir, title="林芝", place="林芝")
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assert data["meta"]["coverOpeningStyle"] == "veil-footer"


def test_build_render_context_maps_legacy() -> None:
    trip = load_golden_trip()
    trip.setdefault("meta", {})["coverOpeningStyle"] = "magazine-head"
    ctx = build_render_context(trip, export_mode="draft")
    assert ctx["coverOpeningStyle"] == "folio-overlap"


def test_studio_entry_exposes_cover_style_options() -> None:
    trip = load_golden_trip()
    payload = build_entry(trip, "golden")
    assert payload["coverOpeningStyle"] == resolve_cover_opening_style(trip)
    assert [o["id"] for o in payload["coverStyleOptions"]] == list(assignable_style_ids())
    assert "coverJointLocked" in payload
    assert "coverLegacyMapped" in payload
    assert "coverStyleLabel" in payload


def test_schema_accepts_v5_and_v6_cover_opening_style() -> None:
    """AC-CSV6-05 · V6∪V5 enum 均可 schema validate。"""
    from travelogue.services.validate import validate_trip

    trip = load_golden_trip()
    for style in (
        "veil-footer",
        "band-cut",
        "card-br",
        "split-mat",
        "magazine-head",
    ):
        trip.setdefault("meta", {})["coverOpeningStyle"] = style
        errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
        assert not any("coverOpeningStyle" in e for e in errs), (style, errs)


def test_schema_accepts_cover_joint_lock_fields() -> None:
    from travelogue.services.validate import validate_trip

    trip = load_golden_trip()
    trip.setdefault("curation", {})
    trip["curation"]["coverJointLocked"] = True
    trip["curation"]["coverStyleExplain"] = {
        "source": "joint-v6",
        "styleId": "veil-footer",
        "assetId": "a1",
        "joint": 0.5,
        "quality": 0.4,
        "fit": 0.3,
        "avoidPenalty": 0.0,
        "lowConfidence": False,
    }
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert not any("coverJoint" in e or "coverStyleExplain" in e for e in errs), errs


def test_set_style_status_retired_drops_assignable() -> None:
    """AC-CSV6-41 · retired 后不可新选；仍可 resolve。"""
    from travelogue.cover_engine.registry import reset_registry_for_tests, set_style_status

    try:
        set_style_status("band-cut", "retired")
        assert not is_assignable("band-cut")
        assert "band-cut" not in assignable_style_ids()
        assert resolve_style_id("band-cut") == "band-cut"
        assert get_style("band-cut") is not None
    finally:
        reset_registry_for_tests()


def test_journal_css_v6_tokens_and_skins() -> None:
    """AC-CSV6-10～14 / 12 · token + 五款选择器 + band 72%。"""
    from travelogue.paths import JOURNAL_CSS

    css = JOURNAL_CSS.read_text(encoding="utf-8")
    for needle in (
        "--cover-font-title",
        "--cover-veil-fog-height",
        "--cover-band-center: 72%",
        "--cover-folio-fade",
        "--cover-cameo-ring",
        "--cover-monument-dim",
        "--cover-dock-safe",
        "--cover-panel-z",
        'data-cover-opening="veil-footer"',
        'data-cover-opening="folio-overlap"',
        'data-cover-opening="band-cut"',
        'data-cover-opening="cameo-aperture"',
        'data-cover-opening="type-monument"',
        "border-radius: 50%",
        "min-width: 64rem",
        "cover-opening__placeholder-badge",
    ):
        assert needle in css, needle


def test_no_hardcoded_v6_tuple_outside_engine() -> None:
    """AC-CSV6-42 · 业务真相源不得散落第二份五元组（粗检 services/web）。"""
    from travelogue.paths import ROOT

    banned = '("veil-footer", "folio-overlap", "band-cut", "cameo-aperture", "type-monument")'
    hits: list[str] = []
    for rel in (
        "travelogue/services",
        "travelogue/web",
        "travelogue/curation",
        "travelogue/render",
    ):
        root = ROOT / rel
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if "cover_engine" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            if banned in text:
                hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
