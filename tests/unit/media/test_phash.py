"""Perceptual hash dedupe."""

from __future__ import annotations

from PIL import Image

from travelogue.media.phash import dhash_hex, hamming_distance_hex, is_near_duplicate


def test_dhash_differs_for_different_images():
    import random

    a = Image.new("RGB", (200, 200))
    b = Image.new("RGB", (200, 200))
    a.putdata([(random.randint(0, 255), 0, 0) for _ in range(200 * 200)])
    b.putdata([(0, random.randint(0, 255), 0) for _ in range(200 * 200)])
    assert dhash_hex(a) != dhash_hex(b)


def test_near_duplicate_same_image():
    img = Image.new("RGB", (800, 600), (128, 64, 32))
    h1 = dhash_hex(img)
    h2 = dhash_hex(img.copy())
    assert is_near_duplicate(h1, h2, threshold=0)
    assert hamming_distance_hex(h1, h2) == 0
