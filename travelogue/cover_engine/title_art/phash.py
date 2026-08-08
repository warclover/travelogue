"""轻量感知哈希（SHD-CAL-01 · AC-CAL-02 金样对比）。

零外部依赖：用 Pillow 做 average hash。透明 PNG 先合成到白底再哈希，
避免「大片透明 vs 不透明」主导汉明距离。
"""

from __future__ import annotations

from PIL import Image


def average_hash(img: Image.Image, *, hash_size: int = 16) -> int:
    """返回 ``hash_size**2`` 位的 average hash（默认 256 bit）。"""
    rgba = img.convert("RGBA")
    canvas = Image.new("RGB", rgba.size, (255, 255, 255))
    canvas.paste(rgba, mask=rgba.split()[3])
    gray = canvas.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(gray.get_flattened_data())
    avg = sum(pixels) / max(len(pixels), 1)
    bits = 0
    for i, value in enumerate(pixels):
        if value >= avg:
            bits |= 1 << i
    return bits


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()
