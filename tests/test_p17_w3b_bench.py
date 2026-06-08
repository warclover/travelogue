"""W3b-11 phase17 curate bench helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_bench():
    path = ROOT / "scripts" / "phase17_curate_bench.py"
    spec = importlib.util.spec_from_file_location("phase17_curate_bench_testmod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase17_curate_bench_testmod"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_delta_pct_and_budget() -> None:
    mod = _load_bench()
    assert mod.delta_pct(100.0, 110.0) == 10.0
    assert mod.within_budget(100.0, 114.9) is True
    assert mod.within_budget(100.0, 116.0) is False


def test_curate_bench_golden_within_budget(tmp_path: Path) -> None:
    mod = _load_bench()
    result = mod.run_fixture_bench(
        "golden-mixed-scenes",
        work_dir=tmp_path / "bench",
        repeats=1,
    )
    assert result["baselineMs"] > 0
    assert result["candidateMs"] > 0
    assert result["deltaPct"] is not None
    assert result["withinBudget"] is True
