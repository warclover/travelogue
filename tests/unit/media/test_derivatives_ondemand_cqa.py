"""CQA AC-10/10b/11 · on-demand single-flight, busy, atomic persist."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from travelogue.media import derivatives as der
from travelogue.web.studio_jobs import StudioJobStore


@pytest.fixture()
def trip_dir(tmp_path: Path) -> Path:
    d = tmp_path / "my-trip"
    d.mkdir()
    (d / "trip.json").write_text('{"assets":[]}\n', encoding="utf-8")
    return d


def test_is_on_demand_alive_for_trip_id(trip_dir: Path) -> None:
    gate = threading.Event()

    def _run() -> None:
        gate.wait(timeout=5)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    der.register_on_demand_thread_for_tests(trip_dir, t)
    assert der.is_on_demand_alive(trip_dir)
    assert der.is_on_demand_alive_for_trip_id("my-trip")
    assert not der.is_on_demand_alive_for_trip_id("other")
    store = StudioJobStore()
    assert store.is_trip_busy("my-trip")
    gate.set()
    t.join(timeout=2)
    der.stop_or_join_on_demand(trip_dir, timeout=0.1)
    assert not store.is_trip_busy("my-trip")


def test_materialize_coalesces_second_request(
    trip_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        der,
        "get_config",
        lambda: MagicMock(
            pipeline=MagicMock(deferred_derivatives=True),
            ingest=MagicMock(webp_widths=(800, 1600)),
        ),
    )

    started = threading.Event()
    release = threading.Event()
    calls: list[set[str]] = []

    def _ensure(trip, trip_dir, *, app_cfg=None, asset_ids=None, mark_unselected_skipped=True):
        calls.append(set(asset_ids or ()))
        started.set()
        release.wait(timeout=5)
        return der.MaterializeResult()

    monkeypatch.setattr(der, "ensure_derivatives_for_trip", _ensure)
    monkeypatch.setattr(
        der,
        "asset_ids_needing_materialize",
        lambda trip, asset_ids=None, planned_widths=(): sorted(asset_ids or []),
    )

    trip: dict = {"assets": [], "pipeline": {}}
    ids_a = {f"a{i}" for i in range(10)}
    ids_b = {f"b{i}" for i in range(10)}

    r1 = der.materialize_on_demand(
        trip, trip_dir, asset_ids=ids_a, sync_max_assets=1, persist=False
    )
    assert r1.mode == "async"
    assert started.wait(timeout=2)

    r2 = der.materialize_on_demand(
        trip, trip_dir, asset_ids=ids_b, sync_max_assets=1, persist=False
    )
    assert r2.mode == "async"

    with der._on_demand_lock:
        alive = [
            t for t in der._on_demand_threads.values() if t is not None and t.is_alive()
        ]
    assert len(alive) == 1

    release.set()
    alive[0].join(timeout=5)
    union = set().union(*calls) if calls else set()
    assert ids_a.issubset(union)
    assert ids_b.issubset(union)


def test_persist_trip_json_atomic(trip_dir: Path) -> None:
    trip = {"id": "my-trip", "assets": [{"id": "x"}]}
    der._persist_trip_json(trip_dir, trip)
    data = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assert data["assets"][0]["id"] == "x"
    assert list(trip_dir.glob("trip.json.*.tmp")) == []
