"""LTN D3 · layout role table + rhythmSignOff gate."""

from __future__ import annotations

from pathlib import Path

from travelogue.layout_contract.layout_roles import (
    LAYOUT_ROLE_TABLE,
    product_role_for,
    resolve_layout_roles,
)
from travelogue.layout_contract.rhythm_signoff import (
    RHYTHM_SIGNOFF,
    verify_rhythm_signoff,
)
from travelogue.render.context import build_layout_screen

ROOT = Path(__file__).resolve().parents[3]


def test_product_role_aliases_cover_prd_vocabulary():
    aliases = {row["productRole"] for row in LAYOUT_ROLE_TABLE}
    assert aliases >= {"plate", "1col", "stack-3", "2col", "mosaic-hero", "breath"}
    assert product_role_for("hero_single") == "1col"
    assert product_role_for("stack") == "stack-3"
    assert product_role_for("mosaic_hero") == "mosaic-hero"


def test_resolve_layout_roles_from_pattern():
    narr, prod = resolve_layout_roles(
        {
            "patternId": "screen-mosaic-5-main-portrait-3land",
            "slots": [{"assetId": "a1", "role": "main"}, {"assetId": "a2"}],
        }
    )
    assert narr == "mosaic_hero"
    assert prod == "mosaic-hero"


def test_build_layout_screen_emits_role_attrs():
    screen = {
        "patternId": "screen-portrait-3",
        "slots": [{"assetId": "a1"}, {"assetId": "a2"}, {"assetId": "a3"}],
    }
    assets = {
        "a1": {"id": "a1", "width": 800, "height": 1200},
        "a2": {"id": "a2", "width": 800, "height": 1200},
        "a3": {"id": "a3", "width": 800, "height": 1200},
    }
    ctx = build_layout_screen(screen, assets, meta_title="T", export_layout="web")
    assert ctx.get("narrativeRole") == "stack"
    assert ctx.get("layoutRole") == "stack-3"
    assert ctx.get("hasLayoutRole") is True


def test_rhythm_signoff_matches_preamble_and_overlays():
    for rel in (
        "templates/visual-journal/journal-screens-overlays.css",
        "templates/visual-journal/journal-screens.css",
    ):
        css = (ROOT / rel).read_text(encoding="utf-8")
        assert verify_rhythm_signoff(css) == [], rel
    assert RHYTHM_SIGNOFF["id"] == "ltn-d1-rhythm-v1"


def test_rhythm_signoff_detects_drift():
    css = "--rhythm-l0-gap: 9px;\n--rhythm-l1-gap: clamp(10px, 1.6vh, 20px);\n--rhythm-l2-gap: clamp(36px, 6vh, 64px);\n"
    errs = verify_rhythm_signoff(css)
    assert any("rhythm-l0-gap" in e for e in errs)
