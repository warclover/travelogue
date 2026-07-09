"""Phase 11 · copy-toggle / photos-only regression for decorLine CSS."""



from __future__ import annotations

from tests._repo_root import repo_root

REPO = repo_root(__file__)
CSS = REPO / "templates" / "visual-journal" / "copy-display.css"


def test_copy_display_hides_decor_line() -> None:
    text = CSS.read_text(encoding="utf-8")
    for selector in (
        'html[data-copy-display="photos"] [data-block="decor-line"]',
        'html[data-photos-only="on"] [data-block="decor-line"]',
        'html[data-copy-display="photos"] .chapter-decor-line',
        'html[data-photos-only="on"] .chapter-decor-line',
    ):
        assert selector in text, selector
