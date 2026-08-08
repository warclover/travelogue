"""Unit tests · title_art contract (PRD-COVER-CALLIGRAPHY-TITLE-V1 §4 · OQ-CAL-10)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.contract import (
    MAIN_SOURCE,
    MAX_MAIN_CHARS,
    resolve_title_text,
)

pytestmark = pytest.mark.unit


def test_resolve_title_text_short_title_unchanged() -> None:
    trip = {"meta": {"title": "拾光"}}
    result = resolve_title_text(trip)
    assert result.main == "拾光"
    assert result.truncated is False
    assert result.subtitle is None
    assert result.empty is False
    assert result.main_source == MAIN_SOURCE


def test_resolve_title_text_truncates_over_max_chars() -> None:
    long_title = "夏睿彤贵州暑假游记全纪录"
    assert len(long_title) > MAX_MAIN_CHARS
    trip = {"meta": {"title": long_title}}
    result = resolve_title_text(trip)
    assert len(result.main) == MAX_MAIN_CHARS
    assert result.truncated is True


def test_resolve_title_text_empty_title_is_fail_open() -> None:
    trip = {"meta": {"title": "   "}}
    result = resolve_title_text(trip)
    assert result.empty is True
    assert result.main == ""


def test_resolve_title_text_missing_meta_is_fail_open() -> None:
    result = resolve_title_text({})
    assert result.empty is True


def test_resolve_title_text_optional_subtitle() -> None:
    trip = {"meta": {"title": "拾光", "titleArtSubtitle": "贵州 · 暑假"}}
    result = resolve_title_text(trip)
    assert result.subtitle == "贵州 · 暑假"


def test_resolve_title_text_blank_subtitle_is_none() -> None:
    trip = {"meta": {"title": "拾光", "titleArtSubtitle": "   "}}
    result = resolve_title_text(trip)
    assert result.subtitle is None


def test_resolve_title_text_uses_display_title_over_raw_meta_title() -> None:
    """OQ-CAL-10 · 贴纸主串须与封面 <h1> 同源（displayTitle）。"""
    trip = {
        "meta": {
            "title": "夏睿彤年度精选2",
            "displayTitle": "夏睿彤年度精选",
        }
    }
    result = resolve_title_text(trip)
    assert result.main == "夏睿彤年度精选"
    assert result.main_source == "displayTitle"
    assert "2" not in result.main
