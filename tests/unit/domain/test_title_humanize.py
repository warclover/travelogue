"""Share-Ready W2 · BE-SR-05 title humanize + First-Session Trust BE-FST-06."""

from travelogue.domain.title_humanize import (
    extract_place_label,
    humanize_folder_title,
    is_folder_title_noise,
    resolve_display_title,
)


def test_humanize_strips_hash_and_handtest_suffix() -> None:
    assert humanize_folder_title("linzhi_a1b2c3d4e5f6") == "linzhi"
    assert humanize_folder_title("ux-handtest-photos-v2") == "我的旅途"
    assert humanize_folder_title("京都雨后") == "京都雨后"


def test_humanize_empty_and_noise() -> None:
    assert humanize_folder_title("") == "我的旅途"
    assert humanize_folder_title(None) == "我的旅途"
    assert humanize_folder_title("新建文件夹") == "我的旅途"
    assert humanize_folder_title("my_trip_photos") == "my trip photos"


def test_humanize_preserves_dots_in_folder_names() -> None:
    """文件夹名可含点；不得按任意扩展名剥掉后缀。"""
    assert humanize_folder_title("2024.10 京都") == "2024 10 京都"
    assert humanize_folder_title("Day1.出发") == "Day1 出发"
    assert humanize_folder_title("2024.精选") == "2024 精选"


def test_humanize_strips_known_media_suffix_only() -> None:
    assert humanize_folder_title("京都雨后.zip") == "京都雨后"
    assert humanize_folder_title("photos.jpg") == "photos"
    assert humanize_folder_title("album.HEIC") == "album"


def test_humanize_respects_limit() -> None:
    long_name = "一二三四五六七八九十一二三四五六七八九十"
    assert humanize_folder_title(long_name, limit=20) == long_name[:20]
    assert humanize_folder_title("短标题", limit=20) == "短标题"


def test_folder_title_noise_chinese_heuristics() -> None:
    assert is_folder_title_noise("王丹昙华林2") is True
    assert is_folder_title_noise("京都雨后") is False
    assert is_folder_title_noise("导出相册01") is True


def test_resolve_display_title_fallback_for_noise() -> None:
    meta = {
        "title": "王丹昙华林2",
        "places": ["武汉"],
        "dateStart": "2026-07-01",
        "dateEnd": "2026-07-02",
    }
    shown = resolve_display_title(meta)
    assert "王丹昙华林2" not in shown
    assert "武汉" in shown
    assert "·" in shown


def test_resolve_display_title_keeps_readable() -> None:
    assert resolve_display_title({"title": "雨后京都", "places": ["京都"]}) == "雨后京都"


def test_humanize_collapses_double_dash() -> None:
    assert humanize_folder_title("武大--米娜") == "武大 米娜"
    assert is_folder_title_noise("武大--米娜") is True


def test_extract_place_from_year_serial_folder() -> None:
    assert extract_place_label("2025东澳岛9") == "东澳岛"
    shown = resolve_display_title(
        {
            "title": "2025东澳岛9",
            "places": ["旅途"],
            "dateStart": "2025-04-20",
            "dateEnd": "2025-04-23",
        }
    )
    assert shown == "东澳岛 · 旅行"
    assert "9" not in shown


def test_resolve_display_title_revalidates_stored_dirty() -> None:
    """D-SFC-03 · 历史脏 displayTitle 不得穿透。"""
    shown = resolve_display_title(
        {
            "title": "武大--米娜",
            "displayTitle": "武大--米娜",
            "places": ["武汉"],
            "dateStart": "2015-07-08",
        }
    )
    assert shown == "武大 米娜"
    assert "--" not in shown


def test_date_fallback_cross_year_keeps_year() -> None:
    """跨年区间不得丢年，避免书架出现「1月20–1月16日」倒挂感。"""
    shown = resolve_display_title(
        {
            "title": "夏睿彤年度精选2",
            "displayTitle": "旅行 · 1月20–1月16日",
            "places": ["旅途"],
            "dateStart": "2024-01-20",
            "dateEnd": "2025-01-16",
        }
    )
    assert shown == "旅行 · 24.1.20–25.1.16"
    assert "1月20–1月16日" not in shown


def test_date_fallback_same_year_span_unchanged() -> None:
    shown = resolve_display_title(
        {
            "title": "王丹昙华林2",
            "places": ["武汉"],
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-02",
        }
    )
    assert shown == "武汉 · 7月1–7月2日"
