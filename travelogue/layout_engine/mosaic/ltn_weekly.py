"""LTN Wave E / R-E2 · weekly dashboard metrics (offline, no re-curate)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from travelogue.layout_contract.asymmetric_quota import (
    asymmetric_dense_snapshot,
    dense_opportunity_min_for,
)
from travelogue.layout_contract.chapter_items import (
    resolve_longshot_mode,
    screens_to_longshot_items,
)
from travelogue.layout_contract.mosaic_track import resolve_mosaic_track, track_params_for
from travelogue.layout_contract.planner_state import (
    ScreenLayoutPlannerState,
    is_dense_collage_pattern,
)
from travelogue.layout_contract.rhythm import dense_collage_limits_for_trip
from travelogue.layout_engine.mosaic.ltn_isolation import STACK3_PATTERNS
from travelogue.layout_engine.mosaic.metrics import (
    mcs_unified_exposure_rate,
    mosaic5_exposure_rate,
)

_BURST_WINDOW_LENS = (5, 6)
_NON_LAYOUT_PATTERNS = frozenset({"screen-breath-pause"})


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


def _dense_used_count(chapters: list[dict[str, Any]]) -> int:
    used = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if is_dense_collage_pattern(pid) or "mosaic" in pid:
            used += 1
    return used


def _dense_max_for_trip(
    trip_photo_total: int, *, dense_max_cap: int | None = None
) -> int:
    _lo, hi = dense_collage_limits_for_trip(max(0, int(trip_photo_total)))
    if dense_max_cap is not None:
        hi = min(hi, max(0, int(dense_max_cap)))
    return max(0, int(hi))


def dense_quota_utilization(
    chapters: list[dict[str, Any]],
    *,
    trip_photo_total: int,
    dense_max_cap: int | None = None,
) -> float | None:
    """used dense screens / P21(+track) max."""
    hi = _dense_max_for_trip(trip_photo_total, dense_max_cap=dense_max_cap)
    if hi <= 0:
        return None
    used = _dense_used_count(chapters)
    return round(min(1.0, used / hi), 6)


def dense_opportunity_seen_from_logs(mosaic_logs: list[dict[str, Any]]) -> int:
    """Legal scored windows (E4 opportunity dimension) from decision logs."""
    n = 0
    for lg in _winner_plan_logs(mosaic_logs):
        if int(lg.get("windowSize") or 0) < 4:
            continue
        if lg.get("fallbackReason") == "no_candidates":
            continue
        cc = lg.get("candidatesCount")
        if cc is not None:
            if int(cc) > 0:
                n += 1
            continue
        if lg.get("top3Patterns") or (
            lg.get("winnerPatternId") and not lg.get("fallbackUsed")
        ):
            n += 1
    return n


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
            if pid not in STACK3_PATTERNS:
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


def _aspect_family(kind: str) -> str:
    if kind in ("portrait", "tall"):
        return "portrait"
    if kind in ("landscape", "panorama"):
        return "landscape"
    return "square"


def burst_pass_rate(
    trip: dict[str, Any],
    *,
    burst_seconds: float = 1800.0,
) -> float | None:
    """G-LTN-07 / LRG · 1P+(N-1)L window time-near pass rate."""
    from travelogue.layout_contract.burst import parse_taken_ts, time_near_chain
    from travelogue.layout_contract.orientations import aspect_kind_for_asset

    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    if not assets_map:
        return None
    aspects = {aid: aspect_kind_for_asset(a) for aid, a in assets_map.items()}
    cur = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    ordered = [str(x) for x in (cur.get("displayedAssetIds") or []) if str(x) in assets_map]
    if not ordered:
        ordered = sorted(assets_map, key=lambda i: parse_taken_ts(assets_map[i]) or 0.0)
    geometry_total = 0
    pass_total = 0
    for window_len in _BURST_WINDOW_LENS:
        for i in range(max(0, len(ordered) - window_len + 1)):
            window = ordered[i : i + window_len]
            kinds = [_aspect_family(str(aspects.get(aid, "square"))) for aid in window]
            n_p = sum(1 for k in kinds if k == "portrait")
            n_l = sum(1 for k in kinds if k == "landscape")
            if n_p != 1 or n_l != window_len - 1:
                continue
            geometry_total += 1
            if time_near_chain(window, assets_map, burst_seconds=burst_seconds):
                pass_total += 1
    if geometry_total == 0:
        return None
    return round(pass_total / geometry_total, 6)


def content_screen_count(chapters: list[dict[str, Any]]) -> int:
    n = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if pid in _NON_LAYOUT_PATTERNS or "breath" in pid:
            continue
        n += 1
    return n


def screen_count_parity(
    chapters: list[dict[str, Any]],
    *,
    html_layout_screen_count: int | None = None,
) -> dict[str, Any]:
    """trip content screens vs optional HTML layout-screen count."""
    trip_n = content_screen_count(chapters)
    if html_layout_screen_count is None:
        return {
            "screenCount": trip_n,
            "htmlLayoutScreenCount": None,
            "screenCountParityOk": None,
        }
    return {
        "screenCount": trip_n,
        "htmlLayoutScreenCount": int(html_layout_screen_count),
        "screenCountParityOk": trip_n == int(html_layout_screen_count),
    }


def scroll_longshot_slot_conservation_rate(
    chapters: list[dict[str, Any]],
) -> float | None:
    """Share of screens whose longshot view conserves slot assets (G-LTN-07)."""
    eligible = 0
    ok_n = 0
    for _ch, sc in _iter_screens(chapters):
        pid = str(sc.get("patternId") or "")
        if not pid or "breath" in pid:
            continue
        slots = [
            str(sl.get("assetId"))
            for sl in (sc.get("slots") or [])
            if isinstance(sl, dict) and sl.get("assetId")
        ]
        if not slots:
            continue
        eligible += 1
        mode = resolve_longshot_mode(dict(sc))
        items = screens_to_longshot_items({"screens": [sc]})
        if mode == "flatten":
            item_aids = [
                str(it.get("assetId"))
                for it in items
                if isinstance(it, dict) and it.get("assetId")
            ]
            if item_aids == slots:
                ok_n += 1
        elif mode == "preserve_stack":
            if (
                len(items) == 1
                and list(items[0].get("assetIds") or []) == slots
            ):
                ok_n += 1
        elif mode == "representative_badge":
            if len(items) == 1 and items[0].get("assetId") in slots:
                ok_n += 1
    if eligible == 0:
        return None
    return round(ok_n / eligible, 6)


def compute_ltn_weekly_metrics(
    trip: dict[str, Any] | None = None,
    *,
    chapters: list[dict[str, Any]] | None = None,
    mosaic_logs: list[dict[str, Any]] | None = None,
    html_layout_screen_count: int | None = None,
    burst_seconds: float = 1800.0,
    include_ac_c01_strict: bool = False,
    ac_c01_baseline_rate: float | None = None,
) -> dict[str, Any]:
    """Aggregate LTN weekly dashboard metrics for one trip (or chapter slice).

    ``include_ac_c01_strict`` is opt-in: isolation replay is O(n×sizes) and
    expensive on archive trips.
    """
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
    dense_max = _dense_max_for_trip(kept, dense_max_cap=params.dense_collage_max_cap)
    dense_used = _dense_used_count(chapters)
    opp_min = dense_opportunity_min_for(dense_max=dense_max, track=track)
    opp_seen = dense_opportunity_seen_from_logs(logs)
    asym = asymmetric_dense_snapshot(
        dense_max=dense_max,
        dense_used=dense_used,
        opportunity_min=opp_min,
        opportunity_seen=opp_seen,
    )
    parity = screen_count_parity(
        chapters, html_layout_screen_count=html_layout_screen_count
    )

    out: dict[str, Any] = {
        "mosaicTrack": track,
        "keptCount": kept,
        "windowSizeDistribution": window_size_distribution(logs),
        "mosaic5ExposureRate": mosaic5_exposure_rate(chapters),
        "mcsUnifiedExposureRate": mcs_unified_exposure_rate(chapters),
        "heroMosaicCount": hero_mosaic_count(chapters),
        "studioRejectExplainRate": studio_reject_explain_rate(logs),
        "denseQuotaUtilization": asym["denseQuotaUtilization"],
        "denseOpportunityMin": asym["denseOpportunityMin"],
        "denseOpportunitySeen": asym["denseOpportunitySeen"],
        "denseOpportunityFillRate": asym["denseOpportunityFillRate"],
        "denseForcedEmit": False,
        "asymmetricQuota": True,
        "preserveGroupHonorRate": preserve_group_honor_rate(chapters),
        "portrait3AfterFailedMcs5Rate": portrait3_after_failed_mcs5_rate(chapters, logs),
        "crossSceneWindowRate": cross_scene_window_rate(logs),
        "mosaicWindowDecisions": len(_winner_plan_logs(logs)),
        "burstPassRate": burst_pass_rate(trip, burst_seconds=burst_seconds),
        "screenCount": parity["screenCount"],
        "htmlLayoutScreenCount": parity["htmlLayoutScreenCount"],
        "screenCountParityOk": parity["screenCountParityOk"],
        "scrollLongshotSlotConservationRate": scroll_longshot_slot_conservation_rate(
            chapters
        ),
        "notes": [],
    }
    if include_ac_c01_strict and assets and chapters:
        try:
            from travelogue.layout_engine.mosaic.ltn_isolation import (
                compute_ac_c01_on_trip,
            )

            c01 = compute_ac_c01_on_trip(
                trip, baseline_rate=ac_c01_baseline_rate
            )
            out["portrait3AfterFailedMcs5RateStrict"] = c01.get("rate")
            out["acC01FailedWindowCount"] = c01.get("failedWindowCount")
            out["acC01WithinAbsoluteBand"] = c01.get("withinAbsoluteBand")
            out["acC01Baseline"] = c01.get("baseline")
            out["acC01Ok"] = c01.get("ok")
        except Exception as exc:  # noqa: BLE001 — dashboard must not crash
            out["notes"].append(
                f"acC01Strict skipped: {type(exc).__name__}: {exc}"
            )
            out["portrait3AfterFailedMcs5RateStrict"] = None
    if out["crossSceneWindowRate"] is None and not logs:
        out["notes"].append("no mosaicDecisionLog; log-dependent rates skipped/null")
    elif out["crossSceneWindowRate"] is None:
        out["notes"].append("crossSceneWindowRate null — C4 constructs windows within segments")
    if out["portrait3AfterFailedMcs5Rate"] is not None:
        out["notes"].append(
            "portrait3AfterFailedMcs5Rate is MVP proxy; "
            "prefer --strict-c01 portrait3AfterFailedMcs5RateStrict"
        )
    if not out["notes"]:
        out.pop("notes")
    return out
