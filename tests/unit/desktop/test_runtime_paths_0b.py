"""Unit tests for desktop installer path contract (M-INS-0b / ADR-018)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import travelogue.paths as paths


@pytest.fixture(autouse=True)
def _clear_path_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_USER_DATA", raising=False)
    monkeypatch.delenv("TRAVELOGUE_TRIPS_DIR", raising=False)


def test_dev_mode_trips_under_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert paths.is_portable_mode() is False
    assert paths.user_data_dir() == paths.ROOT
    assert paths.default_trips_dir() == paths.ROOT / "trips"


def test_frozen_portable_uses_exe_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exe = tmp_path / "TravelogueStudio.exe"
    exe.write_bytes(b"")
    (tmp_path / "portable.flag").write_text("portable\n", encoding="utf-8")
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "exe_dir", lambda: tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert paths.is_portable_mode() is True
    assert paths.user_data_dir() == tmp_path
    assert paths.default_trips_dir() == tmp_path / "trips"
    assert paths.logs_dir() == tmp_path / "logs"


def test_frozen_install_uses_localappdata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exe_home = tmp_path / "Programs" / "Travelogue"
    exe_home.mkdir(parents=True)
    local = tmp_path / "LocalAppData"
    local.mkdir()
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "exe_dir", lambda: exe_home)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert paths.is_portable_mode() is False
    assert paths.user_data_dir() == (local / "Travelogue").resolve()
    assert paths.default_trips_dir() == paths.user_data_dir() / "trips"


def test_env_overrides_paths_not_portable_bit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exe_home = tmp_path / "app"
    exe_home.mkdir()
    (exe_home / "portable.flag").write_text("x\n", encoding="utf-8")
    external = tmp_path / "external-data"
    external.mkdir()
    monkeypatch.setenv("TRAVELOGUE_USER_DATA", str(external))
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "exe_dir", lambda: exe_home)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert paths.is_portable_mode() is True  # flag still wins for mode bit
    assert paths.user_data_dir() == external.resolve()
    assert paths.default_trips_dir() == external.resolve() / "trips"


def test_ensure_user_data_layout_writes_marker_and_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "is_portable_mode", lambda: True)
    monkeypatch.setattr(paths, "exe_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "user_data_dir", lambda: tmp_path)
    example = tmp_path / "config.yaml.example"
    example.write_text("trips_dir: ./trips\n", encoding="utf-8")
    monkeypatch.setattr(paths, "bundled_config_example", lambda: example)

    root = paths.ensure_user_data_layout()
    assert root == tmp_path
    assert (tmp_path / "trips").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / paths.OWNERSHIP_MARKER_NAME).is_file()
    assert (tmp_path / "config.yaml").is_file()
    assert "trips_dir" in (tmp_path / "config.yaml").read_text(encoding="utf-8")


def test_picker_command_frozen_uses_argv_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.desktop import folder_picker_service as fps

    monkeypatch.setattr(fps, "is_frozen", lambda: True)
    monkeypatch.setattr(sys, "executable", r"C:\App\TravelogueStudio.exe")
    out = Path(r"C:\Temp\out.json")
    cmd = fps._picker_command("选择照片文件夹", out_path=out)
    assert cmd[0].endswith("TravelogueStudio.exe")
    assert cmd[1] == "--pick-folder-worker"
    assert cmd[2].startswith("--out=")
    assert cmd[3] == "选择照片文件夹"


def test_pick_folder_worker_out_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.desktop import pick_folder_worker as worker

    monkeypatch.setattr(worker, "pick_folder", lambda title: tmp_path / "相册")
    out = tmp_path / "result.json"
    worker.main([f"--out={out}", "标题"])
    data = out.read_text(encoding="utf-8")
    assert "相册" in data


def test_parse_worker_payload_tolerates_stdout_warning() -> None:
    from travelogue.desktop.folder_picker_service import _parse_worker_payload

    polluted = (
        '[WARNING] Ignore caches that are heterogeneous\n'
        '{"path": "D:\\\\Photos\\\\2025东澳岛"}'
    )
    data = _parse_worker_payload(polluted)
    assert data is not None
    assert data["path"].endswith("东澳岛")


def test_request_folder_reads_out_file_not_polluted_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: native WARNING on stdout must not break pick-folder API."""
    import json
    import subprocess

    from travelogue.desktop import folder_picker_service as fps

    album = tmp_path / "相册"
    album.mkdir()

    def fake_run(cmd, **kwargs):  # noqa: ANN001
        out = None
        for arg in cmd:
            if isinstance(arg, str) and arg.startswith("--out="):
                out = Path(arg.split("=", 1)[1])
                break
        assert out is not None, "dev pick-folder must pass --out"
        out.write_text(
            json.dumps({"path": str(album)}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout='[WARNING] Ignore caches that are heterogeneous\n{"path": null}\n',
            stderr="",
        )

    monkeypatch.setattr(fps.subprocess, "run", fake_run)
    result = fps.request_folder(title="t")
    assert result.error is None
    assert result.cancelled is False
    assert result.path == album
