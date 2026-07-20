"""LTN E1 · active set inventory + LEGACY derivation + rollout lifecycle."""

from __future__ import annotations

from datetime import date

from travelogue.layout_contract.active_set import (
    SIX_WRITE_SOURCES,
    inventory_report,
    legacy_registry_ids,
    scan_rollout_zero_lifecycle,
)
from travelogue.layout_engine.mosaic.pattern_catalog import LEGACY_MOSAIC_REGISTRY_IDS


def test_six_write_sources_documented():
    ids = {row["id"] for row in SIX_WRITE_SOURCES}
    assert ids == {
        "yaml_status",
        "yaml_rollout",
        "lte_policy",
        "codegen",
        "schema_enum",
        "config_override",
    }


def test_legacy_equals_codegen_unified():
    assert set(LEGACY_MOSAIC_REGISTRY_IDS) == set(legacy_registry_ids())
    report = inventory_report(today=date(2026, 7, 20))
    assert report["legacyVsPolicy"]["only_in_legacy"] == []
    assert report["legacyVsPolicy"]["only_in_policy"] == []


def test_inventory_gate_ok():
    report = inventory_report(today=date(2026, 7, 20))
    assert report["ok"] is True
    assert report["activeUnionCount"] <= 12
    assert report["rolloutZeroLifecycle"]["ok"] is True


def test_rollout_zero_overdue_fails():
    life = scan_rollout_zero_lifecycle(today=date(2026, 9, 1))
    # zeroSince 2026-07-20 + 28d → due 2026-08-17; Sep 1 is overdue
    assert life["ok"] is False
    assert any(r["id"].startswith("screen-mosaic-") for r in life["overdue"])
