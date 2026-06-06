"""M11 desktop: demo album, bundle paths, folder dialog."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from travelogue.desktop.bundle import bundle_root, default_trips_dir
from travelogue.desktop.demo_album import (
    DEMO_ALBUM_SENTINEL,
    is_demo_album_path,
    resolve_demo_album_dir,
)


def test_demo_album_dir_has_enough_photos() -> None:
    album = resolve_demo_album_dir()
    assert album.is_dir()
    jpgs = list(album.glob("*.jpg"))
    assert len(jpgs) >= 4


def test_is_demo_album_path_sentinel() -> None:
    assert is_demo_album_path(DEMO_ALBUM_SENTINEL)
    assert is_demo_album_path("@demo-album")
    assert not is_demo_album_path(r"D:\Photos\test")


def test_default_trips_dir_under_repo_or_exe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    trips = default_trips_dir()
    assert trips.name == "trips"
    assert (bundle_root() / "templates" / "studio").is_dir()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows IFileDialog only")
def test_pick_folder_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("comtypes")
    from travelogue.desktop import folder_dialog

    class _Dialog:
        def SetOptions(self, *_args, **_kwargs) -> None:
            return None

        def SetTitle(self, *_args, **_kwargs) -> None:
            return None

        def Show(self, *_args, **_kwargs) -> int:
            return 1

    monkeypatch.setattr(folder_dialog, "_pick_folder_ifiledialog", lambda _title: None)
    monkeypatch.setattr(folder_dialog, "_pick_folder_tk", lambda _title: None)
    assert folder_dialog.pick_folder(title="test") is None


@pytest.mark.e2e
def test_studio_import_demo_album(tmp_path: Path) -> None:
    from tests.studio_test_helpers import wait_for_job
    from tests.test_studio_server import (
        _free_port,
        _get_json,
        _post_json,
        _start_studio_server,
    )
    from travelogue.web.studio_jobs import reset_job_store

    reset_job_store()
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {"useDemoAlbum": True, "title": "示例", "place": "示例"},
        )
        assert status == 202, body
        job_id = body["jobId"]

        last = wait_for_job(
            lambda: _get_json(f"{base}/__travelogue/status?jobId={job_id}")[1],
            timeout_sec=180,
            poll_sec=0.05,
        )

        assert last.get("status") == "succeeded", last
        assert (trips_dir / last["tripId"] / "index.html").is_file()
    finally:
        server.shutdown()
        server.server_close()
