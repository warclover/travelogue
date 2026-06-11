"""P19: journal-screens.css must not hardcode object-position over focal vars."""

from __future__ import annotations

import re
from pathlib import Path

_CSS_DIR = Path(__file__).resolve().parents[1] / "templates" / "visual-journal"
_CSS_FILES = (_CSS_DIR / "journal-screens.css", _CSS_DIR / "journal.css")
_FORBIDDEN = re.compile(
    r"object-position:\s*(top\s+center|center)\s*;",
    re.IGNORECASE,
)


def test_journal_screens_no_hardcoded_object_position() -> None:
    for css_path in _CSS_FILES:
        text = css_path.read_text(encoding="utf-8")
        matches = list(_FORBIDDEN.finditer(text))
        assert not matches, (
            f"{css_path.name}: hardcoded object-position at lines: "
            f"{[text[:m.start()].count(chr(10)) + 1 for m in matches]}"
        )
