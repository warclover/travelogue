"""P5 · reading experience enhancements (PRD-EXPERIENCE deferred items)."""

from __future__ import annotations

from travelogue.paths import TEMPLATE_VISUAL_JOURNAL
from travelogue.render.reading_profile import (
    SURFACE_MOBILE,
    resolve_reading_payload,
)

SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"
SCREENPLAY_HASH_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay-hash.js"
SCREENPLAY_BOOKMARKS_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay-bookmarks.js"
BREATH_GSAP_JS = TEMPLATE_VISUAL_JOURNAL / "breath-gsap.js"
JOURNAL_HBS = TEMPLATE_VISUAL_JOURNAL / "journal.hbs"


def test_present_deep_link_implementation() -> None:
    js = SCREENPLAY_HASH_JS.read_text(encoding="utf-8")
    main = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "TraveloguePresentHash" in js
    assert "parse" in js
    assert "#present/" in js
    assert "TraveloguePresentHash" in main


def test_present_deep_link_default_enabled() -> None:
    payload = resolve_reading_payload({"chapters": [], "assets": []}, export_layout_override="web")
    assert payload["present"]["deepLink"] is True


def test_present_deep_link_can_disable() -> None:
    payload = resolve_reading_payload(
        {"export": {"reading": {"present": {"deepLink": False}}}},
        export_layout_override="web",
    )
    assert payload["present"]["deepLink"] is False


def test_breath_engine_native_by_default() -> None:
    payload = resolve_reading_payload({"chapters": [], "assets": []}, export_layout_override="web")
    assert payload["scroll"]["breathEngine"] == "native"


def test_breath_engine_gsap_option() -> None:
    payload = resolve_reading_payload(
        {"export": {"reading": {"scroll": {"breath": "cinematic", "breathEngine": "gsap"}}}},
        export_layout_override="web",
    )
    assert payload["scroll"]["breathEngine"] == "gsap"


def test_breath_gsap_runtime_detection() -> None:
    js = BREATH_GSAP_JS.read_text(encoding="utf-8")
    assert "useGsapEngine" in js
    assert "setupCinematicGsap" in js
    assert "breathEngine" in js


def test_journal_loads_screenplay_modules() -> None:
    hbs = JOURNAL_HBS.read_text(encoding="utf-8")
    assert "screenplay-hash.js" in hbs
    assert "screenplay-bookmarks.js" in hbs
    assert "screenplay.js" in hbs


def test_journal_injects_gsap_cdn_when_enabled() -> None:
    hbs = JOURNAL_HBS.read_text(encoding="utf-8")
    assert "includeBreathGsapRuntime" in hbs
    assert "gsap.min.js" in hbs
    assert "ScrollTrigger.min.js" in hbs


def test_mobile_legacy_default_unchanged() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        index_name=SURFACE_MOBILE,
    )
    assert payload["profile"] == "legacy"
    assert payload["scroll"]["breath"] == "off"
    assert payload["scroll"]["folio"] == "off"


def test_mobile_profile_override_enables_hybrid() -> None:
    payload = resolve_reading_payload(
        {
            "export": {
                "reading": {
                    "mobileProfile": "default_hybrid",
                }
            }
        },
        index_name=SURFACE_MOBILE,
    )
    assert payload["profile"] == "default_hybrid"
    assert payload["scroll"]["breath"] == "soft"
    assert payload["scroll"]["folio"] == "lite"
    assert payload["scroll"]["snap"] == "proximity"
