"""Unit tests · title_art char_frequency 预筛选（D-CAL-21）。"""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.char_frequency import (
    _build_common_hanzi,
    title_has_only_common_chars,
)

pytestmark = pytest.mark.unit


def test_common_hanzi_table_has_exactly_3755_chars() -> None:
    # GB2312 一级汉字国标数量，用于断言字表构建逻辑没有偏移字节区间。
    assert len(_build_common_hanzi()) == 3755


@pytest.mark.parametrize(
    "title",
    [
        "拾光",
        "稻城亚丁行",
        "阿勒泰散记",
        "重庆火锅魂",
        "厦门老城区",
        "918公里",
        "三亚Vlog",
        "海边·日落",
        "一路向西…",
    ],
)
def test_common_titles_pass(title: str) -> None:
    assert title_has_only_common_chars(title) is True


@pytest.mark.parametrize(
    "title",
    [
        "甪直古镇",  # 甪 不在 GB2312 任一级
        "涠洲岛落日",  # 涠 二级字
        "婺源篁岭",  # 婺/篁 均为二级字
        "黟县宏村",  # 黟 二级字
        "阆中古城",  # 阆 二级字
        "硇洲岛",  # 硇 二级字
        "邺城旧梦",  # 邺 二级字
        "麤犇靐齉爩",  # 极罕见字，甚至不在 GB2312 全字表内
    ],
)
def test_uncommon_titles_are_rejected(title: str) -> None:
    assert title_has_only_common_chars(title) is False


def test_empty_string_passes() -> None:
    assert title_has_only_common_chars("") is True


def test_digits_and_latin_never_block() -> None:
    assert title_has_only_common_chars("2026 Roadtrip!?") is True


def test_lookup_error_disables_prefilter(monkeypatch) -> None:
    """字表构建失败（如极端精简 Python 构建缺 gb2312 codec）时预筛选静默失
    效——不应把"取不到字表"误判成"全部都是生僻字"。"""
    from travelogue.cover_engine.title_art import char_frequency as mod

    mod._common_hanzi.cache_clear()
    monkeypatch.setattr(mod, "_build_common_hanzi", lambda: frozenset())
    assert title_has_only_common_chars("麤犇靐齉爩") is True
    mod._common_hanzi.cache_clear()
