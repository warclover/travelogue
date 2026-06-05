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
    item = _FakeItem("tests/test_export_pdf.py::test_pdf", markers=["playwright_serial"])
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is not None


def test_apply_auto_markers_skips_unit_tests() -> None:
    item = _FakeItem("tests/test_longshot_smoke.py::test_smoke", markers=["unit"])
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is None


def test_apply_auto_markers_tags_playwright_modules() -> None:
    item = _FakeItem("tests/test_studio_lcp_playwright.py::test_lcp")
    tests_conftest._apply_auto_markers(item)  # type: ignore[arg-type]
    assert item.get_closest_marker("e2e") is not None
    assert item.get_closest_marker("playwright_serial") is not None


def test_fast_skip_marker_set_matches_ci_pr_tier() -> None:
    assert tests_conftest._FAST_SKIP_MARKERS == frozenset(
        {"e2e", "playwright_serial", "integration", "vision", "legacy_homepage"}
    )
