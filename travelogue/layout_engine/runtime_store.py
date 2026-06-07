"""LSE runtime overrides store (W2 · config_governance approved patches)."""

from __future__ import annotations

import copy
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT

_LOCK = threading.Lock()
_CACHE: tuple[float, dict[str, Any]] | None = None

LSE_PATCH_KEYS = frozenset(
    {
        "layout_strategy_weights",
        "layout_strategy_penalties",
        "layout_strategy_rollout",
        "layout_strategy_overrides_disable_stages",
        "layout_strategy_overrides_disable_patterns",
    }
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def resolve_store_path(path: str | Path | None = None) -> Path:
    p = Path(path or "data/lse_runtime.json")
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    return p


def _empty() -> dict[str, Any]:
    return {
        "revision": 0,
        "overrides": {"disable_stages": [], "disable_patterns": []},
        "scoring_profiles": {},
        "rollout": {},
        "configHistory": [],
    }


def _load_unlocked(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(data, dict):
        return _empty()
    data.setdefault("revision", 0)
    data.setdefault("overrides", {"disable_stages": [], "disable_patterns": []})
    data.setdefault("scoring_profiles", {})
    data.setdefault("rollout", {})
    data.setdefault("configHistory", [])
    return data


def _save_unlocked(path: Path, data: dict[str, Any]) -> None:
    global _CACHE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    _CACHE = None


def load_lse_runtime(path: str | Path | None = None) -> dict[str, Any]:
    store = resolve_store_path(path)
    global _CACHE
    try:
        mtime = store.stat().st_mtime if store.is_file() else 0.0
    except OSError:
        mtime = 0.0
    if _CACHE is not None and _CACHE[0] == mtime:
        return dict(_CACHE[1])
    with _LOCK:
        data = _load_unlocked(store)
    _CACHE = (mtime, data)
    return dict(data)


def _validate_weights(weights: Any) -> dict[str, float]:
    if not isinstance(weights, dict):
        raise ValueError("E_LSE_WEIGHTS_INVALID")
    out: dict[str, float] = {}
    for k, v in weights.items():
        fv = float(v)
        if fv < 0 or fv > 1:
            raise ValueError("E_LSE_WEIGHT_OUT_OF_RANGE")
        out[str(k)] = fv
    total = sum(out.values())
    if total > 0 and abs(total - 1.0) > 0.05:
        raise ValueError("E_LSE_WEIGHTS_NOT_NORMALIZED")
    return out


def _validate_penalties(penalties: Any) -> dict[str, float]:
    if not isinstance(penalties, dict):
        raise ValueError("E_LSE_PENALTIES_INVALID")
    out: dict[str, float] = {}
    for k, v in penalties.items():
        fv = float(v)
        if fv < 0 or fv > 1:
            raise ValueError("E_LSE_PENALTY_OUT_OF_RANGE")
        out[str(k)] = fv
    return out


def merge_approved_patch(
    patch: dict[str, Any],
    *,
    store_path: str | Path | None = None,
    change_id: str = "",
) -> dict[str, Any]:
    """Apply approved layout_strategy_* patch keys to lse_runtime.json."""
    path = resolve_store_path(store_path)
    with _LOCK:
        data = _load_unlocked(path)
        before = {
            "overrides": copy.deepcopy(data.get("overrides") or {}),
            "scoring_profiles": copy.deepcopy(data.get("scoring_profiles") or {}),
            "rollout": copy.deepcopy(data.get("rollout") or {}),
        }
        overrides = data.setdefault("overrides", {"disable_stages": [], "disable_patterns": []})

        if "layout_strategy_overrides_disable_stages" in patch:
            stages = patch["layout_strategy_overrides_disable_stages"]
            if not isinstance(stages, list):
                raise ValueError("E_LSE_DISABLE_STAGES_INVALID")
            overrides["disable_stages"] = [str(s) for s in stages if s]

        if "layout_strategy_overrides_disable_patterns" in patch:
            patterns = patch["layout_strategy_overrides_disable_patterns"]
            if not isinstance(patterns, list):
                raise ValueError("E_LSE_DISABLE_PATTERNS_INVALID")
            overrides["disable_patterns"] = [str(p) for p in patterns if p]

        if "layout_strategy_weights" in patch:
            profile_id = str(patch.get("profileId") or "default")
            weights = _validate_weights(patch["layout_strategy_weights"])
            profiles = data.setdefault("scoring_profiles", {})
            prof = profiles.setdefault(profile_id, {})
            prof["weights"] = weights

        if "layout_strategy_penalties" in patch:
            profile_id = str(patch.get("profileId") or "default")
            penalties = _validate_penalties(patch["layout_strategy_penalties"])
            profiles = data.setdefault("scoring_profiles", {})
            prof = profiles.setdefault(profile_id, {})
            prof["penalties"] = penalties

        if "layout_strategy_rollout" in patch:
            rollout = patch["layout_strategy_rollout"]
            if not isinstance(rollout, dict):
                raise ValueError("E_LSE_ROLLOUT_INVALID")
            data["rollout"] = dict(rollout)

        data.setdefault("configHistory", []).append(
            {
                "at": _utc_now(),
                "changeId": change_id,
                "patch": {k: patch[k] for k in patch if k in LSE_PATCH_KEYS or k == "profileId"},
                "before": before,
            }
        )
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(path, data)
        return data


def effective_disable_stages(
    cfg: Any,
    *,
    runtime_path: str | None = None,
) -> tuple[str, ...]:
    base = tuple(cfg.layout.strategy_engine.overrides.disable_stages)
    rt = load_lse_runtime(runtime_path or cfg.layout.strategy_engine.runtime_store)
    extra = rt.get("overrides", {}).get("disable_stages") or []
    merged = tuple(dict.fromkeys([*base, *(str(x) for x in extra)]))
    return merged


def effective_disable_patterns(
    cfg: Any,
    *,
    runtime_path: str | None = None,
) -> tuple[str, ...]:
    rt = load_lse_runtime(runtime_path or cfg.layout.strategy_engine.runtime_store)
    extra = rt.get("overrides", {}).get("disable_patterns") or []
    return tuple(str(x) for x in extra if x)


def rollback_lse_runtime(
    *,
    steps: int = 1,
    store_path: str | Path | None = None,
) -> dict[str, Any]:
    """Restore LSE runtime from configHistory snapshots (W2 · AC-P17-14)."""
    if steps < 1:
        raise ValueError("E_LSE_ROLLBACK_STEPS_INVALID")
    path = resolve_store_path(store_path)
    with _LOCK:
        data = _load_unlocked(path)
        history = list(data.get("configHistory") or [])
        if len(history) < steps:
            raise ValueError("E_LSE_ROLLBACK_EMPTY")
        target = history[-steps]
        before = target.get("before")
        if not isinstance(before, dict):
            raise ValueError("E_LSE_ROLLBACK_NO_SNAPSHOT")
        data["overrides"] = copy.deepcopy(before.get("overrides") or {})
        data["scoring_profiles"] = copy.deepcopy(before.get("scoring_profiles") or {})
        data["rollout"] = copy.deepcopy(before.get("rollout") or {})
        data["configHistory"] = history[:-steps]
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(path, data)
        return data


def runtime_scoring_overlay(
    cfg: Any,
    *,
    profile_id: str = "default",
    runtime_path: str | None = None,
) -> dict[str, Any]:
    """Approved L2 weights/penalties overlay for a scoring profile."""
    rt = load_lse_runtime(runtime_path or cfg.layout.strategy_engine.runtime_store)
    prof = (rt.get("scoring_profiles") or {}).get(profile_id) or {}
    return {
        "weights": dict(prof.get("weights") or {}),
        "penalties": dict(prof.get("penalties") or {}),
        "rollout": dict(rt.get("rollout") or {}),
    }
