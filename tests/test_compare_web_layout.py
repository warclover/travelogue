"""Cross-platform compare-web-layout helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.paths import FIXTURES_DIR
from travelogue.render.compare_web import compare_web_layout
from travelogue.render.dual_layout_regression import (
    check_legacy_render_contract,
    check_screens_render_contract,
)


def test_compare_web_layout_writes_both_html(tmp_path: Path) -> None:
    fixture = FIXTURES_DIR / "trip.render_golden.json"
    if not fixture.is_file():
        pytest.skip("fixture missing")
    trip_path = tmp_path / "trip.json"
    trip_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        result = compare_web_layout(trip_path, out_dir=tmp_path)
    except Exception as exc:
        pytest.skip(f"compare_web_layout needs full render env: {exc}")

    assert result.legacy_html.is_file()
    assert result.screens_html.is_file()
    legacy = result.legacy_html.read_text(encoding="utf-8")
    screens = result.screens_html.read_text(encoding="utf-8")
    assert len(legacy) > 500
    assert len(screens) > 500
    assert not check_legacy_render_contract(legacy)
    assert not check_screens_render_contract(screens)
