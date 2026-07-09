from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from travelogue.config import AppConfig, CullConfig
from travelogue.curation.photo_cull import CULL_EXCLUDE_REASONS
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _make_textured(path: Path, *, idx: int, width: int = 1800, height: int = 1200) -> None:
    img = Image.new("RGB", (width, height), (40 + idx * 10, 60 + idx * 5, 90 + idx * 3))
    draw = ImageDraw.Draw(img)
    for x in range(0, width, 24):
        color = (20 + (x // 24) % 220, 80 + (idx * 7) % 100, 160)
        draw.line([(x, 0), (x, height - 1)], fill=color, width=2)
    img.save(path, quality=92)


def _make_flat(path: Path, *, shade: int) -> None:
    Image.new("RGB", (1800, 1200), (shade, shade, shade)).save(path, quality=92)


def _album_for_regression(tmp_path: Path) -> Path:
    album = tmp_path / "album-regression"
    album.mkdir()
    stamp = time.time() - 120
    for i in range(4):
        p = album / f"texture-{i}.jpg"
        _make_textured(p, idx=i)
        os.utime(p, (stamp + i * 10, stamp + i * 10))
    for i in range(2):
        p = album / f"flat-{i}.jpg"
        _make_flat(p, shade=35 + i * 20)
        os.utime(p, (stamp + (4 + i) * 10, stamp + (4 + i) * 10))
    return album


def _dual_album_with_low_res(tmp_path: Path) -> Path:
    root = tmp_path / "album-dual-lowres"
    featured = root / "精选"
    material = root / "素材上传"
    featured.mkdir(parents=True)
    material.mkdir(parents=True)
    stamp = time.time() - 180
    for i in range(2):
        p = featured / f"feat-{i}.jpg"
        _make_textured(p, idx=20 + i, width=3200, height=2400)
        os.utime(p, (stamp + i * 10, stamp + i * 10))
    for i in range(3):
        p = material / f"mat-ok-{i}.jpg"
        _make_textured(p, idx=40 + i, width=3200, height=2400)
        os.utime(p, (stamp + (2 + i) * 10, stamp + (2 + i) * 10))
    low = material / "mat-low.jpg"
    Image.new("RGB", (320, 320), (45, 45, 45)).save(low, quality=90)
    os.utime(low, (stamp + 60, stamp + 60))
    return root


def test_ingest_e2e_cull_explain_and_summary(tmp_path: Path) -> None:
    album = _album_for_regression(tmp_path)
    trips = tmp_path / "trips"
    trip_json = create_trip("phase9-e2e-reg", trips, title="P9 回归")
    trip_dir = trips / "phase9-e2e-reg"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))

    cfg = AppConfig(
        cull=CullConfig(
            enabled=True,
            min_keep=2,
            keep_ratio_floor=0.0,
            bucketed_blur_thresholds=True,
            bucketed_blur_min_samples=2,
            score_duplicate_group_penalty=0.08,
            enable_cull_explain=True,
            recalc_strict_groups=True,
        )
    )
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=cfg)

    curation = trip.get("curation") or {}
    cull = curation.get("cullSummary") or {}
    assert cull.get("enabled") is True
    assert int(cull.get("excludedByCull") or 0) >= 1
    excluded_assets = [
        a
        for a in trip.get("assets") or []
        if not a.get("layoutEligible", True)
        and str(a.get("excludeReason") or "") in CULL_EXCLUDE_REASONS
    ]
    assert excluded_assets
    assert all((a.get("quality") or {}).get("cullExplain") for a in excluded_assets)


def test_ingest_e2e_ml_cache_reused_between_rebuilds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("torch")
    album = _album_for_regression(tmp_path)
    trips = tmp_path / "trips"
    trip_json = create_trip("phase9-e2e-ml-cache", trips, title="P9 ML 缓存")
    trip_dir = trips / "phase9-e2e-ml-cache"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))

    calls = {"n": 0}

    class _FakeOut:
        def __init__(self, values: list[float]) -> None:
            self._values = values

        def detach(self):
            return self

        def flatten(self):
            return self

        def tolist(self):
            return self._values

    class _FakeMetric:
        def __call__(self, tensor):  # noqa: ANN001
            calls["n"] += 1
            batch = int(getattr(tensor, "shape", [1])[0])
            return _FakeOut([0.71] * batch)

    monkeypatch.setattr(
        "travelogue.curation.photo_cull_ml.resolve_effective_mode",
        lambda _cfg: "ml",
    )
    monkeypatch.setattr(
        "travelogue.curation.photo_cull.resolve_effective_mode",
        lambda _cfg: "ml",
    )
    monkeypatch.setattr("travelogue.curation.photo_cull_ml.pyiqa_available", lambda: True)
    monkeypatch.setattr(
        "travelogue.curation.photo_cull_ml._get_metric",
        lambda _cfg: _FakeMetric(),
    )

    app_cfg = AppConfig(
        cull=CullConfig(
            enabled=True,
            mode="ml",
            allow_cpu_ml=True,
            min_keep=2,
            keep_ratio_floor=0.0,
        )
    )
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=app_cfg)
    first_calls = calls["n"]
    assert first_calls >= 1
    cache_file = trip_dir / "cache" / "phase9_aesthetic.json"
    assert cache_file.is_file()

    trip2 = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip2, trip_dir, from_dir=album, dedupe=False, app_cfg=app_cfg)
    assert calls["n"] == first_calls
    assert all(
        (a.get("quality") or {}).get("aestheticScore") is not None
        for a in (trip2.get("assets") or [])
    )


def test_ingest_e2e_dual_folders_with_low_res_material(tmp_path: Path) -> None:
    album = _dual_album_with_low_res(tmp_path)
    trips = tmp_path / "trips"
    trip_json = create_trip("phase9-e2e-dual-lowres", trips, title="P9 双目录低清")
    trip_dir = trips / "phase9-e2e-dual-lowres"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))

    cfg = AppConfig(
        cull=CullConfig(
            enabled=False,
            min_keep=2,
            keep_ratio_floor=0.0,
            enable_cull_explain=True,
        )
    )
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=cfg)

    assets = trip.get("assets") or []
    featured = [a for a in assets if a.get("userTier") == "featured"]
    material = [a for a in assets if a.get("userTier") == "material"]
    assert len(featured) == 2
    assert len(material) >= 3
    assert all(a.get("layoutEligible", True) for a in featured)

    curation = trip.get("curation") or {}
    low_res_ids = set(curation.get("excludedLowResAssetIds") or [])
    assert low_res_ids, "low-res material should be excluded by layout eligibility marks"
    low_res_assets = [a for a in assets if a.get("id") in low_res_ids]
    assert low_res_assets
    assert all(a.get("userTier") == "material" for a in low_res_assets)
    assert all(a.get("excludeReason") == "low_resolution" for a in low_res_assets)
