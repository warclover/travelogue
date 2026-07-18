"""Pick best mosaic window (S1/S2 unified)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config import MosaicConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.usage_context import build_window_context
from travelogue.layout_engine.mosaic.candidates import (
    ScreenCandidate,
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.diversity import apply_candidate_diversity
from travelogue.layout_engine.mosaic.log import MosaicWindowLog
from travelogue.layout_engine.mosaic.log_enrich import enrich_mosaic_log_from_screen
from travelogue.layout_engine.mosaic.lte_adapter import (
    mcs_diversity_config,
    mosaic_pattern_disabled,
)
from travelogue.layout_engine.mosaic.scorer import score_candidate, weights_hash
from travelogue.layout_engine.mosaic.selfheal import try_self_heal_pick
from travelogue.layout_engine.usage_rules.tiebreak import apply_usage_tiebreaks

_FACE_CROP_PROXY_THRESHOLD = 0.05


@dataclass
class WindowPickResult:
    screen: dict | None
    log: MosaicWindowLog
    used_legacy: bool


def score_window_candidates_with_rejections(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    prev_screen: dict | None = None,
    chapter_screen_index: int = 0,
    chapter_screen_count: int = 12,
) -> tuple[list[tuple[ScreenCandidate, float, list[str], dict[str, float]]], list[dict], list[dict]]:
    """Score MCS window candidates and return validator-level rejections (golden probe / tests)."""
    scored, rejected, hits, _shadow = _score_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        prev_screen=prev_screen,
        chapter_screen_index=chapter_screen_index,
        chapter_screen_count=chapter_screen_count,
    )
    return scored, rejected, hits


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
) -> list[tuple[ScreenCandidate, float, list[str], dict[str, float]]]:
    """Score all MCS window candidates (shared by compose + replan)."""
    scored, _rejected, _hits, _shadow = _score_window_candidates_with_rejections(
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
    prev_screen: dict | None = None,
    chapter_screen_index: int = 0,
    chapter_screen_count: int = 12,
) -> tuple[
    list[tuple[ScreenCandidate, float, list[str], dict[str, float]]],
    list[dict],
    list[dict],
    dict | None,
]:
    """Score MCS window candidates and collect validator-level rejections."""
    window_ctx = build_window_context(
        asset_ids,
        aspects,
        assets_map,
        layout_state=layout_state,
        median_sharp=median_sharp,
    )
    bundle = generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        window_ctx=window_ctx,
        trip_photo_total=trip_photo_total,
    )
    candidates = bundle.candidates
    rejected = list(bundle.rejected)
    usage_hits = list(bundle.usage_rule_hits)
    contract_shadow = bundle.contract_shadow
    scored: list[tuple[ScreenCandidate, float, list[str], dict[str, float]]] = []
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
            prev_screen=prev_screen,
            chapter_screen_index=chapter_screen_index,
            chapter_screen_count=chapter_screen_count,
        )
        scored.append((cand, sr.total, sr.reason_codes, dict(sr.penalties)))
    scored = apply_usage_tiebreaks(
        scored,
        ctx=window_ctx,
        rejected=rejected,
        usage_hits=usage_hits,
    )
    scored.sort(key=lambda t: (-t[1], t[0].pattern_id))
    div_cfg = mcs_diversity_config()
    scored = apply_candidate_diversity(
        scored,
        layout_state=layout_state,
        mode=str(div_cfg.get("mode", "off")),
        mmr_lambda=float(div_cfg.get("lambda", 0.65)),
    )
    return scored, rejected, usage_hits, contract_shadow


def _usage_rule_log_entries(rejected: list[dict]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for entry in rejected:
        reason = str(entry.get("reason") or "")
        if not reason.startswith("usage_rule:"):
            continue
        rule_id = reason.split(":", 1)[1]
        row: dict[str, str] = {
            "ruleId": rule_id,
            "templateId": str(entry.get("templateId") or ""),
        }
        detail = entry.get("detail")
        if detail:
            row["detail"] = str(detail)
        out.append(row)
    return out


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
    prev_screen: dict | None = None,
    chapter_screen_index: int = 0,
    chapter_screen_count: int = 12,
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

    scored, rejected, usage_hits, contract_shadow = _score_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        prev_screen=prev_screen,
        chapter_screen_index=chapter_screen_index,
        chapter_screen_count=chapter_screen_count,
    )
    log.rejected_templates = rejected
    log.usage_rule_rejects = _usage_rule_log_entries(rejected)
    log.usage_rule_hits = usage_hits
    log.candidates_count = len(scored)
    if isinstance(contract_shadow, dict):
        log.window_mix = contract_shadow.get("windowMix") or None
        log.candidate_source = contract_shadow.get("candidateSource") or None
        log.square_relaxed = bool(contract_shadow.get("squareRelaxed"))
    if not scored:
        log.fallback_used = True
        log.fallback_reason = "no_candidates"
        log.planner_path = "legacy"
        return WindowPickResult(screen=None, log=log, used_legacy=True)

    top = scored[: min(3, cfg.candidate_top_k)]
    log.top3_patterns = [t[0].pattern_id for t in top]
    log.top3_scores = [t[1] for t in top]
    winner_cand, winner_score, reasons, winner_penalties = scored[0]
    if mosaic_pattern_disabled(winner_cand.pattern_id, cfg=cfg):
        log.fallback_used = True
        log.fallback_reason = "pattern_disabled"
        log.planner_path = "legacy"
        return WindowPickResult(screen=None, log=log, used_legacy=True)
    log.winner_pattern_id = winner_cand.pattern_id
    log.winner_score = winner_score
    log.winner_reason_codes = reasons
    log.winner_penalties = dict(winner_penalties)
    log.scoring_weights = dict(cfg.weights or {})
    log.scoring_penalty_weights = dict(cfg.penalties or {})
    fallback = (winner_cand.feature_summary or {}).get("slotAssignmentFallback")
    if fallback:
        log.slot_assignment_fallback = str(fallback)
    _attach_face_crop_proxy(
        log,
        winner_cand.screen,
        aspects=aspects,
        assets_map=assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
    )

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
            median_sharp=median_sharp,
        )
        if healed is not None:
            winner_cand, winner_score, reasons, step, dropped, healed_penalties = healed
            log.winner_pattern_id = winner_cand.pattern_id
            log.winner_score = winner_score
            log.winner_reason_codes = reasons
            log.winner_penalties = dict(healed_penalties)
            _attach_face_crop_proxy(
                log,
                winner_cand.screen,
                aspects=aspects,
                assets_map=assets_map,
                cfg=cfg,
                layout_state=layout_state,
                trip_photo_total=trip_photo_total,
                burst_seconds=burst_seconds,
            )
            log.self_heal_applied = True
            log.self_heal_step = step
            log.dropped_asset_ids = list(dropped)
            log.planner_path = "mosaic"
            enrich_mosaic_log_from_screen(log, winner_cand.screen, assets_map=assets_map)
            _attach_raw_geometry_features(log, winner_cand.pattern_id)
            return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)
        if cfg.fallback_to_legacy:
            log.fallback_used = True
            log.fallback_reason = "low_score"
            log.planner_path = "legacy"
            return WindowPickResult(screen=None, log=log, used_legacy=True)

    log.planner_path = "mosaic"
    enrich_mosaic_log_from_screen(log, winner_cand.screen, assets_map=assets_map)
    _attach_raw_geometry_features(log, winner_cand.pattern_id)
    return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)


def _attach_raw_geometry_features(log: MosaicWindowLog, pattern_id: str) -> None:
    """AC-TPC-10 · record-only raw geometry on winner (decoupled from penalties)."""
    from travelogue.layout_engine.contract.geometry_features import (
        compute_raw_geometry_features,
    )

    feats = compute_raw_geometry_features(pattern_id)
    log.hero_prominence_ratio = feats.get("heroProminenceRatio")  # type: ignore[assignment]
    log.hero_coverage_ratio = feats.get("heroCoverageRatio")  # type: ignore[assignment]
    log.cell_area_cv = feats.get("cellAreaCv")  # type: ignore[assignment]


def _attach_face_crop_proxy(
    log: MosaicWindowLog,
    screen: dict,
    *,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None,
    trip_photo_total: int,
    burst_seconds: float,
) -> None:
    sr = score_candidate(
        screen,
        aspects=aspects,
        assets_by_id=assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
    )
    pen = float(sr.penalties.get("face_crop") or 0.0)
    log.face_crop_proxy = pen > _FACE_CROP_PROXY_THRESHOLD


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
    from travelogue.layout_engine.mosaic.state import note_screens_batch
    from travelogue.layout_engine.planner.screen_planner import plan_screens_for_chapter

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
