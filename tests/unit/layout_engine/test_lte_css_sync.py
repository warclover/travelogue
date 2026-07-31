"""W4: journal-screens.css LTE marker single authority (R-P16-14)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
)
from travelogue.layout_templates.css_gen import (
    LTE_MARKER_END,
    LTE_MARKER_START,
    OVERLAYS_MARKER_END,
    OVERLAYS_MARKER_START,
    TrailingLegacyCssError,
    _truncate_trailing_legacy_after_overlays,
    lte_grid_classes_outside_marker,
    sync_journal_screens_css,
)
from travelogue.layout_templates.registry import get_layout_template, reset_engine_cache_for_tests
from travelogue.paths import JOURNAL_SCREENS_CSS


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.fixture
def journal_css() -> str:
    return Path(JOURNAL_SCREENS_CSS).read_text(encoding="utf-8")


@pytest.mark.unit
def test_journal_has_lte_generated_marker(journal_css: str) -> None:
    assert LTE_MARKER_START in journal_css
    assert LTE_MARKER_END in journal_css
    assert journal_css.index(LTE_MARKER_START) < journal_css.index(LTE_MARKER_END)


@pytest.mark.unit
def test_flagship_and_hero_not_duplicated_outside_marker(journal_css: str) -> None:
    dupes = lte_grid_classes_outside_marker(journal_css)
    flagship = get_layout_template(PATTERN_MOSAIC_5_2P3L_EQUAL).render_grid_class
    hero = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4).render_grid_class
    assert flagship not in dupes
    assert hero not in dupes


@pytest.mark.unit
def test_flagship_and_hero_css_inside_marker(journal_css: str) -> None:
    start = journal_css.index(LTE_MARKER_START)
    end = journal_css.index(LTE_MARKER_END)
    inside = journal_css[start:end]
    flagship = get_layout_template(PATTERN_MOSAIC_5_2P3L_EQUAL).render_grid_class
    hero = get_layout_template(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4).render_grid_class
    assert flagship in inside
    assert hero in inside


@pytest.mark.unit
def test_no_lte_grid_duplicates_outside_marker(journal_css: str) -> None:
    assert lte_grid_classes_outside_marker(journal_css) == []


@pytest.mark.unit
def test_journal_has_overlay_marker(journal_css: str) -> None:
    assert OVERLAYS_MARKER_START in journal_css
    assert OVERLAYS_MARKER_END in journal_css
    assert 'data-pattern="screen-portrait-2-landscape-2"' in journal_css


@pytest.mark.unit
def test_no_legacy_css_after_overlay_marker(journal_css: str) -> None:
    end = journal_css.index(OVERLAYS_MARKER_END) + len(OVERLAYS_MARKER_END)
    tail = journal_css[end:].strip()
    assert tail == ""


@pytest.mark.unit
def test_journal_css_handwritten_inventory_bounded() -> None:
    from scripts.lte_journal_css_audit import audit_journal_css

    report = audit_journal_css(Path(JOURNAL_SCREENS_CSS))
    assert report["duplicateGridClassesOutsideMarker"] == []
    assert report["outsideGeneratedGridClassCount"] == 0


@pytest.mark.unit
def test_journal_has_base_slot_image_containment(journal_css: str) -> None:
    """Regression: P16 sync must not drop universal slot img sizing (object-fit + 100%)."""
    assert ".layout-slot__img--cover" in journal_css
    assert "object-fit: cover" in journal_css
    assert "width: 100%" in journal_css
    assert "height: 100%" in journal_css
    start = journal_css.index(LTE_MARKER_START)
    preamble = journal_css[:start]
    assert ".layout-slot__img" in preamble
    assert "min-height: 0" in preamble
    assert "layout-slot--blurred-fill" in preamble
    assert 'html[data-layout-engine="screens"] .layout-slot__blur' in preamble


@pytest.mark.unit
def test_journal_has_portrait_stage_tokens_and_dense_grid_overlays(journal_css: str) -> None:
    """Regression: overlay block keeps portrait tokens + mosaic/2x2 slot fill rules."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "--portrait-stage-vh:" in overlays
    assert "layout-screen__grid--mosaic-" in overlays
    assert "layout-screen__grid--2x2 .layout-slot__img--cover" in overlays


@pytest.mark.unit
def test_universal_portrait_contain_row_rules(journal_css: str) -> None:
    """All 2/3-up contain rows share top-anchor + intrinsic height overrides."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "Universal portrait contain rows" in overlays
    assert ':not([data-layout-hint="person-pair"])' in overlays
    assert '.layout-screen__grid--2col:has(.layout-slot__img--contain)' in overlays
    assert '.layout-screen__grid--3col:has(.layout-slot__img--contain)' in overlays
    assert "grid-template-rows: auto;" in overlays
    assert "grid-template-rows: repeat(2, auto)" in overlays
    assert ".layout-screen__grid--3x2:has(.layout-slot__img--contain)" in overlays
    assert ".layout-slot > .layout-slot__img--contain" in overlays
    assert "object-position: top center" in overlays
    assert ':not([data-layout-hint="portrait-row-editorial"])' in overlays


@pytest.mark.unit
def test_portrait_row_editorial_overlay_rules(journal_css: str) -> None:
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert 'data-pattern="screen-portrait-3-editorial"' in overlays
    assert "--portrait-row-editorial-width:" in overlays
    assert "object-position: bottom center" in overlays
    assert "layout-slot__img--cover" in overlays
    assert "--editorial-row-ar" in overlays


@pytest.mark.unit
def test_editorial_4mix_overlay_rules(journal_css: str) -> None:
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert 'data-pattern="screen-editorial-4mix"' in overlays
    assert "layout-screen__grid--editorial-4mix" in overlays
    assert "--editorial-4mix-width:" in overlays
    assert ':not([data-pattern="screen-editorial-4mix"])' in overlays
    assert ':not([data-layout-hint="editorial-4mix"])' in overlays


@pytest.mark.unit
def test_portrait_pair_screen_collapses_stage(journal_css: str) -> None:
    """screen-portrait-2 + person-pair must not keep phantom grid rows / vertical padding."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert '[data-pattern="screen-portrait-2"]:not([data-layout-hint])' in overlays
    assert "grid-template-rows: auto;" in overlays
    assert 'padding: 0 var(--portrait-row-inset);' in overlays


@pytest.mark.unit
def test_portrait_quad_2x2_contain_collapses_stage(journal_css: str) -> None:
    """screen-portrait-4 (2×2 contain) must drop the forced 9:16 stage box.

    Regression for consecutive two-portrait-pair collages reading as one tall
    box with large top/bottom blank.
    """
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert (
        '[data-pattern="screen-portrait-4"]:not([data-layout-hint])'
        ":has(.layout-slot__img--contain)" in overlays
    )
    assert '.layout-screen__grid--2x2:has(.layout-slot__img--contain)' in overlays
    assert "aspect-ratio: unset;" in overlays


@pytest.mark.unit
def test_plate_portrait_contain_collapses_stage(journal_css: str) -> None:
    """folio lite screen-plate + portrait contain must share portrait-1 stage collapse.

    Regression: chapter opener plate promoted from screen-portrait-1 left a tall
    native-aspect box with side bands and bottom blank (asset-027 class).
    """
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert (
        ':is([data-pattern="screen-portrait-1"], [data-pattern="screen-plate"])'
        in overlays
    )
    assert "screen-plate (folio lite chapter opener)" in overlays


@pytest.mark.unit
def test_moment_exif_bar_rules_in_overlays(journal_css: str) -> None:
    """P23 moment EXIF footnote CSS must live inside @journal-overlays (Phase 16 sync)."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "inline moment EXIF bar" in overlays
    assert ".moment-exif-bar" in overlays
    assert "background: #0a0a0a" in overlays
    assert ".moment-exif-line" in overlays
    assert ".layout-slot:has(.moment-exif-bar)" in overlays


@pytest.mark.unit
def test_chapter_ticket_stub_rules_in_overlays(journal_css: str) -> None:
    """Ticket-stub chapter separator CSS must live inside @journal-overlays (Phase 16 sync)."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "ticket-stub chapter separator (scheme B)" in overlays
    assert '.chapter-separator--ticket[data-block="chapter-separator"]' in overlays
    assert ".chapter-separator--ticket .chapter-separator__title" in overlays
    assert ':not(.chapter-separator--ticket) .chapter-separator__title' in overlays


@pytest.mark.unit
def test_mosaic_fixed_stage_keeps_aspect_with_contain(journal_css: str) -> None:
    """Fixed-stage mosaics must keep 16:9 when a contain class is present.

    Regression: height:auto + align-items:start punched holes / jagged bottoms in
    W3 rail / weighted / 5-main-portrait composites (demo-2025 dogfood).
    """
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert '[data-pattern^="screen-mosaic-"]:has(.layout-slot__img--contain)' in overlays
    assert "aspect-ratio: var(--screen-aspect, 16 / 9)" in overlays
    assert "grid-template-rows: repeat(3, auto)" not in overlays
    # Contain class still fills the cell (cover + focal) so bottoms align
    assert (
        '[class*="layout-screen__grid--mosaic-"] .layout-slot .layout-slot__img--contain'
        in overlays
    )


@pytest.mark.unit
def test_megc_equal_2x2_fixed_stage_keeps_grid_with_contain(journal_css: str) -> None:
    """MEGC PR-A / AC-MEGC-01: equal 2×2 fixed stage must not grow past the stage on contain.

    Regression: generic --2x2:has(contain)→rows:auto;height:auto let landscape-4
    grids exceed the 16:9 stage; overflow:hidden then clipped the bottom row
    (demo-2019 ch-02-sc-06 / assets 086,088,089,091).

    SSOT is journal-screens-overlays.css — export --sync-journal replaces the
    @journal-overlays block, so MEGC must live there (not only in journal-screens.css).
    """
    from pathlib import Path

    overlays_ssot = Path("templates/visual-journal/journal-screens-overlays.css").read_text(
        encoding="utf-8"
    )
    assert "MEGC · PR-A" in overlays_ssot

    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "MEGC · PR-A" in overlays
    for pattern in ("screen-landscape-4", "screen-portrait-2-landscape-2"):
        assert f'[data-pattern="{pattern}"] .layout-screen__grid--2x2:has(.layout-slot__img--contain)' in overlays
        assert f'[data-pattern="{pattern}"] .layout-screen__grid .layout-slot:has(> .layout-slot__img--contain)' in overlays
        assert f'[data-pattern="{pattern}"] .layout-screen__grid .layout-slot > .layout-slot__img--contain' in overlays
    assert "grid-template-rows: repeat(2, minmax(0, 1fr))" in overlays
    # Generic auto-grow must opt these patterns out (specificity / cascade guard).
    assert (
        ':not([data-pattern="screen-landscape-4"]):not([data-pattern="screen-portrait-2-landscape-2"])'
        in overlays
    )


@pytest.mark.unit
def test_landscape_6_fixed_3x2_keeps_stage_with_contain(journal_css: str) -> None:
    """Tri-col revive: landscape-6 must opt out of generic --3x2 contain-collapse."""
    from pathlib import Path

    overlays_ssot = Path("templates/visual-journal/journal-screens-overlays.css").read_text(
        encoding="utf-8"
    )
    assert 'data-pattern="screen-landscape-6"' in overlays_ssot
    assert (
        ':not([data-pattern="screen-landscape-6"])'
        in overlays_ssot
    )

    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert (
        '[data-pattern="screen-landscape-6"] .layout-screen__grid--3x2:has(.layout-slot__img--contain)'
        in overlays
    )
    assert "grid-template-rows: repeat(2, minmax(0, 1fr))" in overlays


@pytest.mark.unit
def test_megc_does_not_block_portrait4_intrinsic_contain(journal_css: str) -> None:
    """MEGC PR-A / AC-MEGC-02: portrait-4 keep intrinsic height:auto under contain."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert (
        '[data-pattern="screen-portrait-4"]:not([data-layout-hint]):has(.layout-slot__img--contain)'
        in overlays
    )
    # MEGC include list must not name portrait-4 as a fixed-stage override target.
    megc_start = overlays.index("MEGC · PR-A")
    megc_slice = overlays[megc_start : megc_start + 2500]
    assert 'INCLUDE (fixed 16:9 stage): screen-landscape-4, screen-portrait-2-landscape-2' in megc_slice
    assert "screen-portrait-4" in megc_slice  # listed under EXCLUDE
    assert 'data-pattern="screen-portrait-4"' not in megc_slice.split("EXCLUDE")[0]


@pytest.mark.unit
def test_mosaic_portrait_contain_top_anchor(journal_css: str) -> None:
    """Regression: hero mosaic bottom tiles use contain + top center, not focal stretch."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert "layout-screen__grid--mosaic-5-main-hero-plus-4" in overlays
    assert "grid-template-rows: minmax(0, 1fr) minmax(0, 1fr) auto" in overlays
    assert ":not([data-role=\"main\"]) .layout-slot__img--contain" in overlays
    assert "object-position: top center" in overlays


# --- T-LRG-11 / AC-LRG-03: automated negative guard tests ------------------
#
# Hard constraint (PRD §3.2.3): these tests operate ONLY on in-memory strings
# or tmp_path file copies. They must never write to / delete-and-restore the
# real templates/visual-journal/journal-screens*.css files.

_TICKET_STUB_KEY_SELECTORS = (
    'chapter-separator--ticket[data-block="chapter-separator"]',
    ".chapter-separator--ticket .chapter-separator__title",
    ':not(.chapter-separator--ticket) .chapter-separator__title',
)


def _missing_overlay_selectors(overlays_text: str, required: tuple[str, ...]) -> list[str]:
    """AC-LRG-03 guard-detection helper: which required key selectors are absent."""
    return [sel for sel in required if sel not in overlays_text]


@pytest.mark.unit
def test_overlay_ticket_removal_fails_guard(journal_css: str) -> None:
    """AC-LRG-03: deleting the ticket-stub overlay selector must be detectable.

    Simulates the regression from the 2026-07 incident (ticket-stub overlay block
    silently missing) by tampering an *in-memory copy* of the overlay text — the
    real overlays.css / journal-screens.css on disk are only ever read here.
    """
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    assert _missing_overlay_selectors(overlays, _TICKET_STUB_KEY_SELECTORS) == []

    tampered = overlays.replace(
        '.chapter-separator--ticket[data-block="chapter-separator"]',
        '.chapter-separator--REMOVED[data-block="chapter-separator"]',
    )
    missing = _missing_overlay_selectors(tampered, _TICKET_STUB_KEY_SELECTORS)
    assert missing == ['chapter-separator--ticket[data-block="chapter-separator"]']


@pytest.mark.unit
def test_overlay_exif_removal_fails_guard(journal_css: str) -> None:
    """AC-LRG-03 companion: same guard-detection sanity check for the EXIF overlay."""
    ostart = journal_css.index(OVERLAYS_MARKER_START)
    oend = journal_css.index(OVERLAYS_MARKER_END)
    overlays = journal_css[ostart:oend]
    exif_selectors = (".moment-exif-bar", ".layout-slot:has(.moment-exif-bar)")
    assert _missing_overlay_selectors(overlays, exif_selectors) == []

    tampered = overlays.replace(".moment-exif-bar", ".REMOVED-exif-bar")
    missing = _missing_overlay_selectors(tampered, exif_selectors)
    assert ".moment-exif-bar" in missing


# --- T-LRG-12 / AC-LRG-12: export fail-fast on marker-external legacy CSS ---


@pytest.mark.unit
def test_truncate_trailing_legacy_raises_by_default() -> None:
    text = (
        f"{OVERLAYS_MARKER_START}\n.overlay-rule {{ color: blue; }}\n{OVERLAYS_MARKER_END}\n"
        "\n.legacy-leftover { color: red; }\n"
    )
    with pytest.raises(TrailingLegacyCssError) as exc_info:
        _truncate_trailing_legacy_after_overlays(text)
    assert "legacy-leftover" in str(exc_info.value)


@pytest.mark.unit
def test_truncate_trailing_legacy_warn_only_still_truncates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    text = (
        f"{OVERLAYS_MARKER_START}\n.overlay-rule {{ color: blue; }}\n{OVERLAYS_MARKER_END}\n"
        "\n.legacy-leftover { color: red; }\n"
    )
    result = _truncate_trailing_legacy_after_overlays(text, on_trailing_legacy="warn")
    assert ".legacy-leftover" not in result
    assert result.rstrip().endswith(OVERLAYS_MARKER_END)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "legacy-leftover" in err


@pytest.mark.unit
def test_truncate_trailing_legacy_ignores_comment_and_whitespace_only_tail() -> None:
    text = (
        f"{OVERLAYS_MARKER_START}\n.overlay-rule {{ color: blue; }}\n{OVERLAYS_MARKER_END}\n"
        "\n/* trailing comment only, no rule */\n  \n"
    )
    result = _truncate_trailing_legacy_after_overlays(text)  # must not raise
    assert result.rstrip().endswith(OVERLAYS_MARKER_END)


@pytest.mark.unit
def test_sync_journal_screens_css_strict_raises_on_trailing_legacy(tmp_path: Path) -> None:
    """T-LRG-12 integration: fail-fast fires through the real sync pipeline.

    Only a tmp_path copy is written/read; the repo's real journal-screens.css is
    never touched, and journal-screens-overlays.css is only ever *read* here.
    """
    journal_text = (
        'html[data-layout="web"] .layout-screen__grid--1col,\n'
        'html[data-layout="auto"] .layout-screen__grid--1col {\n'
        "  grid-template-columns: 1fr;\n"
        "}\n\n"
        f"{OVERLAYS_MARKER_START}\n/* placeholder */\n{OVERLAYS_MARKER_END}\n"
        "\n.legacy-leftover-rule { color: red; }\n"
    )
    journal_path = tmp_path / "journal-screens.css"
    journal_path.write_text(journal_text, encoding="utf-8")

    with pytest.raises(TrailingLegacyCssError) as exc_info:
        sync_journal_screens_css({}, journal_path=journal_path)
    assert "legacy-leftover-rule" in str(exc_info.value)
    # Fail-fast must not leave a partially-written file behind.
    assert journal_path.read_text(encoding="utf-8") == journal_text


@pytest.mark.unit
def test_sync_journal_screens_css_warn_bypass_writes_truncated_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    journal_text = (
        'html[data-layout="web"] .layout-screen__grid--1col,\n'
        'html[data-layout="auto"] .layout-screen__grid--1col {\n'
        "  grid-template-columns: 1fr;\n"
        "}\n\n"
        f"{OVERLAYS_MARKER_START}\n/* placeholder */\n{OVERLAYS_MARKER_END}\n"
        "\n.legacy-leftover-rule { color: red; }\n"
    )
    journal_path = tmp_path / "journal-screens.css"
    journal_path.write_text(journal_text, encoding="utf-8")

    sync_journal_screens_css({}, journal_path=journal_path, on_trailing_legacy="warn")

    written = journal_path.read_text(encoding="utf-8")
    assert ".legacy-leftover-rule" not in written
    assert "WARNING" in capsys.readouterr().err
