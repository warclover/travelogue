"""Single-screen replan API (Benchmark P1 · studio / offline edits)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.curation.mosaic.candidates import generate_window_candidates
from travelogue.curation.mosaic.legacy import build_legacy_screen
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState

ReplanStrategy = Literal["alt_topk", "legacy"]


class ReplanError(ValueError):
    """Invalid replan request (missing screen, breath pause, missing context)."""


def _find_screen(chapters: list[dict], screen_id: str) -> tuple[int, int, dict, dict]:
    for ch_i, ch in enumerate(chapters):
        for sc_i, sc in enumerate(ch.get("screens") or []):
            if sc.get("screenId") == screen_id:
                return ch_i, sc_i, ch, sc
    raise ReplanError(f"screen not found: {screen_id!r}")


def _ordered_asset_ids(screen: dict) -> list[str]:
    slots = screen.get("slots") or []
    return [str(sl["assetId"]) for sl in slots if sl.get("assetId")]


def _pick_alt_topk(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    current_pattern_id: str,
    top_k: int,
    layout_state: ScreenLayoutPlannerState | None,
    trip_photo_total: int,
    burst_seconds: float,
    median_sharp: float | None,
) -> tuple[dict | None, int, str]:
    candidates = generate_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    if not candidates:
        return None, 0, "no_candidates"

    scored: list[tuple[Any, float, list[str]]] = []
    for cand in candidates:
        sr = score_candidate(
            cand.screen,
            aspects=aspects,
            assets_by_id=assets_map,
            cfg=cfg,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            burst_seconds=burst_seconds,
        )
        scored.append((cand, sr.total, sr.reason_codes))
    scored.sort(key=lambda t: (-t[1], t[0].pattern_id))

    rank = 0
    for cand, _score, _reasons in scored[: max(1, top_k)]:
        rank += 1
        if cand.pattern_id != current_pattern_id:
            return cand.screen, rank, "alt_topk"
    if scored:
        return scored[0][0].screen, 1, "unchanged_best_only"
    return None, 0, "no_candidates"


def replan_screen(
    chapters: list[dict],
    screen_id: str,
    *,
    strategy: ReplanStrategy = "alt_topk",
    top_k: int = 3,
    aspects: dict[str, AspectKind] | None = None,
    assets_map: dict[str, dict] | None = None,
    cfg: MosaicConfig | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
) -> dict[str, Any]:
    """
    Replace one screen in ``chapters`` (in place) using MCS alternates or legacy rules.

    Requires ``aspects`` and ``assets_map`` for scoring / candidate generation.
    """
    if top_k < 1:
        raise ReplanError("top_k must be >= 1")
    if aspects is None or assets_map is None:
        raise ReplanError("aspects and assets_map are required for replan_screen")

    ch_i, sc_i, _ch, screen = _find_screen(chapters, screen_id)
    pattern_id = str(screen.get("patternId") or "")
    if pattern_id == BREATH_PATTERN or not screen.get("slots"):
        raise ReplanError(f"screen {screen_id!r} has no replannable photo slots")

    asset_ids = _ordered_asset_ids(screen)
    if len(asset_ids) < 3:
        raise ReplanError(
            f"screen {screen_id!r} has {len(asset_ids)} assets; replan supports 3–9 slot windows"
        )

    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    mosaic_cfg = cfg or get_effective_mosaic_config()
    window_size = len(asset_ids)
    previous = dict(screen)

    if strategy == "legacy":
        new_screen = build_legacy_screen(
            asset_ids,
            window_size,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
            trip_total=trip_photo_total,
        )
        reason = "legacy" if new_screen else "legacy_failed"
        rank = 0
    else:
        new_screen, rank, reason = _pick_alt_topk(
            asset_ids,
            aspects,
            assets_map,
            cfg=mosaic_cfg,
            current_pattern_id=pattern_id,
            top_k=top_k,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )

    if not new_screen:
        return {
            "screenId": screen_id,
            "strategy": strategy,
            "applied": False,
            "reason": reason,
            "previousPatternId": pattern_id,
            "rank": rank,
        }

    new_screen = dict(new_screen)
    new_screen["screenId"] = screen_id
    chapters[ch_i]["screens"][sc_i] = new_screen

    return {
        "screenId": screen_id,
        "strategy": strategy,
        "applied": True,
        "reason": reason,
        "previousPatternId": pattern_id,
        "newPatternId": new_screen.get("patternId"),
        "rank": rank,
        "screen": new_screen,
        "previousScreen": previous,
    }
