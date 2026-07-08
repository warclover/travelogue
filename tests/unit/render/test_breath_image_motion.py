"""Breath image scrub must not stagger mosaic / portrait-row slots."""



from __future__ import annotations
from tests._repo_root import repo_root

from pathlib import Path

import pytest

BREATH_IMAGE = (
    repo_root(__file__)
    / "templates"
    / "visual-journal"
    / "breath-image.js"
)


@pytest.mark.unit
def test_breath_image_unifies_motion_for_mosaic_and_person_rows() -> None:
    text = BREATH_IMAGE.read_text(encoding="utf-8")
    assert "function shouldUnifySlotMotion" in text
    assert "layout-slot__img--contain" in text
    assert "--3x2" in text
    assert "unifyMotion" in text
    assert "if (enterRaw >= 1) return 1;" in text
