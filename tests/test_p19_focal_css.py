"""P19: journal-screens.css must not hardcode object-position over focal vars."""

from __future__ import annotations

import re
from pathlib import Path

_CSS = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "journal-screens.css"
_FORBIDDEN = re.compile(
    r"object-position:\s*(top\s+center|center)\s*;",
    re.IGNORECASE,
)


def test_journal_screens_no_hardcoded_object_position() -> None:
    text = _CSS.read_text(encoding="utf-8")
    matches = list(_FORBIDDEN.finditer(text))
    assert not matches, f"hardcoded object-position at lines: {[text[:m.start()].count(chr(10)) + 1 for m in matches]}"
