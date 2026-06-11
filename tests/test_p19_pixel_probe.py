"""P19 pixel-layer probe (focal CSS + LTE slot aspect)."""

from __future__ import annotations

from travelogue.eval.pixel_probe import (
    audit_3p2l_mosaic_geometry,
    audit_2p3l_equal_geometry,
    run_p19_pixel_probe,
    scan_journal_screens_focal_css,
)


def test_p19_pixel_probe_passes_repo_defaults() -> None:
    report = run_p19_pixel_probe()
    assert report["ok"], report.get("warnings")


def test_scan_journal_screens_focal_css_ok() -> None:
    focal = scan_journal_screens_focal_css()
    assert focal["ok"]
    assert focal["violations"] == 0


def test_p19_mosaic_geometry_probes_pass() -> None:
    assert audit_3p2l_mosaic_geometry()["ok"]
    assert audit_2p3l_equal_geometry()["ok"]
