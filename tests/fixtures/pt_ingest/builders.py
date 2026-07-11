"""PT-A* album builders (Pipeline Throughput algorithm fixtures).

Images are generated at test time (no large binaries in git).
Paths align with IMPLEMENTATION §4.1 naming.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def write_burst_album(album: Path, *, n: int = 5, base_t: float = 1_700_000_000.0) -> Path:
    """PT-A1 · frames within 3s, sharpness ascending."""
    album.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        img = Image.new("RGB", (900, 1200), (30, 40, 50))
        draw = ImageDraw.Draw(img)
        step = max(2, 20 - i * 3)
        for x in range(0, 900, step):
            draw.line((x, 0, x, 1200), fill=(200, 200, 200))
        if i < 2:
            img = img.filter(ImageFilter.GaussianBlur(radius=2.5 - i * 0.5))
        path = album / f"b{i:02d}.jpg"
        img.save(path, quality=95)
        os.utime(path, (base_t + i * 0.4, base_t + i * 0.4))
    return album


def write_phash_album(album: Path, *, base_t: float = 1_700_000_000.0) -> Path:
    """PT-A2 · 2 near-duplicates + 1 unrelated."""
    album.mkdir(parents=True, exist_ok=True)
    base = Image.new("RGB", (1000, 1200), (80, 90, 100))
    draw = ImageDraw.Draw(base)
    draw.rectangle((100, 100, 400, 500), fill=(200, 50, 50))
    base.save(album / "near_a.jpg", quality=95)
    near_b = base.copy()
    ImageDraw.Draw(near_b).rectangle((105, 105, 405, 505), fill=(198, 52, 52))
    near_b.save(album / "near_b.jpg", quality=95)
    other = Image.new("RGB", (1000, 1200), (10, 180, 40))
    ImageDraw.Draw(other).ellipse((200, 200, 700, 900), fill=(255, 255, 0))
    other.save(album / "other.jpg", quality=95)
    for i, name in enumerate(("near_a.jpg", "near_b.jpg", "other.jpg")):
        os.utime(album / name, (base_t + i * 600, base_t + i * 600))
    return album


def write_face_album(album: Path, *, base_t: float = 1_700_000_000.0) -> Path:
    """PT-A3 · portrait with off-center skin oval (Haar may or may not fire)."""
    album.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1200, 1600), (40, 45, 50))
    draw = ImageDraw.Draw(img)
    # Off-center "face" blob — serial/parallel must agree on focal either way.
    draw.ellipse((620, 280, 980, 720), fill=(210, 170, 140))
    draw.ellipse((700, 400, 740, 440), fill=(40, 40, 40))
    draw.ellipse((860, 400, 900, 440), fill=(40, 40, 40))
    draw.arc((740, 500, 860, 600), start=20, end=160, fill=(120, 60, 60), width=4)
    path = album / "face_portrait.jpg"
    img.save(path, quality=95)
    os.utime(path, (base_t, base_t))
    # Distractor landscape so album has ≥2 photos for parallel min_photos
    land = Image.new("RGB", (1600, 1000), (20, 80, 140))
    ImageDraw.Draw(land).rectangle((0, 600, 1600, 1000), fill=(30, 120, 40))
    land_path = album / "landscape.jpg"
    land.save(land_path, quality=92)
    os.utime(land_path, (base_t + 900, base_t + 900))
    return album


def write_cull_album(
    album: Path,
    *,
    n_good: int = 28,
    n_flat: int = 4,
    base_t: float = 1_700_000_000.0,
) -> Path:
    """PT-A4 · ≥30 photos with flat/low-detail frames for global cull."""
    album.mkdir(parents=True, exist_ok=True)
    for i in range(n_good):
        img = Image.new("RGB", (1600, 1200), (40 + i * 3, 60, 90))
        draw = ImageDraw.Draw(img)
        for x in range(0, 1600, 28):
            draw.line((x, 0, x, 1200), fill=(20 + (x // 28 + i) % 200, 90, 150), width=2)
        path = album / f"good_{i:02d}.jpg"
        img.save(path, quality=92)
        os.utime(path, (base_t + i * 45, base_t + i * 45))
    for i in range(n_flat):
        shade = 30 + i * 15
        path = album / f"flat_{i:02d}.jpg"
        Image.new("RGB", (1600, 1200), (shade, shade, shade)).save(path, quality=90)
        os.utime(path, (base_t + (n_good + i) * 45, base_t + (n_good + i) * 45))
    return album
