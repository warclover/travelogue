"""M-INS-0c · single-instance helpers (non-mutex paths)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.desktop import single_instance as si


def test_instance_state_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(si, "user_data_dir", lambda: tmp_path)
    state = si.InstanceState(
        pid=12345,
        port=8766,
        url="http://127.0.0.1:8766/",
        host="127.0.0.1",
        started_at=1.0,
    )
    path = si.write_instance_state(state)
    assert path.is_file()
    loaded = si.read_instance_state()
    assert loaded is not None
    assert loaded.port == 8766
    assert loaded.url.endswith(":8766/")
    si.clear_instance_state()
    assert si.read_instance_state() is None


def test_open_existing_clears_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(si, "user_data_dir", lambda: tmp_path)
    monkeypatch.setattr(si, "_pid_alive", lambda _pid: False)
    (tmp_path / si.STATE_FILENAME).write_text(
        json.dumps(
            {
                "pid": 999999,
                "port": 8766,
                "url": "http://127.0.0.1:8766/",
                "host": "127.0.0.1",
                "startedAt": 1,
            }
        ),
        encoding="utf-8",
    )
    assert si.open_existing_instance_or_stale() is None
    assert not (tmp_path / si.STATE_FILENAME).is_file()


def test_try_acquire_non_frozen_always_owned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(si, "is_frozen", lambda: False)
    handle = si.try_acquire_single_instance()
    assert handle.owned is True
