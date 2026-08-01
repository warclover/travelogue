"""TripService load/save."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.services.trip import TripService


def test_save_removes_temp_file_on_replace_failure(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "trip.json"
    trip = {"tripId": "t1", "version": "0.2"}
    svc = TripService()

    def boom_replace(src: str, dst: str) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr("travelogue.services.trip.os.replace", boom_replace)
    with pytest.raises(OSError):
        svc.save(trip, path)
    leftovers = list(tmp_path.glob(".trip-*.json"))
    assert leftovers == []


def test_save_retries_windows_busy_then_succeeds(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "trip.json"
    trip = {"tripId": "t1", "version": "0.2"}
    calls = {"n": 0}
    real_replace = __import__("os").replace

    def flaky_replace(src: str, dst: str) -> None:
        calls["n"] += 1
        if calls["n"] < 3:
            err = PermissionError("denied")
            err.winerror = 5  # type: ignore[attr-defined]
            raise err
        real_replace(src, dst)

    monkeypatch.setattr("travelogue.services.trip.os.replace", flaky_replace)
    monkeypatch.setattr("travelogue.services.trip.time.sleep", lambda _s: None)
    TripService().save(trip, path)
    assert calls["n"] == 3
    assert path.is_file()


def test_save_falls_back_to_inplace_when_replace_stays_busy(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "trip.json"
    path.write_text('{"tripId":"old"}\n', encoding="utf-8")

    def always_busy(src: str, dst: str) -> None:
        err = PermissionError("denied")
        err.winerror = 5  # type: ignore[attr-defined]
        raise err

    monkeypatch.setattr("travelogue.services.trip.os.replace", always_busy)
    monkeypatch.setattr("travelogue.services.trip.time.sleep", lambda _s: None)
    TripService().save({"tripId": "t2", "version": "0.2"}, path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["tripId"] == "t2"
    assert list(tmp_path.glob(".trip-*.json")) == []


def test_replace_raises_when_inplace_also_fails(tmp_path: Path, monkeypatch) -> None:
    from unittest.mock import patch

    from travelogue.services.trip import TripSaveError, _replace_trip_json

    path = tmp_path / "trip.json"
    path.write_text('{"tripId":"old"}\n', encoding="utf-8")
    tmp = tmp_path / ".trip-x.json"
    tmp.write_text('{"tripId":"x"}\n', encoding="utf-8")

    def always_busy(src: str, dst: str) -> None:
        raise PermissionError("denied")

    def boom_open(*_a, **_k):
        raise PermissionError("still locked")

    monkeypatch.setattr("travelogue.services.trip.os.replace", always_busy)
    monkeypatch.setattr("travelogue.services.trip.time.sleep", lambda _s: None)
    with patch("builtins.open", boom_open), pytest.raises(TripSaveError):
        _replace_trip_json(str(tmp), path, payload='{"tripId":"x"}\n')


def test_replace_fallback_failure_preserves_dest_via_bak_and_tmp(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-SFC-13 · in-place fallback dying mid-write must stay recoverable.

    Simulate: os.replace永远 busy → 走截断回退；截断后写入中途失败。既有 dest 被
    截断，但 .bak 保留原文、tmp 保留新内容，两者皆可恢复；错误信息含恢复路径。
    """
    import builtins

    from travelogue.services.trip import TripSaveError

    path = tmp_path / "trip.json"
    original = '{"tripId":"original","meta":{"revision":1}}\n'
    path.write_text(original, encoding="utf-8")

    def always_busy(src: str, dst: str) -> None:
        err = PermissionError("denied")
        err.winerror = 5  # type: ignore[attr-defined]
        raise err

    monkeypatch.setattr("travelogue.services.trip.os.replace", always_busy)
    monkeypatch.setattr("travelogue.services.trip.time.sleep", lambda _s: None)

    real_open = builtins.open

    class _FailingHandle:
        def __init__(self, fh: object) -> None:
            self._fh = fh

        def __enter__(self) -> _FailingHandle:
            return self

        def __exit__(self, *_a: object) -> bool:
            self._fh.close()  # type: ignore[attr-defined]
            return False

        def write(self, *_a: object, **_k: object) -> int:
            raise OSError("disk full mid-write")

        def flush(self) -> None:
            pass

        def fileno(self) -> int:
            return self._fh.fileno()  # type: ignore[attr-defined]

    def failing_open(file, mode="r", *args, **kwargs):  # type: ignore[no-untyped-def]
        # Truncate dest (as real "w" open would) then fail on the actual write.
        if Path(file) == path and "w" in mode and "b" not in mode:
            fh = real_open(file, mode, *args, **kwargs)
            return _FailingHandle(fh)
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)

    with pytest.raises(TripSaveError) as excinfo:
        TripService().save({"tripId": "new", "meta": {"revision": 2}}, path)

    monkeypatch.undo()

    bak = path.with_suffix(path.suffix + ".bak")
    assert bak.is_file(), "backup must survive so dest is recoverable"
    assert bak.read_text(encoding="utf-8") == original

    tmps = list(tmp_path.glob(".trip-*.json"))
    assert tmps, "tmp must be preserved for recovery on fallback failure"
    assert json.loads(tmps[0].read_text(encoding="utf-8"))["tripId"] == "new"

    msg = str(excinfo.value)
    assert ".bak" in msg or "recover" in msg


def test_save_writes_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    trip = {"tripId": "t1", "version": "0.2", "meta": {"title": "测"}}
    TripService().save(trip, path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["tripId"] == "t1"


def test_resolve_trip_json_accepts_trip_dir_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    trip_dir = tmp_path / "trips" / "demo"
    trip_dir.mkdir(parents=True)
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    svc = TripService(root=tmp_path)
    assert svc.resolve_trip_json("demo") == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo") == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo/trip.json") == trip_json.resolve()


def test_resolve_trip_json_from_inside_trip_dir(tmp_path: Path, monkeypatch) -> None:
    """When cwd is trips/demo, trips/demo and . should still resolve."""
    trip_dir = tmp_path / "trips" / "demo"
    trip_dir.mkdir(parents=True)
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    monkeypatch.chdir(trip_dir)
    svc = TripService()
    assert svc.resolve_trip_json("trips/demo") == trip_json.resolve()
    assert svc.resolve_trip_json(".") == trip_json.resolve()
    assert svc.resolve_trip_json("demo") == trip_json.resolve()


def test_app_context_for_trip_json_root(tmp_path: Path, monkeypatch) -> None:
    from travelogue.runtime import app_context_for_trip_json, app_context_for_trips_dir

    monkeypatch.chdir(tmp_path)
    trip_json = tmp_path / "trips" / "demo" / "trip.json"
    trip_json.parent.mkdir(parents=True, exist_ok=True)
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    ctx = app_context_for_trip_json(trip_json)
    assert ctx.trips_root == (tmp_path / "trips").resolve()
    assert ctx.trip_service().root == tmp_path.resolve()
    ctx2 = app_context_for_trips_dir(tmp_path / "trips")
    assert ctx2.trip_service().resolve_trip_json("demo", trips_dir=ctx2.trips_root) == trip_json.resolve()
