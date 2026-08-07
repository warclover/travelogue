"""Cover opening render helpers."""

from __future__ import annotations

from travelogue.render.cover_opening import (
    build_cover_archive_strip,
    cover_place_is_distinct,
    is_system_cover_hook,
    show_hook_on_cover,
)


def test_cover_place_hidden_when_same_as_title() -> None:
    assert cover_place_is_distinct("斯里兰卡人文精选", "斯里兰卡人文精选") is False
    assert cover_place_is_distinct("黔西南三日漫游", "黔西南三日漫游·精选") is False
    assert cover_place_is_distinct("京都", "雨后京都") is True  # 短地名眉题保留


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


def test_build_cover_archive_strip_empty_when_nothing_available() -> None:
    assert build_cover_archive_strip(meta_subline="", cover_place="", cover_asset={}) == ""


def test_build_cover_archive_strip_joins_subline_place_and_time() -> None:
    strip = build_cover_archive_strip(
        meta_subline="2026.05.27 – 06.23 · 4 天",
        cover_place="贵阳",
        cover_asset={"takenAt": "2026-05-27T09:30:00Z"},
    )
    assert strip == "2026.05.27 – 06.23 · 4 天\n贵阳\n09:30"


def test_build_cover_archive_strip_dedupes_place_already_in_subline() -> None:
    strip = build_cover_archive_strip(
        meta_subline="贵阳 · 4 天", cover_place="贵阳", cover_asset={}
    )
    assert strip == "贵阳 · 4 天"  # cover_place 已包含在 subline 里，不重复追加
