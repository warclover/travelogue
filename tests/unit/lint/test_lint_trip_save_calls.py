"""Tests for scripts/lint_trip_save_calls.py."""



from __future__ import annotations

import ast

from scripts.lint_trip_save_calls import TripSaveLintVisitor, lint_file
from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _violations(source: str, *, rel: str = "sample.py") -> list[str]:
    tree = ast.parse(source, filename=rel)
    visitor = TripSaveLintVisitor(rel)
    visitor.visit(tree)
    return visitor.violations


def test_allows_update_calls() -> None:
    source = """
def ok(svc, trip_path):
    svc.update(trip_path, lambda t: t.setdefault("meta", {})["title"])
"""
    assert _violations(source) == []


def test_flags_direct_svc_save() -> None:
    source = """
def bad(svc, trip, trip_path):
    svc.save(trip, trip_path)
"""
    assert len(_violations(source)) == 1


def test_flags_save_with_body_dict() -> None:
    source = """
def bad(svc, body, trip_json):
    svc.save(body, trip_json)
"""
    assert len(_violations(source)) == 1


def test_trip_py_is_exempt() -> None:
    allowed = ROOT / "travelogue" / "services" / "trip.py"
    assert lint_file(allowed) == []


def test_travelogue_tree_has_no_external_trip_save() -> None:
    violations: list[str] = []
    for path in (ROOT / "travelogue").rglob("*.py"):
        violations.extend(lint_file(path))
    assert violations == []
