"""Share-Ready W2 · BE-SR-05 title humanize."""

from travelogue.domain.title_humanize import humanize_folder_title


def test_humanize_strips_hash_and_handtest_suffix() -> None:
    assert humanize_folder_title("linzhi_a1b2c3d4e5f6") == "linzhi"
    assert humanize_folder_title("ux-handtest-photos-v2") == "我的旅途"
    assert humanize_folder_title("京都雨后") == "京都雨后"


def test_humanize_empty_and_noise() -> None:
    assert humanize_folder_title("") == "我的旅途"
    assert humanize_folder_title("新建文件夹") == "我的旅途"
    assert humanize_folder_title("my_trip_photos") == "my trip photos"
