"""Demo verify helpers."""

from __future__ import annotations

from travelogue.demo.verify import FIXTURE_NAMES, _validate_fixtures, run_demo_verify


def test_validate_all_fixtures_including_golden():
    errs = _validate_fixtures()
    assert not errs, errs
    assert "trip.render_golden.json" in FIXTURE_NAMES


def test_run_demo_verify_quick_skip_pytest():
    result = run_demo_verify(skip_pytest=True, skip_dom=False)
    assert result.fixture_errors == []
    assert result.dom_errors == []
    assert any("fixtures:" in m for m in result.messages)
    assert any("dom regression: OK" in m for m in result.messages)


def test_run_demo_verify_skip_dom():
    result = run_demo_verify(skip_pytest=True, skip_dom=True)
    assert "dom regression: skipped" in result.messages
