"""LSE config governance helpers (W2 · propose / validate)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_engine.runtime_store import LSE_PATCH_KEYS


def normalize_lse_patch(payload: dict[str, Any]) -> dict[str, Any]:
    """Map API body → config_governance patch keys."""
    raw_patch = payload.get("patch") if isinstance(payload.get("patch"), dict) else payload
    if not isinstance(raw_patch, dict):
        raise ValueError("E_LSE_PATCH_INVALID")

    patch: dict[str, Any] = {}
    profile_id = str(payload.get("profileId") or raw_patch.get("profileId") or "default")

    key_map = {
        "weights": "layout_strategy_weights",
        "penalties": "layout_strategy_penalties",
        "rollout": "layout_strategy_rollout",
        "disableStages": "layout_strategy_overrides_disable_stages",
        "disable_stages": "layout_strategy_overrides_disable_stages",
        "disablePatterns": "layout_strategy_overrides_disable_patterns",
        "disable_patterns": "layout_strategy_overrides_disable_patterns",
    }
    for src, dst in key_map.items():
        if src in raw_patch:
            patch[dst] = raw_patch[src]

    for key in LSE_PATCH_KEYS:
        if key in raw_patch:
            patch[key] = raw_patch[key]

    if profile_id and (
        "layout_strategy_weights" in patch or "layout_strategy_penalties" in patch
    ):
        patch["profileId"] = profile_id

    if not patch:
        raise ValueError("E_LSE_PATCH_EMPTY")
    return patch


def validate_lse_patch(patch: dict[str, Any]) -> None:
    """Dry-run validation (raises ValueError with E_* codes)."""
    from travelogue.layout_engine.runtime_store import (
        _validate_penalties,
        _validate_weights,
    )

    if "layout_strategy_weights" in patch:
        _validate_weights(patch["layout_strategy_weights"])
    if "layout_strategy_penalties" in patch:
        _validate_penalties(patch["layout_strategy_penalties"])
    if "layout_strategy_overrides_disable_stages" in patch:
        stages = patch["layout_strategy_overrides_disable_stages"]
        if not isinstance(stages, list):
            raise ValueError("E_LSE_DISABLE_STAGES_INVALID")
    if "layout_strategy_overrides_disable_patterns" in patch:
        patterns = patch["layout_strategy_overrides_disable_patterns"]
        if not isinstance(patterns, list):
            raise ValueError("E_LSE_DISABLE_PATTERNS_INVALID")
    if "layout_strategy_rollout" in patch:
        rollout = patch["layout_strategy_rollout"]
        if not isinstance(rollout, dict):
            raise ValueError("E_LSE_ROLLOUT_INVALID")


def pending_lse_changes(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    pending = list(runtime.get("pendingConfigChanges") or [])
    out: list[dict[str, Any]] = []
    for item in pending:
        patch = item.get("patch") or {}
        if LSE_PATCH_KEYS.intersection(patch.keys()):
            out.append(item)
    return out
