"""PFM W2 · Output Recipe bypass + portfolio_pages registry (not MCS / PHASE_A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.export.output_recipe import resolve_output_recipe
from travelogue.export.platform_profiles import (
    KNOWN_PLATFORM_IDS,
    PHASE_A_PLATFORMS,
    PORTFOLIO_PLATFORM_IDS,
    file_prefix_for_platform,
    get_profile,
    resolve_profile,
)

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def test_portfolio_ambiguous_does_not_need_intent() -> None:
    trip = {"studio": {"edition": "portfolio"}}
    r = resolve_output_recipe(kept_n=18, trip=trip, entrypoint="preview", enabled=True)
    assert r.needs_intent is False
    assert r.source == "portfolio_bypass"
    assert r.platform == ""
    assert r.intent == ""
    assert r.cta_label == "导出作品集"


def test_journal_ambiguous_still_needs_intent() -> None:
    r = resolve_output_recipe(kept_n=18, entrypoint="preview", enabled=True)
    assert r.needs_intent is True


def test_portfolio_explicit_xhs_still_resolves() -> None:
    trip = {"studio": {"edition": "portfolio"}}
    r = resolve_output_recipe(
        kept_n=18,
        trip=trip,
        entrypoint="preview",
        enabled=True,
        platform="xiaohongshu",
    )
    assert r.needs_intent is False
    assert r.platform == "xiaohongshu"
    assert r.source != "portfolio_bypass"


def test_portfolio_ignores_stale_trip_output_intent() -> None:
    trip = {
        "studio": {"edition": "portfolio"},
        "output": {"intent": "moments_scroll", "platform": "wechat_moments"},
    }
    r = resolve_output_recipe(kept_n=22, trip=trip, entrypoint="preview", enabled=True)
    assert r.source == "portfolio_bypass"
    assert r.needs_intent is False


def test_portfolio_pages_known_not_phase_a() -> None:
    assert "portfolio_pages" in KNOWN_PLATFORM_IDS
    assert "portfolio_pages" in PORTFOLIO_PLATFORM_IDS
    assert "portfolio_pages" not in PHASE_A_PLATFORMS
    profile = get_profile("portfolio_pages")
    assert profile.output.get("aspect") == "16:9"
    assert profile.max_pages == 48
    assert file_prefix_for_platform("奈良", "portfolio_pages").endswith("-portfolio")
    # Studio gray-list does not hide CLI/API access (same as Phase C).
    ok = resolve_profile("portfolio_pages", allowed_platforms=["wechat_moments"])
    assert ok.id == "portfolio_pages"


def test_dispatch_folio_pages_and_print_stay_separate(tmp_path) -> None:
    """S-07 · portfolio_pages → bundle；album_spread → collage；旧 id 不进 collage。"""
    from unittest.mock import patch

    from travelogue.export.dispatch import dispatch_export
    from travelogue.export.longshot import LongshotExportResult
    from travelogue.export.platform_profiles import PlatformProfileError, resolve_profile

    trip = tmp_path / "t"
    trip.mkdir()
    folio = LongshotExportResult(
        outputs=[], platform="portfolio_pages", capture_method="playwright"
    )
    print_pack = LongshotExportResult(
        outputs=[], platform="album_spread", capture_method="collage_pages"
    )
    with (
        patch(
            "travelogue.export.portfolio_pages.export_portfolio_bundle",
            return_value=folio,
        ) as bundle,
        patch(
            "travelogue.export.collage_pack.export_collage_pack",
            return_value=print_pack,
        ) as collage,
    ):
        out = dispatch_export(trip, platform="portfolio_pages")
        assert out.platform == "portfolio_pages"
        bundle.assert_called_once()
        collage.assert_not_called()
        bundle.reset_mock()
        out = dispatch_export(trip, platform="album_spread")
        assert out.platform == "album_spread"
        collage.assert_called_once()
        bundle.assert_not_called()
    with pytest.raises(PlatformProfileError):
        resolve_profile("album_landscape")


def test_folio_page_capture_does_not_use_journal_networkidle() -> None:
    """作品集页图 Writer 不得套用游记 longshot 的 networkidle（会卡死预览）。"""
    folio = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "export"
        / "portfolio_pages.py"
    ).read_text(encoding="utf-8")
    journal = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "export"
        / "longshot.py"
    ).read_text(encoding="utf-8")
    assert 'wait_until="networkidle"' not in folio
    assert 'wait_until="load"' in folio
    assert 'wait_until="networkidle"' in journal
