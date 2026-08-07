"""Album spread count · print-friendly multiples of 4 (auto) + manual clamp."""

from __future__ import annotations

import pytest

from travelogue.export.collage_pack import _album_target_per_card
from travelogue.export.platform_profiles import get_profile, resolve_album_slide_count

pytestmark = pytest.mark.unit


def test_resolve_album_auto_small_keeps_1_or_2() -> None:
    n, hint = resolve_album_slide_count(photo_count=8)
    assert n == 1
    assert "小本" in hint

    n2, _ = resolve_album_slide_count(photo_count=12)
    assert n2 == 2


def test_resolve_album_auto_ceils_to_multiple_of_4() -> None:
    n, hint = resolve_album_slide_count(photo_count=20)
    assert n == 4  # ceil(20/8)=3 → ceil→4
    assert "4 的倍数" in hint

    assert resolve_album_slide_count(photo_count=32)[0] == 4
    assert resolve_album_slide_count(photo_count=40)[0] == 8  # 5 → 8
    assert resolve_album_slide_count(photo_count=64)[0] == 8
    assert resolve_album_slide_count(photo_count=72)[0] == 12  # 9 → 12


def test_resolve_album_auto_caps_at_max_quantum() -> None:
    """max_pages=30 → largest 4k is 28."""
    n, _ = resolve_album_slide_count(photo_count=400)
    assert n == 28
    assert n % 4 == 0


def test_resolve_album_manual_not_forced_to_multiple_of_4() -> None:
    n, _ = resolve_album_slide_count(photo_count=40, slide_count=5)
    assert n == 5
    n2, _ = resolve_album_slide_count(photo_count=40, slide_count=3)
    assert n2 == 3


def test_album_target_per_card_auto_small_stays_greedy() -> None:
    profile = get_profile("album_spread")
    assert (
        _album_target_per_card(12, slide_count=None, profile=profile) is None
    )


def test_album_target_per_card_auto_medium_soft_steers() -> None:
    profile = get_profile("album_spread")
    # 20 photos → target 4 spreads → 8 cards → ceil(20/8)=3
    assert _album_target_per_card(20, slide_count=None, profile=profile) == 3


def test_album_target_per_card_manual_soft_steers() -> None:
    profile = get_profile("album_spread")
    # 4 spreads → 8 cards → ceil(40/8)=5
    assert _album_target_per_card(40, slide_count=4, profile=profile) == 5
