"""PRD-PIPELINE-PERF-V1 · R2.3 · pyramid resize flag defaults off."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.config.ingest import IngestConfig, ingest_from_dict
from travelogue.media.image_ops import export_webp_variants


def test_webp_pyramid_default_false() -> None:
    assert IngestConfig().webp_pyramid is False
    assert ingest_from_dict({}).webp_pyramid is False


def test_export_webp_pyramid_true_writes_all_widths(tmp_path: Path) -> None:
    img = Image.new("RGB", (3200, 2000), (10, 20, 30))
    assets = tmp_path / "assets"
    assets.mkdir()
    _display, srcset, out_w, out_h, _m, _w = export_webp_variants(
        img,
        assets,
        "a1",
        widths=(800, 1600, 2400),
        quality=80,
        webp_method=0,
        pyramid=True,
    )
    widths = [int(e["width"]) for e in srcset]
    assert widths == [800, 1600, 2400]
    for w in widths:
        assert (assets / f"a1-w{w}.webp").is_file()
    assert out_w == 2400


def test_export_webp_default_non_pyramid(tmp_path: Path) -> None:
    img = Image.new("RGB", (1600, 1000), (10, 20, 30))
    assets = tmp_path / "assets"
    assets.mkdir()
    _display, srcset, *_rest = export_webp_variants(
        img,
        assets,
        "a1",
        widths=(800, 1600),
        quality=80,
        webp_method=0,
    )
    assert [int(e["width"]) for e in srcset] == [800, 1600]
