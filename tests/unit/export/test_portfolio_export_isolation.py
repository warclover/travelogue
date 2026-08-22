"""PFM W2 · Output Recipe bypass + portfolio_pages registry (not MCS / PHASE_A)."""

from __future__ import annotations

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
    assert profile.max_pages == 32
    assert file_prefix_for_platform("奈良", "portfolio_pages").endswith("-portfolio")
    # Studio gray-list does not hide CLI/API access (same as Phase C).
    ok = resolve_profile("portfolio_pages", allowed_platforms=["wechat_moments"])
    assert ok.id == "portfolio_pages"
