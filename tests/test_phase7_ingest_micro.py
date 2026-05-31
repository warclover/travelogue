"""Phase 7 ingest micro-optimization tests (M27-B)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.config import IngestConfig
from travelogue.media.color_metrics import color_metrics_from_thumb, mean_luma, dominant_tone_hex
from travelogue.media.subject_detect import reset_cascade_classifier


def test_shared_color_thumb_close_to_legacy() -> None:
    img = Image.new("RGB", (1200, 800), (100, 140, 180))
    luma_shared, tone_shared = color_metrics_from_thumb(img, thumb_px=32)
    luma_legacy = mean_luma(img)
    tone_legacy = dominant_tone_hex(img)
    assert abs(luma_shared - luma_legacy) < 0.08
    assert tone_shared == tone_legacy or tone_shared[:5] == tone_legacy[:5]


def test_webp_method_config_default() -> None:
    cfg = IngestConfig()
    assert cfg.webp_method == 4
    assert cfg.shared_color_thumb_px == 32
    assert cfg.webp_widths == (800, 1600, 2400, 3200)


def test_screen_full_sizes_requests_hd_tier() -> None:
    from travelogue.render.context import pick_image_sizes

    sizes = pick_image_sizes("web", "screen_full")
    assert "3200px" in sizes
    assert "2400px" in sizes


def test_cascade_singleton_reset() -> None:
    reset_cascade_classifier()
