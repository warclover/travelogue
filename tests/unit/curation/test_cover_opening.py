"""Cover opening render helpers."""

from __future__ import annotations

from travelogue.render.cover_opening import (
    cover_place_is_distinct,
    is_system_cover_hook,
    show_hook_on_cover,
)


def test_cover_place_hidden_when_same_as_title() -> None:
    assert cover_place_is_distinct("斯里兰卡人文精选", "斯里兰卡人文精选") is False
    assert cover_place_is_distinct("京都", "雨后京都") is True


def test_system_hook_detection() -> None:
    assert is_system_cover_hook("在斯里兰卡的1天，35 张碎片拼成这一页。")
    assert is_system_cover_hook("35 张碎片拼成这一页。")
    assert is_system_cover_hook("在斯里兰卡的1天，35 张照片汇成这一页。")
    assert is_system_cover_hook("35 张照片汇成这一页。")
    assert is_system_cover_hook("京都，12 张照片留在这里。")
    assert not is_system_cover_hook("鸭川边那阵吹干雨衣的风。")


def test_show_hook_on_cover() -> None:
    assert show_hook_on_cover("在斯里兰卡的1天，35 张碎片拼成这一页。") is False
    assert show_hook_on_cover("在斯里兰卡的1天，35 张照片汇成这一页。") is False
    assert show_hook_on_cover("鸭川边那阵吹干雨衣的风。") is True
