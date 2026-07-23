"""QFX · 策展预处理：回填 → 清低清标 → 条件硬丢（D-QFX-08）。

``curate._curate_preflight`` 只编排调用本模块；keep_all 仅跳过硬丢，永不跳过回填/清标。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.domain.photo_keep_mode import should_skip_low_res_exclusion


def clear_low_resolution_marks(trip: dict) -> int:
    """Clear ``excludeReason==low_resolution`` marks and restore layoutEligible."""
    cleared = 0
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("excludeReason") != "low_resolution":
            continue
        asset.pop("excludeReason", None)
        asset["layoutEligible"] = True
        cleared += 1
    curation = trip.get("curation")
    if isinstance(curation, dict):
        curation.pop("excludedLowResAssetIds", None)
    return cleared


def run_curation_preprocess(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    app_cfg: AppConfig | None = None,
    intent: dict | None = None,
) -> str | None:
    """Backfill → clear stale low_res marks → conditional hard drop.

    Returns warning string from hard-drop step (if any).
    """
    from travelogue.curation.asset_quality import (
        apply_layout_eligibility_marks,
        backfill_native_dimensions,
    )

    if trip_dir is not None:
        backfill_native_dimensions(trip, Path(trip_dir))

    clear_low_resolution_marks(trip)

    intent_data: dict[str, Any] | None
    if intent is not None:
        intent_data = intent if isinstance(intent, dict) else None
    else:
        raw = trip.get("intent") if isinstance(trip, dict) else None
        intent_data = raw if isinstance(raw, dict) else None

    if should_skip_low_res_exclusion(intent_data):
        return None
    return apply_layout_eligibility_marks(trip, app_cfg=app_cfg)
