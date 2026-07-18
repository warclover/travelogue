"""Share-Face Closeout W0 · AC-SFC-01/02 · FX-SFC-01～03."""

from travelogue.domain.share_face_copy import is_unsafe_share_copy, sanitize_share_copy


def test_bans_instructional_captions() -> None:
    assert sanitize_share_copy("示例游记的竖幅。") == ""
    assert sanitize_share_copy("抬头看见示例游记。") == ""
    assert is_unsafe_share_copy("慢慢翻这一页")


def test_bans_weak_daypart_enum() -> None:
    assert sanitize_share_copy("夜景，白天") == ""
    assert sanitize_share_copy("白天，傍晚") == ""
    assert sanitize_share_copy("上午、下午") == ""


def test_bans_title_echo() -> None:
    assert sanitize_share_copy("武大--米娜", title="武大 米娜", kind="caption") == ""
    assert sanitize_share_copy("武大 米娜", title="武大 米娜", kind="alt") == ""


def test_keeps_short_place_date() -> None:
    assert sanitize_share_copy("京都") == "京都"
    assert sanitize_share_copy("5月27日 · 京都") == "5月27日 · 京都"
