"""Unit: NR prefer_web=false resolves source JPEG (AC-PT-12 / D-PT-07)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.vision.clip_encoder import _resolve_asset_path


def test_resolve_prefers_source_when_prefer_web_false(tmp_path: Path) -> None:
    aid = "asset-001"
    source = tmp_path / "source" / f"{aid}.jpg"
    webp = tmp_path / "assets" / f"{aid}-w640.webp"
    source.parent.mkdir(parents=True)
    webp.parent.mkdir(parents=True)
    Image.new("RGB", (64, 80), (10, 20, 30)).save(source, quality=90)
    webp.write_bytes(b"RIFF....WEBP")  # not a real decode; existence only

    asset = {
        "id": aid,
        "sourceFile": f"source/{aid}.jpg",
        "displayFile": f"assets/{aid}-w640.webp",
        "srcset": [{"width": 640, "file": f"assets/{aid}-w640.webp"}],
    }
    path, used_web = _resolve_asset_path(asset, tmp_path, prefer_web_derivative=False)
    assert path == source.resolve()
    assert used_web is False


def test_resolve_can_use_web_when_prefer_web_true(tmp_path: Path) -> None:
    aid = "asset-002"
    source = tmp_path / "source" / f"{aid}.jpg"
    webp = tmp_path / "assets" / f"{aid}-w800.webp"
    source.parent.mkdir(parents=True)
    webp.parent.mkdir(parents=True)
    Image.new("RGB", (64, 80), (1, 2, 3)).save(source, quality=90)
    Image.new("RGB", (32, 40), (4, 5, 6)).save(webp, format="WEBP")

    asset = {
        "id": aid,
        "sourceFile": f"source/{aid}.jpg",
        "srcset": [{"width": 800, "file": f"assets/{aid}-w800.webp"}],
    }
    path, used_web = _resolve_asset_path(asset, tmp_path, prefer_web_derivative=True)
    assert path == webp.resolve()
    assert used_web is True
