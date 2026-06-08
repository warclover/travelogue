"""AC-P17-13 · weightsHash → scoring profile snapshot persistence."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from travelogue.layout_engine.registry import StrategyPack
from travelogue.paths import ROOT

_LOCK = threading.Lock()
DEFAULT_STORE = ROOT / "data" / "lse_weights_audit.json"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def resolve_audit_path(path: str | Path | None = None) -> Path:
    p = Path(path or DEFAULT_STORE)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    return p


def _empty_store() -> dict[str, Any]:
    return {"schemaVersion": 1, "snapshots": {}}


def load_weights_audit_store(path: str | Path | None = None) -> dict[str, Any]:
    store_path = resolve_audit_path(path)
    if not store_path.is_file():
        return _empty_store()
    try:
        data = json.loads(store_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_store()
    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("schemaVersion", 1)
    data.setdefault("snapshots", {})
    return data


def _profile_snapshot(pack: StrategyPack, profile_id: str = "default") -> dict[str, Any]:
    profiles = pack.raw.get("scoring_profiles") or {}
    profile = profiles.get(profile_id) or {}
    return {
        "weightsHash": pack.weights_hash(profile_id),
        "strategyId": pack.id,
        "strategyVersion": pack.version,
        "algorithmVersion": pack.algorithm_version,
        "contentHash": pack.content_hash,
        "profileId": profile_id,
        "weights": dict(profile.get("weights") or {}),
        "penalties": dict(profile.get("penalties") or {}),
        "recordedAt": _utc_now(),
    }


def record_pack_weights_snapshot(
    pack: StrategyPack,
    *,
    profile_id: str = "default",
    store_path: str | Path | None = None,
) -> dict[str, Any]:
    """Persist weightsHash → profile snapshot (idempotent per hash)."""
    snap = _profile_snapshot(pack, profile_id)
    wh = str(snap["weightsHash"])
    path = resolve_audit_path(store_path)
    with _LOCK:
        data = load_weights_audit_store(path)
        snapshots = data.setdefault("snapshots", {})
        if wh not in snapshots:
            snapshots[wh] = snap
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(path)
    return snap


def lookup_weights_snapshot(
    weights_hash: str,
    *,
    store_path: str | Path | None = None,
) -> dict[str, Any] | None:
    wh = str(weights_hash or "").strip()
    if not wh:
        return None
    data = load_weights_audit_store(store_path)
    snap = (data.get("snapshots") or {}).get(wh)
    return dict(snap) if isinstance(snap, dict) else None
