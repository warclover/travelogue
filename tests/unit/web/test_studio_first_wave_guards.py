"""First-wave Studio path, upload, JSON, and write-guard tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from tests.studio_test_helpers import MockStudioHandler
from travelogue.media.storage_cleanup import contained_trip_source, deep_cleanup_source
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_auth import studio_write_guard
from travelogue.web.studio_handlers.storage_handlers import (
    handle_storage_cleanup,
    handle_storage_remount,
)
from travelogue.web.studio_json import loads_json_object, parse_content_length
from travelogue.web.studio_uploads import save_upload_files, safe_upload_basename


@pytest.mark.unit
def test_parse_content_length_rejects_negative_and_oversize() -> None:
    assert parse_content_length(None, max_bytes=10) == 0
    assert parse_content_length("8", max_bytes=10) == 8
    with pytest.raises(ValueError):
        parse_content_length("-1", max_bytes=10)
    with pytest.raises(ValueError):
        parse_content_length("nope", max_bytes=10)
    with pytest.raises(OverflowError):
        parse_content_length("11", max_bytes=10)


@pytest.mark.unit
def test_loads_json_object_empty_vs_invalid() -> None:
    assert loads_json_object(b"") == {}
    assert loads_json_object(b'{"safe": true}') == {"safe": True}
    with pytest.raises(ValueError):
        loads_json_object(b"{")
    with pytest.raises(ValueError):
        loads_json_object(b"[1]")


@pytest.mark.unit
def test_safe_upload_basename_rejects_escape_and_devices() -> None:
    assert safe_upload_basename("photos/ok.jpg") == "ok.jpg"
    assert safe_upload_basename("京都 夜.jpg") == "京都 夜.jpg"
    assert safe_upload_basename("../../etc/passwd") is None
    assert safe_upload_basename("C:/temp/evil.jpg") is None
    assert safe_upload_basename(r"\\server\share\a.jpg") is None
    assert safe_upload_basename("ok.jpg:Zone.Identifier") is None
    assert safe_upload_basename("CON") is None
    assert safe_upload_basename("NUL.txt") is None


@pytest.mark.unit
def test_save_upload_files_drive_and_dedup(tmp_path: Path) -> None:
    upload_dir = tmp_path / "job-1"
    upload_dir.mkdir()
    sentinel = tmp_path / "sentinel.bin"
    sentinel.write_bytes(b"keep")
    saved = save_upload_files(
        upload_dir,
        [
            (str(sentinel), b"overwrite"),
            (r"C:\temp\evil.jpg", b"x"),
            ("ok.jpg", b"one"),
            ("ok.jpg", b"two"),
        ],
    )
    assert saved == 2
    assert sentinel.read_bytes() == b"keep"
    assert (upload_dir / "ok.jpg").read_bytes() == b"one"
    assert (upload_dir / "ok-2.jpg").read_bytes() == b"two"


@pytest.mark.unit
def test_contained_trip_source_rejects_escape(tmp_path: Path) -> None:
    trip_dir = tmp_path / "trip"
    (trip_dir / "source").mkdir(parents=True)
    sentinel = tmp_path / "outside.jpg"
    sentinel.write_bytes(b"keep")
    assert contained_trip_source(trip_dir, "source/a.jpg") == (trip_dir / "source" / "a.jpg").resolve()
    assert contained_trip_source(trip_dir, "../outside.jpg") is None
    assert contained_trip_source(trip_dir, str(sentinel)) is None
    assert contained_trip_source(trip_dir, "assets/a.jpg") is None


@pytest.mark.unit
def test_deep_cleanup_does_not_delete_outside_source(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t"
    (trip_dir / "source").mkdir(parents=True)
    sentinel = tmp_path / "secret.jpg"
    Image.new("RGB", (8, 8)).save(sentinel)
    trip = {
        "assets": [
            {"id": "a1", "type": "image", "sourceFile": str(sentinel)},
            {"id": "a2", "type": "image", "sourceFile": "../secret.jpg"},
        ]
    }
    deep = deep_cleanup_source(trip, trip_dir, accept_derivatives_only=True)
    assert sentinel.is_file()
    assert all(item.status == "skipped" for item in deep.items)
    assert deep.bytes_freed == 0


@pytest.mark.unit
def test_storage_cleanup_rejects_escaped_trip_ids(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-01", trips_dir)
    sentinel = tmp_path / "outside" / "trip.json"
    sentinel.parent.mkdir()
    sentinel.write_text("{}", encoding="utf-8")
    handler = MockStudioHandler(
        trips_dir,
        json_body={"tripIds": [str(sentinel.parent)], "safe": True},
    )
    handler.command = "POST"
    handle_storage_cleanup(handler)
    assert handler.response is not None
    assert handler.response[0] == 400
    assert handler.response[1]["error"] == "E_STUDIO_PATH"
    assert sentinel.is_file()


@pytest.mark.unit
def test_storage_cleanup_safe_path_still_works(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-01", trips_dir)
    cache = trip_json.parent / ".cluster-cache"
    cache.mkdir()
    (cache / "x").write_bytes(b"12345")
    handler = MockStudioHandler(trips_dir, json_body={"tripIds": ["demo-01"], "safe": True})
    handler.command = "POST"
    handle_storage_cleanup(handler)
    assert handler.response is not None
    assert handler.response[0] == 200
    assert handler.response[1]["ok"] is True
    assert not cache.exists()


@pytest.mark.unit
def test_storage_remount_rejects_escaped_trip_id(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-01", trips_dir)
    album = tmp_path / "album"
    album.mkdir()
    handler = MockStudioHandler(
        trips_dir,
        json_body={"tripId": "../outside", "albumPath": str(album)},
    )
    handler.command = "POST"
    handle_storage_remount(handler)
    assert handler.response is not None
    assert handler.response[0] == 400
    assert handler.response[1]["error"] == "E_STUDIO_PATH"


@pytest.mark.unit
def test_write_guard_rejects_cross_origin_and_text_plain() -> None:
    assert studio_write_guard(
        method="POST",
        path="/__travelogue/storage/cleanup",
        headers={"Content-Type": "application/json", "Host": "127.0.0.1:8766"},
        allow_lan=False,
    )
    assert not studio_write_guard(
        method="POST",
        path="/__travelogue/storage/cleanup",
        headers={
            "Content-Type": "application/json",
            "Host": "127.0.0.1:8766",
            "Origin": "https://evil.example",
        },
        allow_lan=False,
    )
    assert not studio_write_guard(
        method="POST",
        path="/__travelogue/storage/cleanup",
        headers={"Content-Type": "text/plain", "Host": "127.0.0.1:8766"},
        allow_lan=False,
    )
    assert studio_write_guard(
        method="POST",
        path="/__travelogue/import",
        headers={
            "Content-Type": "multipart/form-data; boundary=x",
            "Host": "127.0.0.1:8766",
        },
        allow_lan=False,
    )
    assert not studio_write_guard(
        method="POST",
        path="/__travelogue/cancel",
        headers={"Content-Type": "application/json", "Host": "evil.example"},
        allow_lan=False,
    )
