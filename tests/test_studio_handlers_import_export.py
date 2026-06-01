"""Unit tests for Studio import/export/job handlers (no full pipeline)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_constants import STUDIO_MAX_MULTIPART_BODY_BYTES
from travelogue.web.studio_handlers.export_handlers import handle_export, handle_reveal
from travelogue.web.studio_handlers.import_handlers import (
    album_path_allowed,
    handle_album_preview,
    handle_import,
    read_import_request,
)
from travelogue.web.studio_pipeline import sample_album_preview_thumbs
from travelogue.web.studio_handlers.job_handlers import handle_cancel, handle_status
from travelogue.web.studio_jobs import get_job_store, reset_job_store
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def test_handle_export_requires_trip_id(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", json_body={"confirmPrivacy": True})
    handle_export(handler)
    assert handler.response == (400, {"ok": False, "error": "tripId required"})


def test_handle_export_requires_privacy_confirm(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-01", trips_dir)
    handler = MockStudioHandler(trips_dir, json_body={"tripId": "demo-01"})
    handle_export(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_EXPORT_PRIVACY"


def test_handle_export_trip_not_found(tmp_path: Path) -> None:
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"tripId": "missing-trip", "confirmPrivacy": True},
    )
    handle_export(handler)
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_export_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-export", trips_dir, title="导出测试", place="京都")
    zip_path = trips_dir / "demo-export" / "demo-export.zip"
    zip_path.write_bytes(b"PK")

    handler = MockStudioHandler(
        trips_dir,
        json_body={"tripId": "demo-export", "confirmPrivacy": True},
    )
    with patch(
        "travelogue.export.packager.export_trip",
        return_value=zip_path,
    ):
        handle_export(handler)

    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["zipRelPath"] == "demo-export.zip"
    assert body["tripId"] == "demo-export"


def test_handle_export_surfaces_packager_error(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-bad", trips_dir)
    handler = MockStudioHandler(
        trips_dir,
        json_body={"tripId": "demo-bad", "confirmPrivacy": True},
    )
    from travelogue.export.packager import ExportError

    with patch(
        "travelogue.export.packager.export_trip",
        side_effect=ExportError("E_VALIDATE", "schema failed"),
    ):
        handle_export(handler)

    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_VALIDATE"


def test_handle_import_requires_album_path(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", json_body={"title": "测试"})
    handle_import(handler)
    assert handler.response == (400, {"ok": False, "error": "albumPath required"})


def test_read_import_request_rejects_oversized_multipart(tmp_path: Path) -> None:
    handler = MockStudioHandler(
        tmp_path / "trips",
        headers={
            "Content-Type": "multipart/form-data; boundary=----x",
            "Content-Length": str(STUDIO_MAX_MULTIPART_BODY_BYTES + 1),
        },
    )
    from travelogue.demo.build import DemoError

    with pytest.raises(DemoError) as exc:
        read_import_request(handler)
    assert exc.value.code == "E_STUDIO_BODY_TOO_LARGE"


def test_read_import_request_rejects_empty_upload(tmp_path: Path) -> None:
    boundary = b"----x"
    title_field = "title".encode("utf-8")
    title_value = "test".encode("utf-8")
    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="' + title_field + b'"\r\n\r\n'
        + title_value + b"\r\n"
        b"--" + boundary + b"--\r\n"
    )
    handler = MockStudioHandler(
        tmp_path / "trips",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
            "Content-Length": str(len(body)),
        },
        body=body,
    )
    from travelogue.demo.build import DemoError

    with pytest.raises(DemoError) as exc:
        read_import_request(handler)
    assert exc.value.code == "E_STUDIO_UPLOAD_EMPTY"


def test_album_path_allowed_accepts_upload_dir(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    from travelogue.web.studio_uploads import upload_dir_for_job

    upload_dir = upload_dir_for_job(trips_dir, "job-1")
    upload_dir.mkdir(parents=True, exist_ok=True)
    handler = MockStudioHandler(trips_dir)
    assert album_path_allowed(handler, upload_dir, trips_root=trips_dir) is True


def test_album_path_allowed_denies_local_when_trust_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trips_dir = tmp_path / "trips"
    outside = tmp_path / "outside-album"
    outside.mkdir()
    handler = MockStudioHandler(trips_dir)
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "0")
    assert album_path_allowed(handler, outside, trips_root=trips_dir) is False


def test_album_path_allowed_accepts_trip_source_dir(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    source = trips_dir / "demo-trip" / "source"
    source.mkdir(parents=True)
    handler = MockStudioHandler(trips_dir)
    assert album_path_allowed(handler, source, trips_root=trips_dir) is True


def test_album_path_allowed_denies_outside_uploads_on_lan(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    outside = tmp_path / "outside-album"
    outside.mkdir()
    handler = MockStudioHandler(trips_dir, studio_host="0.0.0.0", studio_allow_lan=True)
    assert album_path_allowed(handler, outside, trips_root=trips_dir) is False


def test_handle_import_denies_untrusted_album(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    outside = tmp_path / "outside-album"
    outside.mkdir()
    handler = MockStudioHandler(
        trips_dir,
        json_body={"albumPath": str(outside), "title": "测试"},
        studio_host="0.0.0.0",
        studio_allow_lan=True,
    )
    handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_STUDIO_ALBUM_DENIED"


def test_handle_import_accepts_loopback_local_album(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    album = tmp_path / "album"
    album.mkdir()
    handler = MockStudioHandler(
        trips_dir,
        json_body={"albumPath": str(album), "title": "测试"},
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess"):
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
        ):
            handle_import(handler)

    assert handler.response is not None
    status, body = handler.response
    assert status == 202
    assert body["ok"] is True
    assert body.get("jobId")


def test_handle_reveal_denies_path_outside_trip(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-reveal", trips_dir)
    outside = tmp_path / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    handler = MockStudioHandler(
        trips_dir,
        json_body={"tripId": "demo-reveal", "relPath": "../../../secret.txt"},
    )
    handle_reveal(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_STUDIO_REVEAL_DENIED"


def test_handle_status_requires_job_id(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handler.path = "/__travelogue/status"
    handle_status(handler)
    assert handler.response == (400, {"ok": False, "error": "jobId required"})


def test_handle_cancel_unknown_job(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", json_body={"jobId": "missing"})
    handle_cancel(handler)
    assert handler.response == (404, {"ok": False, "error": "job not found"})


def test_handle_cancel_existing_job(tmp_path: Path) -> None:
    job = get_job_store().create_import_job()
    assert job is not None
    handler = MockStudioHandler(tmp_path / "trips", json_body={"jobId": job.job_id})
    handle_cancel(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["status"] == "cancelled"


def test_handle_longshot_requires_trip_id(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.export_handlers import handle_longshot

    handler = MockStudioHandler(tmp_path / "trips", json_body={"scale": 1})
    handle_longshot(handler)
    assert handler.response == (400, {"ok": False, "error": "tripId required"})


def test_read_import_request_json_body(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.import_handlers import read_import_request

    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": "/tmp/album", "title": "JSON导入"},
    )
    payload, upload_dir = read_import_request(handler)
    assert payload["albumPath"] == "/tmp/album"
    assert payload["title"] == "JSON导入"
    assert upload_dir is None


def test_sample_album_preview_thumbs(tmp_path: Path) -> None:
    from tests.studio_test_helpers import make_test_album

    album = make_test_album(tmp_path, n=8)
    thumbs, count = sample_album_preview_thumbs(album)
    assert count == 8
    assert len(thumbs) == 4
    assert all(t.startswith("data:image/jpeg;base64,") for t in thumbs)


def test_handle_album_preview_success(tmp_path: Path) -> None:
    from tests.studio_test_helpers import make_test_album

    trips_dir = tmp_path / "trips"
    album = make_test_album(tmp_path, n=5)
    handler = MockStudioHandler(trips_dir, json_body={"albumPath": str(album)})
    handle_album_preview(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["photoCount"] == 5
    assert len(body["thumbs"]) == 4


def test_handle_album_preview_denies_untrusted_album(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    outside = tmp_path / "outside-album"
    outside.mkdir()
    handler = MockStudioHandler(
        trips_dir,
        json_body={"albumPath": str(outside)},
        studio_host="0.0.0.0",
        studio_allow_lan=True,
    )
    handle_album_preview(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_STUDIO_ALBUM_DENIED"
