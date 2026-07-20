"""LTN Wave E / R-E2 · weekly dashboard metrics (offline, no re-curate)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from travelogue.layout_contract.chapter_items import resolve_longshot_mode
from travelogue.layout_contract.mosaic_track import resolve_mosaic_track, track_params_for
from travelogue.layout_contract.planner_state import (
    ScreenLayoutPlannerState,
    is_dense_collage_pattern,
)
from travelogue.layout_contract.rhythm import dense_collage_limits_for_trip
from travelogue.layout_engine.mosaic.metrics import (
    mcs_unified_exposure_rate,
    mosaic5_exposure_rate,
)

_STACK3_PATTERNS = frozenset(
    {
        "screen-portrait-3",
        "screen-portrait-3-editorial",
        "screen-landscape-3",
        "screen-portrait-1-landscape-2",
    }
)


def _winner_plan_logs(mosaic_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lg in mosaic_logs:
        if not isinstance(lg, dict):
            continue
        if "isWinnerPlan" in lg and not lg.get("isWinnerPlan"):
            continue
        out.append(lg)
    return out


def _screen_asset_ids(screen: dict[str, Any]) -> set[str]:
    return {
        str(sl.get("assetId"))
        for sl in (screen.get("slots") or [])
        if isinstance(sl, dict) and sl.get("assetId")
    }


def _iter_screens(chapters: list[dict[str, Any]]):
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        for sc in ch.get("screens") or []:
            if isinstance(sc, dict):
                yield ch, sc


def hero_mosaic_count(chapters: list[dict[str, Any]]) -> int:
    """§12 · screens with main/hero role on a dense/mosaic pattern."""
    n = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if not pid or "breath" in pid:
            continue
        dense = "mosaic" in pid or is_dense_collage_pattern(pid)
        if not dense:
            continue
        has_main = any(
            isinstance(sl, dict) and sl.get("role") in ("main", "hero")
            for sl in (sc.get("slots") or [])
        )
        if has_main or ScreenLayoutPlannerState.pattern_has_main_role(pid):
            n += 1
    return n


def window_size_distribution(mosaic_logs: list[dict[str, Any]]) -> dict[str, int]:
    dist: Counter[str] = Counter()
    for lg in _winner_plan_logs(mosaic_logs):
        size = lg.get("windowSize")
        if size is None:
            continue
        dist[str(int(size))] += 1
    return dict(sorted(dist.items(), key=lambda kv: int(kv[0])))


def studio_reject_explain_rate(mosaic_logs: list[dict[str, Any]]) -> float | None:
    """Share of interesting winner-plan decisions that carry Top3 rejects."""
    interesting = 0
    explained = 0
    for lg in _winner_plan_logs(mosaic_logs):
        has_decision = bool(lg.get("fallbackUsed") or lg.get("fallbackReason") or lg.get("winnerPatternId"))
        if not has_decision:
            continue
        interesting += 1
        rejected = lg.get("rejectedTemplates") or lg.get("geometryRejectedTemplates") or []
        if isinstance(rejected, list) and rejected:
            explained += 1
    if interesting == 0:
        return None
    return round(explained / interesting, 6)


def dense_quota_utilization(
    chapters: list[dict[str, Any]],
    *,
    trip_photo_total: int,
    dense_max_cap: int | None = None,
) -> float | None:
    """used dense screens / P21(+track) max."""
    _lo, hi = dense_collage_limits_for_trip(max(0, int(trip_photo_total)))
    if dense_max_cap is not None:
        hi = min(hi, max(0, int(dense_max_cap)))
    if hi <= 0:
        return None
    used = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if is_dense_collage_pattern(pid) or "mosaic" in pid:
            used += 1
    return round(min(1.0, used / hi), 6)


def preserve_group_honor_rate(chapters: list[dict[str, Any]]) -> float | None:
    """Among mosaic screens that should preserve, share that do not flatten."""
    eligible = 0
    honored = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if "mosaic" not in pid:
            continue
        slots = [s for s in (sc.get("slots") or []) if isinstance(s, dict) and s.get("assetId")]
        if len(slots) < 2:
            continue
        eligible += 1
        mode = resolve_longshot_mode(dict(sc))
        if mode != "flatten":
            honored += 1
    if eligible == 0:
        return None
    return round(honored / eligible, 6)


def _window_asset_ids(lg: dict[str, Any]) -> set[str]:
    for key in ("assetIds", "windowAssetIds", "orderedAssetIds"):
        raw = lg.get(key)
        if isinstance(raw, list) and raw:
            return {str(x) for x in raw if x}
    return set()


def portrait3_after_failed_mcs5_rate(
    chapters: list[dict[str, Any]],
    mosaic_logs: list[dict[str, Any]],
) -> float | None:
    """MVP proxy for AC-C-01 (strict口径 needs offline isolation replay)."""
    failed = [
        lg
        for lg in _winner_plan_logs(mosaic_logs)
        if int(lg.get("windowSize") or 0) >= 4 and lg.get("fallbackUsed")
    ]
    if not failed:
        return None

    screens = [sc for _ch, sc in _iter_screens(chapters)]
    hits = 0
    for lg in failed:
        win_aids = _window_asset_ids(lg)
        seg = lg.get("segmentId")
        for sc in screens:
            pid = str(sc.get("patternId") or "")
            if pid not in _STACK3_PATTERNS:
                continue
            sc_aids = _screen_asset_ids(sc)
            if win_aids:
                if win_aids & sc_aids:
                    hits += 1
                    break
                continue
            if seg and sc.get("segmentId") == seg:
                hits += 1
                break
    return round(hits / len(failed), 6)


def cross_scene_window_rate(mosaic_logs: list[dict[str, Any]]) -> float | None:
    """Proxy: windows that record crossSegment/crossScene flags. Else None (C4构造)."""
    flagged = 0
    total = 0
    for lg in _winner_plan_logs(mosaic_logs):
        if lg.get("windowSize") is None:
            continue
        total += 1
        if lg.get("crossSegment") or lg.get("crossScene") or lg.get("cross_scene"):
            flagged += 1
    if total == 0:
        return None
    return round(flagged / total, 6)


def compute_ltn_weekly_metrics(
    trip: dict[str, Any] | None = None,
    *,
    chapters: list[dict[str, Any]] | None = None,
    mosaic_logs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate LTN weekly dashboard metrics for one trip (or chapter slice)."""
    trip = trip or {}
    chapters = list(chapters if chapters is not None else (trip.get("chapters") or []))
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    logs = list(
        mosaic_logs
        if mosaic_logs is not None
        else (curation.get("mosaicDecisionLog") or [])
    )
    assets = trip.get("assets") if isinstance(trip.get("assets"), list) else []
    kept = len(assets) if assets else sum(
        len(_screen_asset_ids(sc)) for _ch, sc in _iter_screens(chapters)
    )
    intent_mode = str((trip.get("intent") or {}).get("mode") or "")
    track = resolve_mosaic_track(kept_count=kept, intent_mode=intent_mode)
    params = track_params_for(track)

    out: dict[str, Any] = {
        "mosaicTrack": track,
        "keptCount": kept,
        "windowSizeDistribution": window_size_distribution(logs),
        "mosaic5ExposureRate": mosaic5_exposure_rate(chapters),
        "mcsUnifiedExposureRate": mcs_unified_exposure_rate(chapters),
        "heroMosaicCount": hero_mosaic_count(chapters),
        "studioRejectExplainRate": studio_reject_explain_rate(logs),
        "denseQuotaUtilization": dense_quota_utilization(
            chapters,
            trip_photo_total=kept,
            dense_max_cap=params.dense_collage_max_cap,
        ),
        "preserveGroupHonorRate": preserve_group_honor_rate(chapters),
        "portrait3AfterFailedMcs5Rate": portrait3_after_failed_mcs5_rate(chapters, logs),
        "crossSceneWindowRate": cross_scene_window_rate(logs),
        "mosaicWindowDecisions": len(_winner_plan_logs(logs)),
        "notes": [],
    }
    if out["crossSceneWindowRate"] is None and not logs:
        out["notes"].append("no mosaicDecisionLog; log-dependent rates skipped/null")
    elif out["crossSceneWindowRate"] is None:
        out["notes"].append("crossSceneWindowRate null — C4 constructs windows within segments")
    if out["portrait3AfterFailedMcs5Rate"] is not None:
        out["notes"].append(
            "portrait3AfterFailedMcs5Rate is MVP proxy; see AC-C-01 for strict口径"
        )
    # Drop empty notes noise when nothing to say
    if not out["notes"]:
        out.pop("notes")
    return out
