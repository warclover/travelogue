"""PIS W3 · compiled face stars. Journal mosaic must not import this."""

from __future__ import annotations

import re
import warnings

import pytest
import yaml

from travelogue.layout_engine.editorial_series.page_stars import (
    DISABLED_FACES,
    FACE_STARS,
    is_disabled,
    star_of,
)
from travelogue.layout_engine.editorial_series.place import place_groups
from travelogue.layout_engine.editorial_series.slot_match import (
    _cousin_faces,
    _cousin_rank_key,
    load_slot_specs,
    maybe_star_upgrade,
    take_for_page,
)
from travelogue.paths import ROOT

pytestmark = pytest.mark.unit

_DISABLED = ("page-4-2p2p", "page-6-4l2p")
_SRC_FILES = (
    ROOT / "travelogue" / "layout_engine" / "editorial_series" / "page_stars.py",
    ROOT / "travelogue" / "layout_engine" / "editorial_series" / "slot_match.py",
)
_IMPORT_RESERVE = re.compile(
    r"^(?:from|import)\s+(?:docs\.)?templates\.reserve",
    re.MULTILINE,
)


def _workshop_stars() -> tuple[dict[str, int], frozenset[str]]:
    raw = yaml.safe_load(
        (ROOT / "docs" / "templates" / "reserve" / "stars.yaml").read_text(
            encoding="utf-8"
        )
    )
    disabled = frozenset(str(x) for x in (raw.get("disabled") or []))
    stars = {
        str(k): int(v)
        for k, v in raw.items()
        if k != "disabled" and v is not None
    }
    return stars, disabled


def test_star_of_unlisted_is_zero() -> None:
    assert star_of("page-2-pair-square") == 0
    assert star_of("") == 0
    assert star_of("not-a-face") == 0
    assert star_of("page-5-3p2l-center") == 3
    assert star_of("page-5-3p2l-left") == 2
    assert star_of("page-4-1p3l-left") == 1


def test_disabled_faces_are_the_workshop_pair() -> None:
    assert set(_DISABLED) <= set(DISABLED_FACES)
    assert all(is_disabled(tid) for tid in _DISABLED)
    assert is_disabled("page-4-port") is False


def test_disabled_faces_never_enter_cousins() -> None:
    cousins4 = _cousin_faces("page-4-port", max_n=4, have_n=4)
    cousins6 = _cousin_faces("page-6-grid-land", max_n=6, have_n=6)
    assert "page-4-2p2p" not in cousins4
    assert "page-6-4l2p" not in cousins6
    for tid in _DISABLED:
        taken = take_for_page(
            ["p1", "p2", "p3", "p4", "l1", "l2"],
            tid,
            band=4 if "page-4" in tid else 6,
            aspect_kinds={
                "p1": "portrait",
                "p2": "portrait",
                "p3": "portrait",
                "p4": "portrait",
                "l1": "landscape",
                "l2": "landscape",
            },
            aspect_ratios={
                "p1": 0.75,
                "p2": 0.75,
                "p3": 0.75,
                "p4": 0.75,
                "l1": 16 / 9,
                "l2": 16 / 9,
            },
        )
        assert taken.skip is True


def test_disabled_planned_face_falls_back() -> None:
    ids = ["p1", "p2", "p3", "p4"]
    kinds = {i: "portrait" for i in ids}
    ratios = {i: 0.75 for i in ids}
    placed = place_groups(
        [{"id": "g", "kind": "scene", "asset_ids": ids}],
        [{"role": "grid4", "slotBand": 4, "patternId": "page-4-2p2p"}],
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert placed.pages
    assert placed.pages[0].pattern_id != "page-4-2p2p"
    assert placed.pages[0].pattern_id not in DISABLED_FACES


def test_same_slot_three_star_beats_one_star(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(FACE_STARS, "page-5-3p2l-left", 1)
    planned = load_slot_specs("page-5-3p2l-left")
    center = load_slot_specs("page-5-3p2l-center")
    official: frozenset[str] = frozenset()
    one = _cousin_rank_key(planned, 5, "page-5-3p2l-left", planned, official)
    three = _cousin_rank_key(planned, 5, "page-5-3p2l-center", center, official)
    assert three < one

    ids = ["p1", "p2", "p3", "l1", "l2"]
    kinds = {i: ("portrait" if i.startswith("p") else "landscape") for i in ids}
    ratios = {i: (0.75 if i.startswith("p") else 16 / 9) for i in ids}
    placed = place_groups(
        [{"id": "g", "kind": "scene", "asset_ids": ids}],
        [{"role": "grid5", "slotBand": 5, "patternId": "page-5-3p2l-left"}],
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert placed.pages[0].pattern_id in {
        "page-5-3p2l-center",
        "page-5-3p2l-center-flip",
    }
    assert placed.demoted_pages == 0


def test_wrong_mix_three_star_does_not_beat_true_fit() -> None:
    ids = ["p1", "l1", "l2", "l3"]
    kinds = {i: ("portrait" if i.startswith("p") else "landscape") for i in ids}
    ratios = {i: (0.75 if i.startswith("p") else 4 / 3) for i in ids}
    taken = take_for_page(
        ids,
        "page-4-1p3l-left",
        band=4,
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert taken.skip is False
    face, upgraded = maybe_star_upgrade(
        ids,
        "page-4-1p3l-left",
        taken,
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert face == "page-4-1p3l-left"
    assert upgraded.asset_ids
    assert star_of("page-4-1p3l-wide-left") == 3
    assert star_of("page-4-1p3l-left") == 1


def test_planned_three_star_that_fits_does_not_swap() -> None:
    ids = ["l1", "l2", "l3", "l4"]
    kinds = {i: "landscape" for i in ids}
    ratios = {i: 16 / 9 for i in ids}
    placed = place_groups(
        [{"id": "g", "kind": "scene", "asset_ids": ids}],
        [{"role": "grid4", "slotBand": 4, "patternId": "page-4-grid-land"}],
        aspect_kinds=kinds,
        aspect_ratios=ratios,
    )
    assert placed.pages[0].pattern_id == "page-4-grid-land"
    assert placed.demoted_pages == 0


def test_snapshot_reconcile_warns_not_fails() -> None:
    workshop, disabled = _workshop_stars()
    if workshop != dict(FACE_STARS) or disabled != DISABLED_FACES:
        warnings.warn(
            "page_stars snapshot drifted from docs/templates/reserve/stars.yaml; "
            "sync travelogue/layout_engine/editorial_series/page_stars.py",
            stacklevel=1,
        )


def test_runtime_modules_do_not_import_reserve() -> None:
    for path in _SRC_FILES:
        text = path.read_text(encoding="utf-8")
        assert _IMPORT_RESERVE.search(text) is None, path


def test_journal_mosaic_does_not_import_page_stars() -> None:
    mosaic = ROOT / "travelogue" / "layout_engine" / "mosaic"
    banned = ("editorial_series.page_stars", "page_stars")
    for path in mosaic.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path} imports portfolio page_stars"
