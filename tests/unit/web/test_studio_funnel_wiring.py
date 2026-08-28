"""MET-01 · funnel_first_preview is registered and fired from preview chrome."""

from __future__ import annotations

from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS
from travelogue.domain.studio_funnel import FUNNEL_FIRST_PREVIEW_EVENT, WIZARD_PREVIEW_EVENT
from travelogue.paths import ROOT

_ANALYTICS = ROOT / "templates/studio/js/analytics.js"
_INIT = ROOT / "templates/studio/preview-toolbar/init-v3.js"
_WIZARD = ROOT / "templates/studio/homepage-v2/import-wizard.js"


def test_funnel_first_preview_allowlisted_on_both_sides() -> None:
    analytics = _ANALYTICS.read_text(encoding="utf-8")
    assert FUNNEL_FIRST_PREVIEW_EVENT in ALLOWED_STUDIO_HOMEPAGE_EVENTS
    assert f'"{FUNNEL_FIRST_PREVIEW_EVENT}"' in analytics


def test_preview_toolbar_fires_funnel_first_preview_once() -> None:
    text = _INIT.read_text(encoding="utf-8")
    start = text.find("function trackFunnelFirstPreview")
    assert start != -1
    chunk = text[start : start + 900]
    assert f'trackStudioEvent("{FUNNEL_FIRST_PREVIEW_EVENT}"' in chunk
    assert "travelogue.funnel.firstPreview." in chunk
    assert "isSharePreview()" in chunk
    assert 'source: "preview_toolbar"' in chunk
    assert "displayTitle" not in chunk
    assert "path" not in chunk


def test_wizard_preview_loaded_is_not_reused_as_first_preview() -> None:
    wizard = _WIZARD.read_text(encoding="utf-8")
    assert f'trackStudioEvent("{WIZARD_PREVIEW_EVENT}"' in wizard
    assert FUNNEL_FIRST_PREVIEW_EVENT not in wizard
