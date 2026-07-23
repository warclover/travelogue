"""QFX D-QFX-10 · 空/缺字段测量 fail-closed → P0。"""

from __future__ import annotations

from tests.e2e.ui_detail_runtime_helpers import findings_from_panel_metrics


def test_missing_metrics_fields_are_p0() -> None:
    findings = findings_from_panel_metrics({"fontSizeCount": 1}, surface="panel")
    assert findings and findings[0]["id"] == "D-UID-HARNESS"
    assert findings[0]["severity"] == "P0"


def test_empty_measurement_is_p0() -> None:
    findings = findings_from_panel_metrics(
        {
            "fontSizeCount": 0,
            "uniqueFontSizes": [],
            "uniqueColors": [],
        },
        surface="panel",
    )
    assert findings and findings[0]["id"] == "D-UID-HARNESS"


def test_nan_font_count_is_p0() -> None:
    findings = findings_from_panel_metrics(
        {
            "fontSizeCount": float("nan"),
            "uniqueFontSizes": [],
            "uniqueColors": ["rgb(1,2,3)"],
        },
        surface="panel",
    )
    assert findings and findings[0]["id"] == "D-UID-HARNESS"
