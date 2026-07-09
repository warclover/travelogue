"""Sharpness score tests."""

from __future__ import annotations

from PIL import Image, ImageFilter

from travelogue.media.sharpness import sharpness_score


def test_sharpness_blur_lower_than_sharp() -> None:
    base = Image.effect_noise((800, 600), 64).convert("RGB")
    sharp = sharpness_score(base)
    blurred = sharpness_score(base.filter(ImageFilter.GaussianBlur(radius=6)))
    assert sharp > blurred
