"""Tests for scripts/lint_trip_pipeline_mutations.py (M-C4)."""



from __future__ import annotations

import ast

from scripts.lint_trip_pipeline_mutations import (
    PipelineMutationLintVisitor,
    iter_scan_files,
    lint_file,
)
from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _violations(source: str, *, rel: str = "sample.py") -> list[str]:
    tree = ast.parse(source, filename=rel)
    visitor = PipelineMutationLintVisitor(rel)
    visitor.visit(tree)
    return visitor.violations


def test_allows_pipeline_view_helpers() -> None:
    source = """
from travelogue.domain.pipeline_view import set_pipeline_status, append_pipeline_run

def ok(trip):
    set_pipeline_status(trip, "copy_draft")
    append_pipeline_run(trip, {"runId": "x", "agent": "storyteller"})
"""
    assert _violations(source) == []


def test_flags_direct_status_assignment() -> None:
    source = """
def bad(trip):
    trip.setdefault("pipeline", {})["status"] = "copy_draft"
"""
    assert len(_violations(source)) == 1


def test_flags_pipeline_alias_status_assignment() -> None:
    source = """
def bad(trip):
    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "structure_locked"
"""
    assert len(_violations(source)) == 1


def test_flags_runs_append() -> None:
    source = """
def bad(trip):
    trip.setdefault("pipeline", {}).setdefault("runs", []).append({"runId": "x"})
"""
    assert len(_violations(source)) == 1


def test_pipeline_state_reexport_is_exempt() -> None:
    path = ROOT / "travelogue" / "services" / "pipeline_state.py"
    assert lint_file(path) == []


def test_scanned_tree_has_no_violations() -> None:
    violations: list[str] = []
    for path in iter_scan_files():
        violations.extend(lint_file(path))
    assert violations == []
