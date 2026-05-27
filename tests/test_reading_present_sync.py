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
