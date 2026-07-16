"""PRD-MEDIA-REFERENCE-STORAGE-V1 · resolve / cleanup / reference ingest."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.config.ingest import IngestConfig, ingest_from_dict
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.source_resolve import (
    MediaSourceMissingError,
    build_source_ref,
    compute_storage_mode,
    file_content_sig,
    remount_album,
    resolve_source_path,
)
from travelogue.media.storage_cleanup import deep_cleanup_source, safe_cleanup_trip
from travelogue.services.trip_factory import create_trip


def _album(tmp: Path, n: int = 4) -> Path:
    album = tmp / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", (640, 480), color=(i * 40, 80, 120)).save(album / f"p{i}.jpg")
    return album


def test_ingest_copy_source_files_default_true():
    cfg = ingest_from_dict({})
    assert cfg.copy_source_files is True
    cfg2 = ingest_from_dict({"copy_source_files": False})
    assert cfg2.copy_source_files is False


def test_resolve_source_path_prefers_materialized_then_ref(tmp_path: Path):
    trip_dir = tmp_path / "trip"
    (trip_dir / "source").mkdir(parents=True)
    src = trip_dir / "source" / "asset-001.jpg"
    Image.new("RGB", (32, 32), color=(1, 2, 3)).save(src)
    album = tmp_path / "album" / "orig.jpg"
    album.parent.mkdir()
    Image.new("RGB", (32, 32), color=(9, 9, 9)).save(album)

    asset = {
        "id": "asset-001",
        "sourceFile": "source/asset-001.jpg",
        "sourceRef": build_source_ref(album_root=album.parent, source_path=album),
    }
    assert resolve_source_path(asset, trip_dir) == src.resolve()

    src.unlink()
    resolved = resolve_source_path(asset, trip_dir)
    assert resolved == album.resolve()

    album.unlink()
    assert resolve_source_path(asset, trip_dir) is None
    with pytest.raises(MediaSourceMissingError):
        resolve_source_path(asset, trip_dir, raise_on_missing=True)


def test_reference_ingest_skips_source_jpeg(tmp_path: Path):
    import json

    album = _album(tmp_path, 4)
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip(trip_id="ref-trip", trips_dir=trips, title="ref")
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = IngestConfig(
        copy_source_files=False,
        webp_widths=(640,),
        generate_crops=False,
        detect_faces=False,
        max_photos=10,
    )
    from travelogue.config.app import AppConfig

    app = AppConfig(ingest=cfg)
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=app)

    source_files = list((trip_dir / "source").glob("*.jpg")) if (trip_dir / "source").is_dir() else []
    assert source_files == []
    assets = trip.get("assets") or []
    assert len(assets) >= 4
    for a in assets:
        assert "sourceFile" not in a or a.get("sourceFile") in (None, "")
        assert isinstance(a.get("sourceRef"), dict)
        assert a["sourceRef"].get("kind") == "filesystem"
        assert Path(a["sourceRef"]["path"]).is_file()
        assert a.get("contentSig")
    assert compute_storage_mode(trip, trip_dir) == "referenced"


def test_copy_ingest_writes_source_and_source_ref(tmp_path: Path):
    import json

    album = _album(tmp_path, 4)
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip(trip_id="copy-trip", trips_dir=trips, title="copy")
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = IngestConfig(
        copy_source_files=True,
        webp_widths=(640,),
        generate_crops=False,
        detect_faces=False,
        max_photos=10,
    )
    from travelogue.config.app import AppConfig

    app = AppConfig(ingest=cfg)
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, app_cfg=app)
    assert list((trip_dir / "source").glob("*.jpg"))
    for a in trip.get("assets") or []:
        assert a.get("sourceFile", "").startswith("source/")
        assert isinstance(a.get("sourceRef"), dict)


def test_safe_and_deep_cleanup(tmp_path: Path):
    trip_dir = tmp_path / "t1"
    (trip_dir / "source").mkdir(parents=True)
    (trip_dir / ".cluster-cache").mkdir()
    cache_file = trip_dir / ".cluster-cache" / "x.bin"
    cache_file.write_bytes(b"12345")
    src = trip_dir / "source" / "asset-001.jpg"
    Image.new("RGB", (16, 16)).save(src)
    album = tmp_path / "a" / "p.jpg"
    album.parent.mkdir()
    Image.new("RGB", (16, 16)).save(album)

    trip = {
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "sourceFile": "source/asset-001.jpg",
                "sourceRef": build_source_ref(album_root=album.parent, source_path=album),
                "contentSig": "1:abc",
            }
        ]
    }
    safe = safe_cleanup_trip(trip_dir)
    assert safe.bytes_freed >= 5
    assert not (trip_dir / ".cluster-cache").exists()
    assert src.is_file()

    deep = deep_cleanup_source(trip, trip_dir, accept_derivatives_only=False)
    assert deep.bytes_freed > 0
    assert not src.exists()
    assert "sourceFile" not in trip["assets"][0]
    assert compute_storage_mode(trip, trip_dir) == "referenced"


def test_deep_cleanup_refused_without_ref(tmp_path: Path):
    trip_dir = tmp_path / "t2"
    (trip_dir / "source").mkdir(parents=True)
    src = trip_dir / "source" / "asset-001.jpg"
    Image.new("RGB", (16, 16)).save(src)
    trip = {
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "sourceFile": "source/asset-001.jpg",
            }
        ]
    }
    deep = deep_cleanup_source(trip, trip_dir, accept_derivatives_only=False)
    assert src.is_file()
    assert any(i.status == "skipped" for i in deep.items)


def test_remount_matches_by_content_sig(tmp_path: Path):
    old = tmp_path / "old" / "p0.jpg"
    old.parent.mkdir(parents=True)
    new_root = tmp_path / "new"
    moved = new_root / "nested" / "p0.jpg"
    moved.parent.mkdir(parents=True)
    Image.new("RGB", (40, 40), color=(10, 20, 30)).save(old)
    Image.new("RGB", (40, 40), color=(10, 20, 30)).save(moved)
    sig = file_content_sig(moved)
    trip = {
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "contentSig": sig,
                "sourceRef": {
                    "kind": "filesystem",
                    "path": str(old.resolve()),
                    "albumRoot": str(old.parent.resolve()),
                    "relativePath": "p0.jpg",
                },
            }
        ]
    }
    result = remount_album(trip, new_root)
    assert result.matched == 1
    assert result.missing == 0
    assert result.content_changed == 0
    assert result.ok
    assert Path(trip["assets"][0]["sourceRef"]["path"]) == moved.resolve()
    assert str(new_root.resolve()) in trip["media"]["albumRoots"]


def test_remount_content_changed_rejects_same_name(tmp_path: Path):
    """AC-MRS-13 · same relative name but different bytes must not auto-link."""
    album = tmp_path / "album"
    album.mkdir()
    candidate = album / "p0.jpg"
    Image.new("RGB", (40, 40), color=(1, 1, 1)).save(candidate)
    trip = {
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "contentSig": "999:deadbeef",
                "sourceRef": {
                    "kind": "filesystem",
                    "path": str(tmp_path / "gone" / "p0.jpg"),
                    "albumRoot": str(tmp_path / "gone"),
                    "relativePath": "p0.jpg",
                },
            }
        ]
    }
    before = trip["assets"][0]["sourceRef"]["path"]
    result = remount_album(trip, album)
    assert result.matched == 0
    assert result.content_changed == 1
    assert result.error_code == "E_MEDIA_CONTENT_CHANGED"
    assert trip["assets"][0]["sourceRef"]["path"] == before


def test_worker_config_respects_copy_source_files_false():
    """AC-MRS-02b · parallel worker must inherit reference-mode flag."""
    from travelogue.media.ingest_worker import WorkerIngestConfig

    cfg = IngestConfig(copy_source_files=False)
    worker = WorkerIngestConfig.from_ingest_config(cfg)
    assert worker.copy_source_files is False
    forced = WorkerIngestConfig.from_ingest_config(cfg, force_materialize=True)
    assert forced.copy_source_files is True


def test_incremental_missing_sets_error_code(tmp_path: Path):
    """AC-MRS-12 · pending replay miss is observable, not silent."""
    import json

    from travelogue.config.app import AppConfig

    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip(trip_id="inc-miss", trips_dir=trips, title="inc")
    trip_dir = trip_json.parent
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    trip["assets"] = [
        {
            "id": "asset-001",
            "type": "image",
            "sourceRef": {
                "kind": "filesystem",
                "path": str(tmp_path / "missing" / "gone.jpg"),
            },
            "contentSig": "1:abc",
        }
    ]
    trip["pipeline"] = {
        "status": "structure_locked",
        "pendingAssets": ["asset-001"],
        "locks": {"structure": True, "copy": False},
    }
    app = AppConfig(
        ingest=IngestConfig(
            copy_source_files=False,
            webp_widths=(640,),
            generate_crops=False,
            detect_faces=False,
            max_photos=10,
        )
    )
    result = ingest_into_trip(
        trip,
        trip_dir,
        from_dir=None,
        incremental=True,
        dedupe=False,
        app_cfg=app,
        min_assets=1,
    )
    assert result.stats.get("errorCode") == "E_MEDIA_INCREMENTAL_SOURCE"
    assert "asset-001" in (result.stats.get("incremental_source_missing") or [])
