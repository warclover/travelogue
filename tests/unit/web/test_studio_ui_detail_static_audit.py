"""Unit smoke for Studio UI detail static audit."""

from __future__ import annotations

from scripts.studio_ui_detail_static_audit import run_audit


def test_static_audit_no_modal_chrome_dual_standard() -> None:
    report = run_audit(wave="modal")
    conflicts = [
        f
        for f in report["findings"]
        if f["id"] == "D-UID-01" and "studio__" in str(f.get("selector", ""))
    ]
    assert conflicts == [], conflicts


def test_static_audit_preview_chrome_no_bare_legacy_hex() -> None:
    report = run_audit(wave="preview-chrome")
    bare = [f for f in report["findings"] if f["id"] == "D-UID-09"]
    assert bare == [], bare
    assert report["summary"]["P1"] == 0


def test_static_audit_wait_tips_no_rainbow_tones() -> None:
    report = run_audit(wave="wait-tips")
    rainbow = [f for f in report["findings"] if f["id"] == "D-UID-10"]
    assert rainbow == [], rainbow


def test_static_audit_cap_narrow_lightbox_no_forest_drift() -> None:
    report = run_audit(wave="cap-narrow-lightbox")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-11"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_bench_wizard_carousel_no_slate_cyan() -> None:
    report = run_audit(wave="bench-wizard-carousel")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-12"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_home_tokens_no_sky_default_or_hardcode() -> None:
    report = run_audit(wave="home-tokens")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-13"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_shelf_dev_loading_no_cyan_shimmer() -> None:
    report = run_audit(wave="shelf-dev-loading")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-14"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_overlay_toast_no_mint_forest() -> None:
    report = run_audit(wave="overlay-toast")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-15"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_wizard_help_closeout_clean() -> None:
    report = run_audit(wave="wizard-help-closeout")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-16"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_all_waves_no_p0_p1() -> None:
    report = run_audit(wave="all")
    assert report["summary"]["P0"] == 0
    assert report["summary"]["P1"] == 0, [
        f for f in report["findings"] if f["severity"] == "P1"
    ]
