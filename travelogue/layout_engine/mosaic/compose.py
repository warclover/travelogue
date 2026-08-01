"""Pick best mosaic window (S1/S2 unified)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    trip_id: str | None = None,
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
        trip_id=trip_id,
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
    trip_id: str | None = None,
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
        trip_id=trip_id,
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
    trip_id: str | None = None,
    ssg_policy: Any | None = None,
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
        trip_id=trip_id,
        ssg_policy=ssg_policy,
    )
    candidates = bundle.candidates
    rejected = list(bundle.rejected)
    usage_hits = list(bundle.usage_rule_hits)
    contract_shadow = bundle.contract_shadow
    scored: list[tuple[ScreenCandidate, float, list[str], dict[str, float]]] = []
    for cand in candidates:
        if mosaic_pattern_disabled(cand.pattern_id, cfg=cfg, trip_id=trip_id) or not cand.hard_valid:
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


def _mtso_quota_snapshot(
    layout_state: ScreenLayoutPlannerState | None,
) -> dict | None:
    if layout_state is None:
        return None
    return {
        "denseUsed": int(layout_state.dense_collage_used),
        "denseMax": int(layout_state.dense_collage_max),
        "largeChapterUsed": int(layout_state.large_mosaic_chapter_used),
        "largeChapterMax": int(layout_state.large_mosaic_max_per_chapter),
        "lastWasDense": bool(layout_state.last_was_dense_collage),
    }


def _prefer_six_hero_canonical(scored: list) -> list:
    """SUP-07 · when twin six-hero patterns tie at top score, emit canonical."""
    if len(scored) < 2:
        return scored
    from travelogue.layout_engine.mosaic.lifecycle import (
        SIX_HERO_FAMILY_CANONICAL,
        six_hero_family_id,
    )

    top_score = float(scored[0][1])
    tied_idx = [
        i
        for i, row in enumerate(scored)
        if abs(float(row[1]) - top_score) <= 1e-9
        and six_hero_family_id(row[0].pattern_id)
    ]
    if len(tied_idx) < 2:
        return scored
    can_i = next(
        (i for i in tied_idx if scored[i][0].pattern_id == SIX_HERO_FAMILY_CANONICAL),
        None,
    )
    if can_i is None or can_i == 0:
        return scored
    preferred = scored[can_i]
    return [preferred] + [row for i, row in enumerate(scored) if i != can_i]


def _apply_six_hero_outcome(log: MosaicWindowLog, *, won_six: bool) -> None:
    if log.six_hero_outcome:
        return
    if not (
        log.window_size == 6
        or log.structurally_qualified_six
        or log.admit_six_hero
        or log.six_hero_qualify_reason
    ):
        return
    from travelogue.layout_engine.mosaic.hero_six import six_hero_outcome_label
    from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id

    won = bool(won_six and six_hero_family_id(log.winner_pattern_id))
    log.six_hero_outcome = six_hero_outcome_label(
        structural=bool(log.structurally_qualified_six),
        admit=bool(log.admit_six_hero),
        reason=str(log.six_hero_qualify_reason or ""),
        attempted_six=log.window_size == 6,
        won_six=won,
    )


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
    trip_id: str | None = None,
    funnel: dict | None = None,
    ssg_policy: Any | None = None,
) -> WindowPickResult:
    wh = weights_hash(cfg)
    base_order = list(
        getattr(getattr(cfg, "density_budget", None), "window_order", ()) or ()
    )
    funnel = funnel or {}
    opp_state = "idle"
    if layout_state is not None:
        opp_state = str(getattr(layout_state, "hero_six_opportunity", "idle") or "idle")
    log = MosaicWindowLog(
        segment_id=segment_id,
        window_size=window_size,
        window_start=window_start,
        scorer_version=cfg.scorer_version,
        weights_hash=wh,
        base_window_order=list(funnel.get("base_window_order") or base_order),
        effective_window_order=list(
            funnel.get("effective_window_order") or funnel.get("base_window_order") or base_order
        ),
        reorder_reason=funnel.get("reorder_reason"),
        atom_cap=funnel.get("atom_cap"),
        structurally_qualified_six=bool(funnel.get("structurally_qualified_six", False)),
        admit_six_hero=bool(funnel.get("admit_six_hero", False)),
        six_hero_opportunity_state=str(
            funnel.get("six_hero_opportunity_state") or opp_state
        ),
        six_hero_family_id=None,
        six_hero_qualify_reason=funnel.get("six_hero_qualify_reason"),
        six_hero_outcome=funnel.get("six_hero_outcome"),
        quota_snapshot=funnel.get("quota_snapshot") or _mtso_quota_snapshot(layout_state),
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
        trip_id=trip_id,
        ssg_policy=ssg_policy,
    )
    log.rejected_templates = rejected
    log.usage_rule_rejects = _usage_rule_log_entries(rejected)
    log.usage_rule_hits = usage_hits
    log.candidates_count = len(scored)
    from travelogue.layout_engine.mosaic.lifecycle import reject_funnel_stage

    log.reject_funnel = [
        {
            "stage": reject_funnel_stage(r.get("reason")),
            "templateId": r.get("templateId"),
            "reason": r.get("reason"),
            **({"detail": r["detail"]} if r.get("detail") else {}),
        }
        for r in rejected
    ]
    if isinstance(contract_shadow, dict):
        log.window_mix = contract_shadow.get("windowMix") or None
        log.candidate_source = contract_shadow.get("candidateSource") or None
        log.square_relaxed = bool(contract_shadow.get("squareRelaxed"))
    if not scored:
        log.fallback_used = True
        log.fallback_reason = "no_candidates"
        log.planner_path = "legacy"
        # LTN E4 · no legal window ⇒ do not force emit (opportunity min is soft only).
        return WindowPickResult(screen=None, log=log, used_legacy=True)

    # LTN E4 · legal scored set counts as dense opportunity (observability).
    if layout_state is not None:
        layout_state.note_dense_opportunity()

    # LTN C5 · arm on hero opportunity; while armed, drop equal-weight dense winners.
    # SUP-03 · MTSO selection_optimization ON → skip old reserve arm+filter (isolated).
    from travelogue.config.mosaic import effective_selection_optimization_enabled

    if layout_state is not None and not effective_selection_optimization_enabled(cfg):
        from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

        hero_hits = [
            row
            for row in scored
            if row[1] >= cfg.min_candidate_score
            and ScreenLayoutPlannerState.pattern_has_main_role(row[0].pattern_id)
        ]
        if hero_hits:
            layout_state.arm_hero_reserve()
        if layout_state.hero_reserve == "armed":
            filtered = [
                row
                for row in scored
                if not layout_state.blocks_dense_for_hero_reserve(row[0].pattern_id)
            ]
            if filtered:
                scored = filtered

    # SUP-07 · twin six-hero emit tie-break → canonical when scores tie.
    scored = _prefer_six_hero_canonical(scored)
    top = scored[: min(3, cfg.candidate_top_k)]
    log.top3_patterns = [t[0].pattern_id for t in top]
    log.top3_scores = [t[1] for t in top]
    winner_cand, winner_score, reasons, winner_penalties = scored[0]
    if mosaic_pattern_disabled(winner_cand.pattern_id, cfg=cfg, trip_id=trip_id):
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
    from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id

    log.six_hero_family_id = six_hero_family_id(winner_cand.pattern_id)
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
            trip_id=trip_id,
        )
        if healed is not None:
            winner_cand, winner_score, reasons, step, dropped, healed_penalties = healed
            if mosaic_pattern_disabled(
                winner_cand.pattern_id, cfg=cfg, trip_id=trip_id
            ):
                healed = None
            else:
                log.winner_pattern_id = winner_cand.pattern_id
                log.winner_score = winner_score
                log.winner_reason_codes = reasons
                log.winner_penalties = dict(healed_penalties)
                log.six_hero_family_id = six_hero_family_id(winner_cand.pattern_id)
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
                _attach_msa_log_from_screen(log, winner_cand.screen)
                _attach_raw_geometry_features(log, winner_cand.pattern_id)
                return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)
        if cfg.fallback_to_legacy:
            log.fallback_used = True
            log.fallback_reason = "low_score"
            log.planner_path = "legacy"
            return WindowPickResult(screen=None, log=log, used_legacy=True)

    log.planner_path = "mosaic"
    enrich_mosaic_log_from_screen(log, winner_cand.screen, assets_map=assets_map)
    _attach_msa_log_from_screen(log, winner_cand.screen)
    _attach_raw_geometry_features(log, winner_cand.pattern_id)
    return WindowPickResult(screen=winner_cand.screen, log=log, used_legacy=False)


def _attach_msa_log_from_screen(log: MosaicWindowLog, screen: dict | None) -> None:
    """Copy MSA instance fields from screen.layoutGeometry into raw window log.

    Always mirrors slot ``cropFocal`` / ``cropSafety`` when present so person-safe
    crop telemetry lands in mosaicDecisionLog even when MSA parent is OFF / not
    whitelisted (no ``layoutGeometry.msa`` block).
    """
    geo = (screen or {}).get("layoutGeometry") or {}
    msa = geo.get("msa") if isinstance(geo.get("msa"), dict) else {}

    def _derive_crop_focals() -> list[dict[str, Any]] | None:
        derived: list[dict[str, Any]] = []
        for s in (screen or {}).get("slots") or []:
            if not isinstance(s, dict):
                continue
            if not s.get("cropFocal") and not s.get("cropSafety"):
                continue
            derived.append(
                {
                    "slot": s.get("slot"),
                    "assetId": s.get("assetId"),
                    "cropFocal": s.get("cropFocal"),
                    "safety": s.get("cropSafety"),
                    "feasible": not bool((s.get("cropSafety") or {}).get("faceClipped")),
                    "containFlipped": bool(s.get("cropContain")),
                }
            )
        return derived or None

    if not msa:
        log.msa_outcome = log.msa_outcome or "skipped_parent_off"
        if log.crop_focals is None:
            log.crop_focals = _derive_crop_focals()
        fits = [str(s.get("fit") or "cover") for s in (screen or {}).get("slots") or []]
        if fits and log.slot_fits is None:
            log.slot_fits = fits
        return

    log.msa_profile = msa.get("profile")
    log.r_hero_target = msa.get("rHeroTarget")
    log.track_override = geo.get("trackOverride")
    fits = [str(s.get("fit") or "cover") for s in (screen or {}).get("slots") or []]
    log.slot_fits = fits or None
    crop = msa.get("cropRisk")
    log.crop_risk = list(crop) if isinstance(crop, list) else None
    focals = msa.get("cropFocals")
    if isinstance(focals, list):
        log.crop_focals = list(focals)
    else:
        log.crop_focals = _derive_crop_focals()
    ws = msa.get("whitespaceRatio", geo.get("whitespaceRatio"))
    try:
        log.whitespace_ratio = float(ws) if ws is not None else None
    except (TypeError, ValueError):
        log.whitespace_ratio = None
    log.msa_outcome = str(msa.get("outcome") or "skipped_parent_off")


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
