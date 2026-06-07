"""W3: layout template Studio admin helpers (R-P16-12)."""

from __future__ import annotations

import pytest

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.layout_templates.layout_admin import (
    is_layout_template_id,
    layout_template_admin_row,
    layout_template_geometry_detail,
    list_layout_templates_for_admin,
    run_admission_for_template,
)
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh_lte_engine() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_is_layout_template_id() -> None:
    assert is_layout_template_id(PATTERN_MOSAIC_5_2P3L_EQUAL)
    assert not is_layout_template_id("not-a-real-template")


@pytest.mark.unit
def test_list_layout_templates_for_admin() -> None:
    rows = list_layout_templates_for_admin()
    ids = {r["templateId"] for r in rows}
    assert PATTERN_MOSAIC_5_2P3L_EQUAL in ids
    flagship = next(r for r in rows if r["templateId"] == PATTERN_MOSAIC_5_2P3L_EQUAL)
    assert flagship["registryKind"] == "layout_pattern"
    assert flagship["category"] == "layout"
    assert "slotAspects" in flagship


@pytest.mark.unit
def test_layout_template_geometry_detail() -> None:
    detail = layout_template_geometry_detail(PATTERN_MOSAIC_5_2P3L_EQUAL)
    assert detail["registryKind"] == "layout_pattern"
    assert detail["render"]["gridTemplateColumns"]
    assert detail["admissionBeta"]["ok"] is True


@pytest.mark.unit
def test_run_admission_for_layout_template() -> None:
    report = run_admission_for_template(PATTERN_MOSAIC_5_2P3L_EQUAL, target="beta")
    assert report["ok"] is True


@pytest.mark.unit
def test_layout_template_admin_row_fields() -> None:
    row = layout_template_admin_row(PATTERN_MOSAIC_5_2P3L_EQUAL)
    assert row["gridClass"].startswith("layout-screen__grid--")
    assert row["photoCount"]["min"] <= row["photoCount"]["max"]
