"""RCL W0 · orchestrator ratchet + comment-budget allowlist."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_rcl_orchestrators import (
    BASELINE,
    COMMENT_ALLOWLIST,
    ORCHESTRATORS,
    ROOT,
    check_comment_budget,
    compare_to_baseline,
    load_baseline,
    main,
    measure_orchestrators,
)

pytestmark = [pytest.mark.unit]


def test_baseline_covers_three_functions_with_owner() -> None:
    current = measure_orchestrators()
    baseline = load_baseline()
    functions = baseline["functions"]
    assert set(functions) == {key for key, *_ in ORCHESTRATORS}
    for key, meta in current.items():
        rec = functions[key]
        assert rec["owner"]
        assert rec["file"] == meta["file"]
        assert rec["lines"] == meta["lines"]
        assert rec["cap_after_w1"] < rec["lines"]


def test_w0_allows_current_size_over_w1_cap() -> None:
    current = measure_orchestrators()
    baseline = load_baseline()
    assert compare_to_baseline(current, baseline, enforce_w1_caps=False) == []
    over = compare_to_baseline(current, baseline, enforce_w1_caps=True)
    assert any("W1 cap" in row for row in over)


def test_growth_above_baseline_is_red() -> None:
    current = measure_orchestrators()
    key = "travelogue.render.assemble:build_render_context"
    inflated = {**current, key: {**current[key], "lines": current[key]["lines"] + 20}}
    baseline = load_baseline()
    hits = compare_to_baseline(inflated, baseline)
    assert any(key in row and "baseline" in row for row in hits)


def test_comment_budget_skips_missing_stage_modules(tmp_path: Path) -> None:
    assert all(not (ROOT / rel).is_file() for rel in COMMENT_ALLOWLIST)
    assert check_comment_budget(root=tmp_path) == []


def test_comment_budget_flags_long_docstring(tmp_path: Path) -> None:
    rel = COMMENT_ALLOWLIST[0]
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('"""' + "\n".join(f"line {i}" for i in range(16)) + '"""\n', encoding="utf-8")
    hits = check_comment_budget(root=tmp_path)
    assert hits and rel in hits[0]


def test_comment_budget_ignores_old_assemble_banner() -> None:
    assert "travelogue/render/assemble.py" not in COMMENT_ALLOWLIST
    assert check_comment_budget() == []


def test_main_green_on_repo() -> None:
    assert BASELINE.is_file()
    assert main([]) == 0
