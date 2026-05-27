"""Reading compat aliases and schema (PRD-EXPERIENCE P4)."""

from __future__ import annotations

import json

from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.reading_profile import resolve_reading_payload
from travelogue.services.validate import validate_trip

SCHEMA = ROOT / "schemas" / "trip.schema.json"
JOURNAL = TEMPLATE_VISUAL_JOURNAL / "journal.hbs"
BREATH_CSS = TEMPLATE_VISUAL_JOURNAL / "breath.css"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"


def test_export_breath_mode_alias_maps_to_scroll_breath() -> None:
    trip = {
        "export": {
            "breathMode": "flow",
            "folioMode": "full",
        }
    }
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["scroll"]["breath"] == "flow"
    assert payload["scroll"]["folio"] == "full"


def test_reading_scroll_overrides_deprecated_aliases() -> None:
    trip = {
        "export": {
            "breathMode": "soft",
            "folioMode": "lite",
            "reading": {"scroll": {"breath": "cinematic", "folio": "off"}},
        }
    }
    payload = resolve_reading_payload(trip, export_mode="draft", export_layout_override="web")
    assert payload["scroll"]["breath"] == "cinematic"
    assert payload["scroll"]["folio"] == "off"


def test_schema_accepts_deprecated_export_aliases() -> None:
    trip = json.loads((ROOT / "schemas" / "fixtures" / "trip.render_golden.json").read_text(encoding="utf-8"))
    trip.setdefault("export", {}).update(
        {
            "breathMode": "soft",
            "folioMode": "lite",
            "reading": {"profile": "default_hybrid"},
        }
    )
    trip["curation"] = {
        "userTierSummary": {"featured": 2, "material": 8, "featuredInLayout": 2},
        "featuredHeroByChapter": {"ch-01": "cover"},
        "featuredCoverPool": ["cover"],
        "folioPlan": {
            "index": True,
            "foreword": False,
            "featuredGrid": False,
            "featuredGridAssetIds": [],
            "plateAssetIds": ["cover"],
        },
    }
    errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert errs == []


def test_schema_defines_tier_and_folio_plan_fields() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    curation = schema["$defs"]["tripCuration"]["properties"]
    export = schema["$defs"]["exportOptions"]["properties"]
    assert "breathMode" in export
    assert "folioMode" in export
    assert "userTierSummary" in curation
    assert "featuredHeroByChapter" in curation
    assert "featuredCoverPool" in curation
    assert "folioPlan" in curation


def test_ac_exp_10_reduced_motion_guards() -> None:
    """AC-EXP-10: reduced-motion disables breath motion paths."""
    breath_js = BREATH_JS.read_text(encoding="utf-8")
    screenplay_js = SCREENPLAY_JS.read_text(encoding="utf-8")
    css = BREATH_CSS.read_text(encoding="utf-8")
    assert "prefersReducedMotion" in breath_js
    assert "prefers-reduced-motion: reduce" in css
    assert "prefersReducedMotion" in screenplay_js
    assert "prefers-reduced-motion: reduce" in screenplay_js


def test_ac_exp_12_no_js_readable_fallbacks() -> None:
    """AC-EXP-12: static HTML readable without JS (breath reveal fallback)."""
    journal = JOURNAL.read_text(encoding="utf-8")
    css = BREATH_CSS.read_text(encoding="utf-8")
    assert 'class="no-js"' in journal
    assert "document.documentElement.classList.remove('no-js')" in journal
    assert "scripting: none" in css
    assert "html.no-js .breath-reveal" in css
    chapter = (TEMPLATE_VISUAL_JOURNAL / "partials" / "chapter.hbs").read_text(encoding="utf-8")
    assert 'data-block="chapter-header"' in chapter
    assert "{{> chapter}}" in journal
