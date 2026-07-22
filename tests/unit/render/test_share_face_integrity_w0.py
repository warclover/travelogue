"""Share-Face Integrity W0 · BE-SFI-01/02 context filter + empty overlay."""

from __future__ import annotations

from travelogue.domain.share_face_copy import (
    is_unsafe_share_copy,
    sanitize_share_copy,
    sanitize_share_copy_tracked,
)
from travelogue.render.context import media_card_classes


def test_bans_example_trip_leak() -> None:
    assert is_unsafe_share_copy("示例游记")
    assert sanitize_share_copy("5月27日·示例游记") == ""


def test_edited_exemption() -> None:
    text, blanked = sanitize_share_copy_tracked(
        "白天，傍晚", kind="decorLine", edited=True
    )
    assert text == "白天，傍晚"
    assert blanked is False


def test_decor_line_weak_enum_blanked() -> None:
    text, blanked = sanitize_share_copy_tracked("白天，傍晚", kind="decorLine")
    assert text == ""
    assert blanked is True


def test_media_card_no_overlay_class_when_empty() -> None:
    classes = media_card_classes(
        {"bleed": True, "fill": True, "overlay": True},
        {"type": "image"},
        has_overlay_text=False,
    )
    assert "media-card--overlay" not in classes
    classes_on = media_card_classes(
        {"overlay": True},
        {"type": "image"},
        has_overlay_text=True,
    )
    assert "media-card--overlay" in classes_on
