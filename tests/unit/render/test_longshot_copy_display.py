"""M14 · longshot copyDisplay capture hook."""

from __future__ import annotations

from travelogue.export.longshot import _APPLY_PHOTOS_MODE_JS, _apply_copy_display


def test_apply_photos_mode_js_sets_attributes() -> None:
    assert "data-photos-only" in _APPLY_PHOTOS_MODE_JS
    assert "data-copy-display" in _APPLY_PHOTOS_MODE_JS
    assert "'photos'" in _APPLY_PHOTOS_MODE_JS


class _FakePage:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def evaluate(self, script: str) -> None:
        self.calls.append(script)


def test_apply_copy_display_photos_only() -> None:
    page = _FakePage()
    _apply_copy_display(page, "photos")
    assert len(page.calls) == 1
    assert page.calls[0] == _APPLY_PHOTOS_MODE_JS


def test_apply_copy_display_full_skips() -> None:
    page = _FakePage()
    _apply_copy_display(page, "full")
    assert page.calls == []
