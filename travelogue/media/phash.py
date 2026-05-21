"""Perceptual hash helpers for near-duplicate photos (no extra deps)."""

from __future__ import annotations

from PIL import Image


def dhash_hex(img: Image.Image, size: int = 8) -> str:
    """
    Difference hash (64-bit for size=8).

    Robust enough for burst/similar frames; compare with hamming_distance.
    """
    gray = img.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(gray.get_flattened_data())
    bits: list[str] = []
    for row in range(size):
        row_off = row * (size + 1)
        for col in range(size):
            bits.append("1" if pixels[row_off + col] > pixels[row_off + col + 1] else "0")
    return f"{int(''.join(bits), 2):016x}"


def hamming_distance_hex(a: str, b: str) -> int:
    if len(a) != len(b):
        b = b.zfill(len(a))
    ia = int(a, 16)
    ib = int(b, 16)
    return (ia ^ ib).bit_count()


def is_near_duplicate(a: str, b: str, *, threshold: int = 8) -> bool:
    return hamming_distance_hex(a, b) <= threshold
