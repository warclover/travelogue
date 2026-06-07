"""Pick best mosaic window (S1/S2 unified)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.candidates import (
    ScreenCandidate,
    generate_window_candidates_with_rejections,
)
from travelogue.curation.mosaic.diversity import apply_candidate_diversity
from travelogue.curation.mosaic.log import MosaicWindowLog
from travelogue.curation.mosaic.log_enrich import enrich_mosaic_log_from_screen
from travelogue.curation.mosaic.lte_adapter import mcs_diversity_config
from travelogue.curation.mosaic.pattern_policy import mosaic_pattern_disabled
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
    scored, _rejected = _score_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    return scored


def _score_window_candidates_with_rejections(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
) -> tuple[list[tuple[ScreenCandidate, float, list[str]]], list[dict]]:
    """Score MCS window candidates and collect validator-level rejections."""
    bundle = generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    candidates = bundle.candidates
    rejected = list(bundle.rejected)
    scored: list[tuple[ScreenCandidate, float, list[str]]] = []
    for cand in candidates:
        if mosaic_pattern_disabled(cand.pattern_id, cfg=cfg) or not cand.hard_valid:
            if not cand.hard_valid and not any(
                r.get("templateId") == cand.pattern_id for r in rejected
            ):
                rejected.append({"templateId": cand.pattern_id, "reason": "hard_invalid"})
            continue
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
    div_cfg = mcs_diversity_config()
    scored = apply_candidate_diversity(
        scored,
        layout_state=layout_state,
        mode=str(div_cfg.get("mode", "off")),
        mmr_lambda=float(div_cfg.get("lambda", 0.65)),
    )
    return scored, rejected


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

    scored, rejected = _score_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    log.rejected_templates = rejected
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
    if mosaic_pattern_disabled(winner_cand.pattern_id, cfg=cfg):
        log.fallback_used = True
        log.fallback_reason = "pattern_disabled"
        log.planner_path = "legacy"
        return WindowPickResult(screen=None, log=log, used_legacy=True)
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
            enrich_mosaic_log_from_screen(log, winner_cand.screen, assets_map=assets_map)
            return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)
        if cfg.fallback_to_legacy:
            log.fallback_used = True
            log.fallback_reason = "low_score"
            log.planner_path = "legacy"
            return WindowPickResult(screen=None, log=log, used_legacy=True)

    log.planner_path = "mosaic"
    enrich_mosaic_log_from_screen(log, winner_cand.screen, assets_map=assets_map)
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
