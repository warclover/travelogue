"""AC-P17-13 · weightsHash snapshot persistence and lookup."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.layout_engine.adapter import resolve_pack, strategy_trace_meta
from travelogue.layout_engine.query import lookup_weights_by_hash
from travelogue.layout_engine.weights_audit import (
    load_weights_audit_store,
    lookup_weights_snapshot,
    record_pack_weights_snapshot,
)
from dataclasses import replace

from travelogue.config import get_config


def _lse_enabled_cfg():
    cfg = get_config(reload=True)
    se = replace(cfg.layout.strategy_engine, enabled=True)
    return replace(cfg, layout=replace(cfg.layout, strategy_engine=se))


def test_record_and_lookup_weights_snapshot(tmp_path: Path) -> None:
    pack = resolve_pack(_lse_enabled_cfg())
    assert pack is not None
    store = tmp_path / "audit.json"
    snap = record_pack_weights_snapshot(pack, store_path=store)
    wh = snap["weightsHash"]
    assert wh
    loaded = lookup_weights_snapshot(wh, store_path=store)
    assert loaded is not None
    assert loaded["weightsHash"] == wh
    assert loaded["strategyId"] == pack.id
    assert "weights" in loaded

    data = load_weights_audit_store(store)
    assert wh in data["snapshots"]
    record_pack_weights_snapshot(pack, store_path=store)
    assert len(data["snapshots"]) == len(load_weights_audit_store(store)["snapshots"])


def test_lookup_weights_by_hash_query_api(tmp_path: Path) -> None:
    pack = resolve_pack(_lse_enabled_cfg())
    assert pack is not None
    store = tmp_path / "audit.json"
    snap = record_pack_weights_snapshot(pack, store_path=store)
    found = lookup_weights_by_hash(snap["weightsHash"], store_path=store)
    assert found is not None
    assert found["profileId"] == "default"


def test_strategy_trace_meta_records_weights_hash(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "audit.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.weights_audit.DEFAULT_STORE",
        store,
    )
    meta = strategy_trace_meta(_lse_enabled_cfg())
    wh = meta.get("weightsHash")
    assert wh
    assert lookup_weights_snapshot(wh, store_path=store) is not None
