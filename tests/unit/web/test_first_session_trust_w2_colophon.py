"""First-Session Trust W2 · AC-FST-14 辑封眉题契约。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
VJ = ROOT / "templates" / "visual-journal"


def test_ac_fst_14_colophon_label_is_chinese() -> None:
    closing = (VJ / "partials" / "cover-closing.hbs").read_text(encoding="utf-8")
    epi = (VJ / "partials" / "epilogue-screen.hbs").read_text(encoding="utf-8")
    css = (VJ / "journal-screens.css").read_text(encoding="utf-8")
    overlays = (VJ / "journal-screens-overlays.css").read_text(encoding="utf-8")

    assert "辑封" in closing
    assert "辑封" in epi
    assert 'content: "辑封"' in css or "content: '辑封'" in css
    assert 'content: "辑封"' in overlays or "content: '辑封'" in overlays
    assert ">Colophon<" not in closing
    assert ">Colophon<" not in epi
    assert 'content: "Colophon"' not in css
    assert 'content: "Colophon"' not in overlays
