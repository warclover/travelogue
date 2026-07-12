"""DS-03 · Wizard import payload 字段契约 snapshot（Sheet 退役后冻结键集）。"""

from __future__ import annotations

from pathlib import Path

from tests.unit.web.fixtures.import_wizard_payload_contract import (
    ALLOWED_KEYS,
    FINE_CRAFT_REQUIRED_KEYS,
    OPTIONAL_KEYS,
    QUICK_SHARE_REQUIRED_KEYS,
)

_ROOT = Path(__file__).resolve().parents[3]
_WIZARD_JS = _ROOT / "templates" / "studio" / "homepage-v2" / "import-wizard.js"
_RUN_JS = _ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js"


def test_ds_03_quick_share_required_keys_frozen() -> None:
    assert "albumPath" in QUICK_SHARE_REQUIRED_KEYS
    assert "photoCullEnabled" in QUICK_SHARE_REQUIRED_KEYS
    assert "layoutDensity" not in QUICK_SHARE_REQUIRED_KEYS
    assert QUICK_SHARE_REQUIRED_KEYS <= ALLOWED_KEYS


def test_ds_03_fine_craft_requires_layout_density() -> None:
    assert FINE_CRAFT_REQUIRED_KEYS - QUICK_SHARE_REQUIRED_KEYS == frozenset({"layoutDensity"})
    assert FINE_CRAFT_REQUIRED_KEYS <= ALLOWED_KEYS


def test_ds_03_optional_keys_disjoint_from_required() -> None:
    assert not (OPTIONAL_KEYS & QUICK_SHARE_REQUIRED_KEYS)
    assert OPTIONAL_KEYS <= ALLOWED_KEYS


def test_ds_03_source_still_assigns_contract_keys() -> None:
    """防回归：JS 仍写入契约字段名（非运行时；e2e 负责真实 POST body）。"""
    wizard = _WIZARD_JS.read_text(encoding="utf-8")
    run = _RUN_JS.read_text(encoding="utf-8")
    assert "function buildWizardPayload" in wizard
    assert "function buildImportPayload" in run
    for key in (
        "photoCullEnabled",
        "keepNearDuplicates",
        "layoutDensity",
        "eligibleCount",
        "dateRange",
        "userNotes",
        "travelNotes",
        "featuredDir",
        "materialDir",
        "planText",
    ):
        assert key in wizard, f"missing key assignment surface: {key}"
