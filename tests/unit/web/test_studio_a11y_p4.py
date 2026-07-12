"""Phase 4 static a11y guards (AC-P4-A11Y-01/02/03)."""



from __future__ import annotations

from tests._repo_root import repo_root
from tests.unit.web._preview_toolbar_css import read_preview_toolbar_css_bundle
from tests.unit.web._studio_home_v2_css import read_studio_home_v2_css_bundle

ROOT = repo_root(__file__)
STUDIO = ROOT / "templates" / "studio"


def test_ac_p4_a11y_01_accent_ink_on_gold_controls() -> None:
    """Gold CTA text uses dark ink (#1a1408), not low-contrast gold-on-gold."""
    css = read_preview_toolbar_css_bundle(STUDIO)
    assert "#1a1408" in css.lower()


def test_ac_p4_a11y_02_import_wizard_dialog_semantics() -> None:
    """Import Wizard exposes dialog semantics + labelled title (v2 primary surface)."""
    html = (STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-import-wizard"' in html
    assert 'role="dialog"' in html
    assert 'aria-labelledby="v2-wizard-title-pick"' in html
    wizard = (STUDIO / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    assert "trapFocus" in wizard


def test_ac_p4_a11y_03_reduced_motion_disables_shimmer() -> None:
    """prefers-reduced-motion disables Ken Burns / loading shimmer animations."""
    css = read_studio_home_v2_css_bundle(STUDIO)
    assert "prefers-reduced-motion: reduce" in css
    assert ".v2-loading__bar" in css
    block_start = css.index("@media (prefers-reduced-motion: reduce)")
    block = css[block_start : block_start + 400]
    assert "animation: none" in block
