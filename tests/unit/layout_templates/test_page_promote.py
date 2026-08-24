"""Promote atelier page-* faces into LTE without touching journal MCS."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.layout_engine.planner.screen_planner import grid_class_for_pattern
from travelogue.layout_templates.page_promote import (
    P0_PAGE_IDS,
    PercentBox,
    boxes_to_grid,
    load_face_boxes,
    promote_pages,
)
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, get_engine
from travelogue.layout_templates.validator import _dense_freeze_exempt, validate_template_def

pytestmark = pytest.mark.unit


def test_p0_eleven_faces_are_in_lte() -> None:
    engine = get_engine()
    for pid in P0_PAGE_IDS:
        tpl = engine.get(pid)
        assert tpl.status == "experimental"
        assert not tpl.rollout
        assert tpl.render_grid_class == f"layout-screen__grid--{pid}"
        report = validate_template_def(tpl, mode="ci")
        errors = [i for i in report.issues if i.level in ("error", "block")]
        assert not errors, (pid, errors)


def test_page_ten_is_in_lte_and_validates() -> None:
    tpl = get_engine().get("page-10-grid-port")
    assert tpl.status == "experimental"
    assert len(tpl.slots) == 10
    report = validate_template_def(tpl, mode="ci")
    errors = [i for i in report.issues if i.level in ("error", "block")]
    assert not errors, errors


def test_page_faces_are_not_mcs_active() -> None:
    engine = get_engine()
    active_ids = {t.id for t in engine.list_active(enforce_quotas=False)}
    assert not any(i.startswith("page-") for i in active_ids)
    from travelogue.layout_templates.legacy_bridge import mosaic_pattern_id_groups

    for ids in mosaic_pattern_id_groups().values():
        assert all(not str(i).startswith("page-") for i in ids)


def test_page_faces_do_not_enter_h8_lifecycle() -> None:
    from travelogue.layout_contract.active_set import (
        contract_extra_ids,
        scan_rollout_zero_lifecycle,
    )

    lifecycle = scan_rollout_zero_lifecycle()
    for bucket in ("missingZeroSince",):
        assert not any(str(i).startswith("page-") for i in lifecycle[bucket])
    for row in lifecycle["overdue"] + lifecycle["withinWindow"]:
        assert not str(row.get("id") or "").startswith("page-")
    active, dogfood = contract_extra_ids()
    assert not any(str(i).startswith("page-") for i in active | dogfood)


def test_grid_class_for_promoted_page() -> None:
    assert (
        grid_class_for_pattern("page-1-hero-land-wide")
        == "layout-screen__grid--page-1-hero-land-wide"
    )


def test_boxes_to_grid_keeps_wide_hero_margins() -> None:
    cols, rows, rects = boxes_to_grid([PercentBox(6.25, 6.25, 87.5, 87.5)])
    assert rects == [(2, 2, 2, 2)]
    assert cols[1] > cols[0]
    assert rows[1] > rows[0]


def test_page_star_exempt_from_ltn_dense_freeze() -> None:
    assert _dense_freeze_exempt("page-8-grid-land") is True
    assert _dense_freeze_exempt("screen-mosaic-7-forbidden-new") is False


def test_promote_writes_ten_slot_page(tmp_path: Path) -> None:
    written, skips = promote_pages(ids=["page-10-grid-port"], templates_dir=tmp_path, write=True)
    assert written == ["page-10-grid-port"]
    assert skips == []
    assert (tmp_path / "page-10-grid-port.yaml").is_file()


def test_faces_js_covers_p0() -> None:
    boxes = load_face_boxes()
    for pid in P0_PAGE_IDS:
        assert pid in boxes
        assert boxes[pid]
