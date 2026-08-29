"""Present ↔ scroll sync and longshot teardown (PRD-EXPERIENCE E3/E4)."""

from __future__ import annotations

from travelogue.paths import TEMPLATE_VISUAL_JOURNAL
from travelogue.render.reading_profile import resolve_reading_payload

SCREENPLAY_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay.js"
SCREENPLAY_BOOKMARKS_JS = TEMPLATE_VISUAL_JOURNAL / "screenplay-bookmarks.js"
BREATH_JS = TEMPLATE_VISUAL_JOURNAL / "breath.js"
LONGSHOT_JS = TEMPLATE_VISUAL_JOURNAL / "longshot.js"


def test_screenplay_sync_scroll_on_exit_implementation() -> None:
    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "syncScrollToSlide" in js
    assert "syncScrollOnExitEnabled" in js
    assert "scrollIntoView" in js
    assert "syncScrollOnExit" in js


def test_default_hybrid_present_sync_enabled() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        export_mode="draft",
        export_layout_override="web",
    )
    assert payload["present"]["syncScrollOnExit"] is True


def test_legacy_present_sync_disabled() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        export_mode="draft",
        export_layout_override="web",
        reading_profile_override="legacy",
    )
    assert payload["present"]["syncScrollOnExit"] is False


def test_breath_destroy_clears_inline_motion() -> None:
    js = BREATH_JS.read_text(encoding="utf-8")
    assert "destroy" in js
    assert 'el.style.opacity = ""' in js or "el.style.opacity" in js
    assert "TravelogueBreath" in js
    assert "destroyLenis" in js
    assert "destroyScrub" in js


def test_scrub_teardown_in_longshot_restore_path() -> None:
    js = LONGSHOT_JS.read_text(encoding="utf-8")
    assert "TravelogueBreath.destroy" in js


def test_longshot_teardown_and_restore_api() -> None:
    js = LONGSHOT_JS.read_text(encoding="utf-8")
    assert "teardownReadingMotion" in js
    assert "restoreReadingMotion" in js
    assert "TravelogueReading.restore" in js
    assert "restoreReadingMotion()" in js
    assert "window.scrollTo(0, prevScroll)" in js


def test_screenplay_skip_aux_blocks_implementation() -> None:
    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "skipAuxBlocksEnabled" in js
    assert "skipAuxBlocks" in js
    assert "presentSlideSelector" in js
    assert "screenplay-aux-slide" in js


def test_folio_partials_mark_present_aux() -> None:
    from travelogue.paths import TEMPLATE_VISUAL_JOURNAL

    for name in (
        "partials/cover-hero.hbs",
        "partials/trip-index.hbs",
        "partials/featured-grid.hbs",
        "partials/foreword-spread.hbs",
        "partials/screen-spread.hbs",
        "partials/epilogue-screen.hbs",
    ):
        text = (TEMPLATE_VISUAL_JOURNAL / name).read_text(encoding="utf-8")
        assert 'data-present-aux="true"' in text
    journal = (TEMPLATE_VISUAL_JOURNAL / "journal.hbs").read_text(encoding="utf-8")
    assert 'data-block="epilogue" data-present-aux="true"' in journal


def test_screenplay_present_bookmarks_implementation() -> None:
    js = SCREENPLAY_BOOKMARKS_JS.read_text(encoding="utf-8")
    main = SCREENPLAY_JS.read_text(encoding="utf-8")
    assert "TraveloguePresentBookmarks" in js
    assert "slideIndexForAsset" in js
    assert "slideIndexForChapterKey" in js
    assert "wire" in js
    assert "TraveloguePresentBookmarks" in main
    assert "goTo" in main
    layout = (TEMPLATE_VISUAL_JOURNAL / "partials/layout-screen.hbs").read_text(
        encoding="utf-8"
    )
    assert "data-asset-ids" in layout


def test_present_config_payload_fields() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        export_mode="share",
        export_layout_override="web",
    )
    present = payload["present"]
    assert present["autoAdvance"] is True
    assert present["manualControls"] is True
    assert present["tapZoneNav"] is True
    assert present["clickStage"] == "pause"
    assert present["loop"] is False


def test_default_hybrid_scroll_keyboard_nav() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        export_mode="draft",
        export_layout_override="web",
    )
    assert payload["scroll"]["keyboardNav"] is True


def test_screenplay_manual_nav_implementation() -> None:
    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    toolbar = (TEMPLATE_VISUAL_JOURNAL / "partials/screenplay-toolbar.hbs").read_text(
        encoding="utf-8"
    )
    journal = (TEMPLATE_VISUAL_JOURNAL / "journal.hbs").read_text(encoding="utf-8")
    assert "manualControlsEnabled" in js
    assert "autoAdvanceEnabled" in js
    assert "tapZoneNavEnabled" in js
    assert "clickStageMode" in js
    assert "scheduleAdvance" in js
    assert 'data-screenplay-action="prev"' in toolbar
    assert "scroll-nav.js" in journal


def test_present_preview_uses_share_profile() -> None:
    payload = resolve_reading_payload(
        {"chapters": [], "assets": []},
        export_mode="present-preview",
        export_layout_override="web",
        index_name="index-present.html",
    )
    assert payload["profile"] == "performance"


def test_screenplay_hash_entry_requires_user_gesture_gate() -> None:
    js = SCREENPLAY_JS.read_text(encoding="utf-8")
    toolbar = (TEMPLATE_VISUAL_JOURNAL / "partials/screenplay-toolbar.hbs").read_text(
        encoding="utf-8"
    )
    assert "showGate" in js
    assert "userGesture" in js
    assert "enteredFullscreen" in js
    assert "requestFullscreenPreferred" in js
    assert 'id="screenplay-gate"' in toolbar
    assert "data-screenplay-gate-start" in toolbar
    assert "armFromHash" in js
    assert "player.showGate(idx)" in js
    assert "player.start(idx)" not in js
    assert "this.gate.contains(focused)" in js
    assert 'this.gate.removeAttribute("aria-hidden")' in js
