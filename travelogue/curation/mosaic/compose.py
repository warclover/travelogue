"""Pick best mosaic window (S1/S2 unified)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.candidates import ScreenCandidate, generate_window_candidates
from travelogue.curation.mosaic.log import MosaicWindowLog
from travelogue.curation.mosaic.scorer import score_candidate, weights_hash
from travelogue.curation.mosaic.selfheal import try_self_heal_pick
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState


@dataclass
class WindowPickResult:
    screen: dict | None
    log: MosaicWindowLog
    used_legacy: bool


def score_window_candidates(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
) -> list[tuple[ScreenCandidate, float, list[str]]]:
    """Score all MCS window candidates (shared by compose + replan)."""
    candidates = generate_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    scored: list[tuple[ScreenCandidate, float, list[str]]] = []
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
    return scored


def pick_best_window(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    window_size: int,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    window_start: int = 0,
    segment_id: str = "",
) -> WindowPickResult:
    wh = weights_hash(cfg)
    log = MosaicWindowLog(
        segment_id=segment_id,
        window_size=window_size,
        window_start=window_start,
        scorer_version=cfg.scorer_version,
        weights_hash=wh,
    )
    if len(asset_ids) != window_size:
        log.fallback_used = True
        log.fallback_reason = "window_size_mismatch"
        log.planner_path = "legacy"
        return WindowPickResult(screen=None, log=log, used_legacy=True)

    scored = score_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    log.candidates_count = len(scored)
    if not scored:
        log.fallback_used = True
        log.fallback_reason = "no_candidates"
        log.planner_path = "legacy"
        return WindowPickResult(screen=None, log=log, used_legacy=True)

    top = scored[: min(3, cfg.candidate_top_k)]
    log.top3_patterns = [t[0].pattern_id for t in top]
    log.top3_scores = [t[1] for t in top]
    winner_cand, winner_score, reasons = scored[0]
    log.winner_pattern_id = winner_cand.pattern_id
    log.winner_score = winner_score
    log.winner_reason_codes = reasons

    if winner_score < cfg.min_candidate_score:
        healed = try_self_heal_pick(
            scored,
            asset_ids=asset_ids,
            aspects=aspects,
            assets_map=assets_map,
            cfg=cfg,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            burst_seconds=burst_seconds,
            min_score=cfg.min_candidate_score,
        )
        if healed is not None:
            winner_cand, winner_score, reasons, step, dropped = healed
            log.winner_pattern_id = winner_cand.pattern_id
            log.winner_score = winner_score
            log.winner_reason_codes = reasons
            log.self_heal_applied = True
            log.self_heal_step = step
            log.dropped_asset_ids = list(dropped)
            log.planner_path = "mosaic"
            return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)
        if cfg.fallback_to_legacy:
            log.fallback_used = True
            log.fallback_reason = "low_score"
            log.planner_path = "legacy"
            return WindowPickResult(screen=None, log=log, used_legacy=True)

    log.planner_path = "mosaic"
    return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)


def compose_segment_s1(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    chapter_id: str = "",
) -> list[dict]:
    """Plan one segment (chapter bucket) via legacy planner + MCS hook; batch note rhythm."""
    from travelogue.curation.mosaic.state import note_screens_batch
    from travelogue.curation.screen_planner import plan_screens_for_chapter

    screens = plan_screens_for_chapter(
        asset_ids,
        aspects,
        assets=assets_map,
        burst_seconds=burst_seconds,
        chapter_id=chapter_id,
        trip_photo_total=trip_photo_total,
    )
    note_screens_batch(layout_state, screens)
    return screens


compose_segment = compose_segment_s1


def pick_best_five_window(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    **kwargs,
) -> WindowPickResult:
    """Backward-compatible alias."""
    return pick_best_window(
        asset_ids, aspects, assets_map, window_size=5, **kwargs
    )


def pick_best_candidate(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    window_size: int = 5,
    **kwargs,
) -> WindowPickResult:
    """PRD §4.2 alias · scored window pick."""
    return pick_best_window(
        asset_ids, aspects, assets_map, window_size=window_size, **kwargs
    )
