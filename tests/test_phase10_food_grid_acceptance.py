"""Tests for scripts/phase10_food_grid_acceptance.py."""

from __future__ import annotations

import subprocess

from scripts.phase10_food_grid_acceptance import run_acceptance


def test_run_acceptance_returns_passed_with_expected_checks() -> None:
    record = run_acceptance()
    assert record["status"] == "passed"
    checks = record.get("checks") or []
    assert len(checks) >= 5
    ids = {c.get("id") for c in checks}
    assert {
        "ac-p10-auto-01",
        "ac-p10-auto-02",
        "ac-p10-auto-03",
        "ac-p10-auto-04",
        "ac-p10-auto-05",
    }.issubset(ids)
    assert all(bool(c.get("passed")) for c in checks)


def test_disable_flag_check_has_zero_food_grid_count() -> None:
    record = run_acceptance()
    checks = record.get("checks") or []
    target = next(c for c in checks if c.get("id") == "ac-p10-auto-04")
    assert target.get("passed") is True
    assert target.get("foodGridCount") == 0


def test_manual_fixture_spec_contains_food_grid_expectations() -> None:
    record = run_acceptance()
    fixture = record.get("manualFixtureSpec") or {}
    expected = fixture.get("expected") or {}
    assert expected.get("mustContainLayoutHint") == "food-grid"
    patterns = expected.get("mustContainPatterns") or []
    assert "screen-portrait-grid-8" in patterns
    assert "screen-square-4" in patterns


def test_run_acceptance_can_include_phase101_checks() -> None:
    record = run_acceptance(
        include_phase101=True,
        mundane_grid_buckets=("food", "sign", "ticket", "shop"),
    )
    checks = record.get("checks") or []
    ids = {c.get("id") for c in checks}
    assert "ac-p10-1-auto-sign-01" in ids
    assert "ac-p10-1-auto-ticket-01" in ids
    assert "ac-p10-1-auto-shop-01" in ids
    assert all(bool(c.get("passed")) for c in checks)


def test_run_acceptance_can_include_demo_verify_check(monkeypatch) -> None:
    def _fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["python", "-m", "travelogue", "demo", "verify"],
            returncode=0,
            stdout="OK demo verify\n",
            stderr="",
        )

    monkeypatch.setattr(
        "scripts.phase10_food_grid_acceptance.subprocess.run",
        _fake_run,
    )
    record = run_acceptance(include_demo_verify=True)
    checks = record.get("checks") or []
    target = next(c for c in checks if c.get("id") == "ac-p10-auto-06")
    assert target.get("passed") is True
    assert target.get("returnCode") == 0
