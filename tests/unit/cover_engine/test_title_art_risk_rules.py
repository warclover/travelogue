"""Unit tests · title_art Route C risk rules (W0.5b / digit_mix)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.risk_rules import (
    route_c_risk_reason,
    title_has_repeated_hanzi,
    title_has_risky_digit_mix,
    title_has_risky_punctuation,
)

pytestmark = pytest.mark.unit


def test_punctuation_detected() -> None:
    assert title_has_risky_punctuation("一路向西…") is True
    assert title_has_risky_punctuation("海边·日落") is True
    assert title_has_risky_punctuation("拾光") is False


def test_repeated_hanzi_detected() -> None:
    assert title_has_repeated_hanzi("一茶一饭间") is True
    assert title_has_repeated_hanzi("秋去秋又来") is True
    assert title_has_repeated_hanzi("稻城亚丁行") is False


def test_digit_mix_skips_embedded_digits_keeps_leading_digits() -> None:
    assert title_has_risky_digit_mix("重走318国道") is True
    assert title_has_risky_digit_mix("川藏318") is True
    assert title_has_risky_digit_mix("918公里") is False
    assert title_has_risky_digit_mix("G318川藏线") is False  # 数字在汉字前，同「918公里」
    assert title_has_risky_digit_mix("拾光") is False
    assert title_has_risky_digit_mix("2026") is False


def test_risk_reason_priority() -> None:
    assert route_c_risk_reason("一·一") == "punctuation"
    assert route_c_risk_reason("一茶一饭间") == "repeated_char"
    assert route_c_risk_reason("重走318国道") == "digit_mix"
    assert route_c_risk_reason("918公里") is None
    assert route_c_risk_reason("拾光") is None
