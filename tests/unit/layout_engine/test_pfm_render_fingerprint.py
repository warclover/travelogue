"""ISO-01 · journal render fingerprint ignores edition / pipeline flag."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.render_fingerprint import trip_render_fingerprint_payload

pytestmark = pytest.mark.unit


def _journal_trip() -> dict:
    return {
        "layoutEngine": "screens",
        "exportLayout": "web",
        "assets": [{"id": "a1"}],
        "chapters": [
            {
                "id": "ch-01",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "screens": [{"patternId": "screen-hero", "slots": [{"assetId": "a1"}]}],
            }
        ],
        "meta": {"title": "奈良"},
        "curation": {"displayedAssetIds": ["a1"]},
        "intent": {"title": "奈良"},
    }


def test_iso01_journal_fingerprint_excludes_studio_edition() -> None:
    base = _journal_trip()
    stamped = {
        **base,
        "studio": {"edition": "journal", "portfolio": {"seriesId": "x"}},
    }
    flag_noise = {**base, "studio": {"layoutVibe": "magazine_default"}}
    fp = trip_render_fingerprint_payload(base)
    assert "studio" not in fp
    assert trip_render_fingerprint_payload(stamped) == fp
    assert trip_render_fingerprint_payload(flag_noise) == fp
    assert fp["layoutEngine"] == "screens"


def test_iso01_flag_on_journal_fingerprint_field_equal() -> None:
    """AC-PFM-03 · 开旗 + 只做游记 ≡ 关旗，字段级对照。"""
    from dataclasses import replace

    from travelogue.config import AppConfig, PortfolioPipelineConfig
    from travelogue.config.runtime import config_override

    base = _journal_trip()
    fp_off = trip_render_fingerprint_payload(base)
    cfg = replace(
        AppConfig(),
        studio=replace(
            AppConfig().studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=True),
        ),
    )
    with config_override(cfg):
        flagged = {
            **base,
            "studio": {"edition": "journal", "portfolio": {"seriesId": "noise"}},
        }
        fp_on = trip_render_fingerprint_payload(flagged)
    assert fp_on == fp_off
    assert set(fp_on) == set(fp_off)
    assert "studio" not in fp_on
    assert "edition" not in fp_on
