"""Share-Face Closeout W0 · AC-SFC-01/02 · FX-SFC-01～03."""

from travelogue.domain.share_face_copy import is_unsafe_share_copy, sanitize_share_copy


def test_bans_instructional_captions() -> None:
    assert sanitize_share_copy("示例游记的竖幅。") == ""
    assert sanitize_share_copy("抬头看见示例游记。") == ""
    assert sanitize_share_copy("示例游记") == ""
    assert sanitize_share_copy("5月27日·示例游记") == ""
    assert is_unsafe_share_copy("慢慢翻这一页")


def test_bans_weak_daypart_enum() -> None:
    assert sanitize_share_copy("夜景，白天") == ""
    assert sanitize_share_copy("白天，傍晚") == ""
    assert sanitize_share_copy("上午、下午") == ""


def test_bans_title_echo() -> None:
    assert sanitize_share_copy("武大--米娜", title="武大 米娜", kind="caption") == ""
    assert sanitize_share_copy("武大 米娜", title="武大 米娜", kind="alt") == ""
    # SFP D-SFP-05 · 「日期 · 题名」回声
    assert (
        sanitize_share_copy("5月27日 · 武大樱花", title="武大樱花", kind="caption")
        == ""
    )
    # 封面 lead/hook 同样抑制题名回声（手机长图三行重题）
    assert (
        sanitize_share_copy("王丹昙华林半日游 · 10月5日", title="王丹昙华林半日游", kind="lead")
        == ""
    )
    assert sanitize_share_copy("王丹昙华林半日游", title="王丹昙华林半日游", kind="lead") == ""
    assert (
        sanitize_share_copy("昙华林半日，梧桐影里", title="王丹昙华林半日游", kind="lead")
        == "昙华林半日，梧桐影里"
    )


def test_bans_dirty_double_dash() -> None:
    assert sanitize_share_copy("武大--米娜 · 2天", kind="lead") == ""


def test_keeps_short_place_date() -> None:
    assert sanitize_share_copy("京都") == "京都"
    assert sanitize_share_copy("5月27日 · 京都") == "5月27日 · 京都"
