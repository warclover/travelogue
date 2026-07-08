"""Regression: CLIP subjectClass must be written atomically per batch.

Covers P1 fix from the Phase 3 code review — `_assign_subject_class` used to
mutate the asset dict inline, so a mid-batch failure left some assets carrying
CLIP labels and others not. After the fix the labels are collected first and
committed only once the full forward pass succeeds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("PIL.Image")
pytest.importorskip("open_clip")


def _make_asset(idx: int, rel: str) -> dict:
    return {
        "id": f"a{idx:02d}",
        "type": "image",
        "path": rel,
        "displayFile": rel,
        "width": 1200,
        "height": 1600,
        "sharpness": 0.6,
    }


def _write_jpeg(path: Path, color: tuple[int, int, int]) -> None:
    from PIL import Image

    Image.new("RGB", (64, 64), color).save(path, quality=85)


def _build_assets_dir(tmp_path: Path) -> list[dict]:
    # _resolve_asset_path resolves paths via trip_dir / rel — put files under
    # the trip root so the real CLIP forward path runs (not heuristic fallback).
    assets_root = tmp_path / "assets" / "web"
    assets_root.mkdir(parents=True)
    rels = []
    for i in range(2):
        rel = f"assets/web/img_{i}.jpg"
        _write_jpeg(tmp_path / rel, (40 + i * 20, 60, 80))
        rels.append(rel)
    return [_make_asset(i, rels[i]) for i in range(2)]


def test_subject_class_not_written_when_clip_fails_midbatch(tmp_path: Path) -> None:
    from travelogue.vision.clip_encoder import ClipEncoder

    assets = _build_assets_dir(tmp_path)

    encoder = ClipEncoder()
    # Boot the real CLIP weights once so we get a genuine model/preprocess/text
    # features stack and only swap encode_image with a flaky stand-in.
    assert encoder._ensure_clip(), "open_clip + torch must be importable for this test"
    real_encode = encoder._model.encode_image

    def always_fail(_tensor):
        raise RuntimeError("simulated CLIP mid-batch failure")

    encoder._model.encode_image = always_fail  # type: ignore[assignment]
    try:
        with pytest.raises(RuntimeError):
            encoder._embed_clip(assets, trip_dir=tmp_path, deterministic=True)
    finally:
        encoder._model.encode_image = real_encode  # type: ignore[assignment]

    for asset in assets:
        assert "subjectClass" not in asset, (
            f"asset {asset['id']} carries subjectClass after mid-batch failure"
        )
        assert "subjectConfidence" not in asset


def test_subject_class_written_for_whole_batch_when_clip_succeeds(tmp_path: Path) -> None:
    from travelogue.vision.clip_encoder import SUBJECT_CLASSES, ClipEncoder

    assets = _build_assets_dir(tmp_path)

    encoder = ClipEncoder()
    assert encoder._ensure_clip()
    encoder._embed_clip(assets, trip_dir=tmp_path, deterministic=True)

    for asset in assets:
        assert asset.get("subjectClass") in SUBJECT_CLASSES, asset
        assert 0.0 <= float(asset.get("subjectConfidence", -1)) <= 1.0
