"""Regression: dedupe replace must not delete freshly exported WebP (asset-031 class bug)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from PIL import Image, ImageFilter

from travelogue.config import IngestConfig
from travelogue.media.ingest import (
    IngestAssetBuildContext,
    IngestPhotoPayload,
    _build_asset_entry,
    _load_photo,
    _missing_derivative_paths,
    _upsert_asset,
)
from travelogue.media.sharpness import sharpness_score
from travelogue.services.trip_factory import create_trip


def test_replace_upsert_must_not_delete_same_id_derivatives(tmp_path: Path) -> None:
    """Simulates the bug: export then delete same-id WebP leaves disk empty."""
    trips = tmp_path / "trips"
    trip_json = create_trip("regression", trips, title="regression")
    trip_dir = trips / "regression"
    json.loads(trip_json.read_text(encoding="utf-8"))
    assets_dir = trip_dir / "assets"
    source_dir = trip_dir / "source"
    assets_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    album = tmp_path / "album"
    album.mkdir()
    base = Image.effect_noise((1200, 1600), 80).convert("RGB")
    blur_path = album / "a.jpg"
    sharp_path = album / "b.jpg"
    base.filter(ImageFilter.GaussianBlur(radius=10)).save(blur_path, quality=95)
    base.save(sharp_path, quality=95)
    t0 = time.time()
    os.utime(blur_path, (t0, t0))
    os.utime(sharp_path, (t0 + 1, t0 + 1))

    cfg = IngestConfig(dedupe_burst=True, dedupe_phash=False, burst_seconds=3.0)
    assets: list[dict] = []
    build_ctx = IngestAssetBuildContext(
        cfg=cfg,
        assets_dir=assets_dir,
        source_dir=source_dir,
        trip_dir=trip_dir,
        ingest_stats={},
        batch="batch-test",
        generate_crops=False,
        max_tags=5,
        geocode_enabled=False,
    )

    for photo in (blur_path, sharp_path):
        loaded = _load_photo(photo)
        img = loaded.image
        asset_id = "asset-001"
        entry = _build_asset_entry(
            build_ctx,
            IngestPhotoPayload(
                asset_id=asset_id,
                photo=photo,
                loaded=loaded,
                img=img,
                dhash="abc",
                sharpness=sharpness_score(img),
                burst_group_id="burst-001",
            ),
        )
        _upsert_asset(assets=assets, replace_index=0 if assets else None, entry=entry)

    assert len(assets) == 1
    assert not _missing_derivative_paths(trip_dir, assets)

    # Buggy pattern from broken _upsert_asset: delete derivatives for same id after export.
    for w in cfg.webp_widths:
        (assets_dir / f"asset-001-w{w}.webp").unlink(missing_ok=True)
    assert _missing_derivative_paths(trip_dir, assets)
