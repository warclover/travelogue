"""Tests for scripts/lint_test_layout.py (M-C2)."""

from __future__ import annotations

from pathlib import Path

from scripts.lint_test_layout import load_baseline, top_level_test_files

ROOT = Path(__file__).resolve().parents[3]


def test_baseline_matches_current_top_level_files() -> None:
    current = top_level_test_files()
    allowed = load_baseline()
    assert current == allowed


def test_lint_script_main_ok() -> None:
    import scripts.lint_test_layout as mod

    assert mod.main() == 0
