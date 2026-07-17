"""Share-Ready W2 · BE-SR-05 title humanize."""

from travelogue.domain.title_humanize import humanize_folder_title


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
