"""AC-TPC-08 · layout_compare helpers (contract on vs off report shape)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]


def _load_layout_compare():
    path = ROOT / "scripts" / "layout_compare.py"
    spec = importlib.util.spec_from_file_location("layout_compare", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_layout_compare_diff_report_stable() -> None:
    mod = _load_layout_compare()
    base = {
        "screenSignatures": ["c1|a|(x,)", "c1|b|(y,)"],
        "patternSequence": ["a", "b"],
    }
    same = {
        "screenSignatures": ["c1|a|(x,)", "c1|b|(y,)"],
        "patternSequence": ["a", "b"],
    }
    diff0 = mod._diff_report(base, same)
    assert diff0["screensChanged"] == 0
    assert diff0["screensChangedPct"] == 0.0

    cand = {
        "screenSignatures": ["c1|a|(x,)", "c1|z|(y,)"],
        "patternSequence": ["a", "z"],
    }
    diff1 = mod._diff_report(base, cand)
    assert diff1["screensChanged"] == 1
    assert diff1["patternOnlyChanges"] == 1


def test_layout_compare_cfg_variant_toggles_contract() -> None:
    from travelogue.config import get_config

    mod = _load_layout_compare()
    base = get_config()
    off = mod._cfg_variant(base, contract_enabled=False)
    on = mod._cfg_variant(base, contract_enabled=True)
    assert off.mosaic.template_contract.enabled is False
    assert on.mosaic.template_contract.enabled is True
