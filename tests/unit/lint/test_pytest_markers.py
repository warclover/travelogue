"""Pytest marker tiering (--fast, auto e2e on playwright modules)."""

from __future__ import annotations

import pytest

from tests import conftest as tests_conftest


class _FakeItem:
    def __init__(self, nodeid: str, *, markers: list[str] | None = None) -> None:
        self.nodeid = nodeid
        self._markers = [getattr(pytest.mark, name)() for name in (markers or [])]

    def get_closest_marker(self, name: str):
        for m in reversed(self._markers):
            if m.name == name:
                return m
        return None

    def iter_markers(self):
        return iter(self._markers)

    def add_marker(self, marker) -> None:
        self._markers.append(marker)


def test_apply_auto_markers_adds_e2e_to_playwright_serial() -> None:
    item = _FakeItem("tests/unit/export/test_export_pdf.py::test_pdf", markers=["playwright_serial"])
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is not None


def test_apply_auto_markers_skips_unit_tests() -> None:
    item = _FakeItem("tests/unit/render/test_longshot_smoke.py::test_smoke", markers=["unit"])
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is None


def test_apply_auto_markers_tags_playwright_modules() -> None:
    item = _FakeItem("tests/e2e/test_studio_lcp_playwright.py::test_lcp")
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is not None
    assert item.get_closest_marker("playwright_serial") is not None


def test_fast_skip_marker_set_matches_ci_pr_tier() -> None:
    assert tests_conftest._FAST_SKIP_MARKERS == frozenset(
        {"e2e", "playwright_serial", "integration", "vision", "legacy_homepage"}
    )


def test_apply_auto_markers_tags_integration_path_bucket() -> None:
    item = _FakeItem("tests/integration/p17/test_p17_controlled_parity.py::test_x")
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("integration") is not None


class _FakeConfig:
    def __init__(self, *, fast: bool) -> None:
        self._fast = fast
        self.hook = type("H", (), {"pytest_deselected": staticmethod(lambda items: None)})()

    def getoption(self, name: str):
        if name == "--fast":
            return self._fast
        raise AssertionError(name)


def test_fast_filter_runs_after_auto_markers_deselects_integration() -> None:
    """M2-A2a · path-bucket integration must not leak into --fast subset."""
    item = _FakeItem("tests/integration/p17/test_p17_controlled_parity.py::test_x")
    unit = _FakeItem("tests/unit/lint/test_pytest_markers.py::test_x", markers=["unit"])
    items: list = [item, unit]
    tests_conftest.pytest_collection_modifyitems(_FakeConfig(fast=True), items)  # type: ignore[arg-type]
    assert item not in items
    assert unit in items
    assert item.get_closest_marker("integration") is not None
