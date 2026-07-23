"""Window-level candidate generation (M4)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from travelogue.config import MosaicConfig, get_config
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.usage_context import WindowContext
from travelogue.layout_contract.usage_rules_registry import USAGE_RULE_UNDO_ORDER
from travelogue.layout_engine.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.layout_engine.mosaic.clone_detection import (
    NEAR_SCENE_CLONE_REJECT_THRESHOLD,
    near_scene_clone_penalty,
    template_prefers_burst,
)
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
from travelogue.layout_engine.mosaic.features import feature_summary_for_window
from travelogue.layout_engine.mosaic.hero_six import (
    effective_mixed_hero_routing_enabled,
    mixed_portrait_is_hero,
)
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_pattern_disabled, mosaic_registry
from travelogue.layout_engine.mosaic.main_eligibility import screen_main_slot_eligible
from travelogue.layout_engine.mosaic.pattern_catalog import (
    MosaicPattern,
    patterns_for_window_size,
)
from travelogue.layout_engine.mosaic.runtime import effective_mosaic_window_sizes
from travelogue.layout_engine.mosaic.slot_geometry import screen_slots_geometry_ok
from travelogue.layout_engine.usage_rules.evaluator import evaluate_reject
from travelogue.media.media_classify import is_collage_asset


@dataclass
class ScreenCandidate:
    pattern_id: str
    ordered_asset_ids: list[str]
    screen: dict
    feature_summary: dict[str, Any] = field(default_factory=dict)
    hard_valid: bool = True


def _mosaic_eligible_asset_ids(
    asset_ids: list[str],
    assets_map: dict[str, dict],
) -> list[str]:
    te = getattr(get_config().layout, "template_engine", None)
    if te is None or not getattr(te, "exclude_collage_from_mosaic", True):
        return asset_ids
    return [aid for aid in asset_ids if not is_collage_asset(assets_map.get(aid, {}))]


@dataclass
class WindowCandidateResult:
    candidates: list[ScreenCandidate]
    rejected: list[dict[str, Any]] = field(default_factory=list)
    usage_rule_hits: list[dict[str, Any]] = field(default_factory=list)
    # TPC W1 shadow (AC-TPC-12); never consumed by pick/score paths.
    contract_shadow: dict[str, Any] | None = None


def _reject(
    rejected: list[dict[str, Any]],
    pattern_id: str,
    reason: str,
    *,
    detail: str | None = None,
) -> None:
    entry: dict[str, Any] = {"templateId": pattern_id, "reason": reason}
    if detail:
        entry["detail"] = detail
    rejected.append(entry)


def _restore_if_usage_emptied_candidates(
    out: list[ScreenCandidate],
    rejected: list[dict[str, Any]],
    usage_deferred: list[tuple[ScreenCandidate, str]],
    usage_hits: list[dict[str, Any]] | None = None,
) -> None:
    if any(c.hard_valid for c in out) or not usage_deferred:
        return
    for rule_id in USAGE_RULE_UNDO_ORDER:
        restore = [c for c, rid in usage_deferred if rid == rule_id]
        if not restore:
            continue
        out.extend(restore)
        restored_ids = {c.pattern_id for c in restore}
        if usage_hits is not None:
            for cand in restore:
                usage_hits.append(
                    {
                        "ruleId": rule_id,
                        "templateId": cand.pattern_id,
                        "action": "restore",
                    }
                )
        rejected[:] = [
            r
            for r in rejected
            if not (
                str(r.get("reason") or "") == f"usage_rule:{rule_id}"
                and r.get("templateId") in restored_ids
            )
        ]
        if any(c.hard_valid for c in out):
            return


def generate_window_candidates(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    registry: dict[str, MosaicPattern] | None = None,
    trip_id: str | None = None,
) -> list[ScreenCandidate]:
    return generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        registry=registry,
        trip_id=trip_id,
    ).candidates


def generate_window_candidates_with_rejections(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    registry: dict[str, MosaicPattern] | None = None,
    window_ctx: WindowContext | None = None,
    trip_photo_total: int = 0,
    trip_id: str | None = None,
) -> WindowCandidateResult:
    asset_ids = _mosaic_eligible_asset_ids(asset_ids, assets_map)
    if len(asset_ids) not in effective_mosaic_window_sizes(cfg):
        return WindowCandidateResult(candidates=[], rejected=[])
    tc = getattr(cfg, "template_contract", None)
    tc_enabled = bool(tc is not None and getattr(tc, "enabled", False))
    if registry is not None:
        reg = registry
    else:
        # Honor MosaicConfig overrides (TPC mix path + MTSO template_experiments).
        reg = mosaic_registry(
            cfg=replace(get_config(), mosaic=cfg),
            trip_id=trip_id,
        )
    contract_source = "legacy_size"
    window_mix_label = ""
    square_relaxed = False
    rejected: list[dict[str, Any]] = []
    if tc_enabled:
        from travelogue.layout_engine.contract.evaluator import (
            patterns_for_contract_window,
        )

        (
            patterns,
            contract_source,
            window_mix_label,
            square_relaxed,
            infeasible_rejects,
        ) = patterns_for_contract_window(asset_ids, aspects, registry=reg)
        for row in infeasible_rejects:
            _reject(
                rejected,
                str(row.get("templateId") or "*"),
                str(row.get("reason") or "contract:infeasible_mix"),
                detail=row.get("detail"),
            )
        if not patterns:
            _reject(rejected, "*", "contract:mix_miss", detail=window_mix_label or None)
            return WindowCandidateResult(
                candidates=[],
                rejected=rejected,
                contract_shadow={
                    "windowMix": window_mix_label,
                    "candidateSource": contract_source,
                    "squareRelaxed": square_relaxed,
                    "livePatternIds": [],
                    "hasDiff": False,
                },
            )
    else:
        patterns = patterns_for_window_size(len(asset_ids), reg)
        contract_source = "legacy_size"
    # LTN C4 · signature on top of TC or legacy sets (TC∩signature).
    # Hit → candidateSource=signature; miss → keep prior set, log contract/legacy
    # source under TC (or signature_fallback on the legacy path).
    from travelogue.layout_engine.mosaic.coarse_segments import apply_signature_route

    patterns, signature_source = apply_signature_route(
        patterns, asset_ids, aspects, assets_map
    )
    if signature_source == "signature":
        route_source = "signature"
    elif tc_enabled:
        route_source = contract_source
    else:
        route_source = signature_source
    summary = feature_summary_for_window(asset_ids, assets_map)
    out: list[ScreenCandidate] = []
    usage_deferred: list[tuple[ScreenCandidate, str]] = []
    usage_hits: list[dict[str, Any]] = []
    orderable_pattern_ids: list[str] = []
    for pat in patterns:
        if mosaic_pattern_disabled(pat.pattern_id, cfg=cfg, trip_id=trip_id):
            _reject(rejected, pat.pattern_id, "pattern_disabled")
            continue
        ordered = try_order_for_pattern(
            pat.pattern_id,
            asset_ids,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )
        if not ordered:
            _reject(rejected, pat.pattern_id, "ordering_failed")
            continue
        # Hard gate (AC-TPC-15): mosaics that do not prefer bursts must not absorb
        # same-scene walking clones (demo-2025 weighted/rail/5-main looked like
        # sliced panoramas). Only rejects when the gate is explicitly enabled; the
        # scorer keeps applying the soft penalty regardless.
        # prefers_burst True → skip; False/None → reject when penalty is high.
        gate = getattr(cfg, "near_scene_clone_gate", None)
        if (
            gate is not None
            and getattr(gate, "enabled", False)
            and template_prefers_burst(pat.pattern_id) is not True
        ):
            clone_pen = near_scene_clone_penalty(
                pat.pattern_id, list(ordered), assets_map
            )
            if clone_pen >= NEAR_SCENE_CLONE_REJECT_THRESHOLD:
                _reject(
                    rejected,
                    pat.pattern_id,
                    "near_scene_clone",
                    detail=f"penalty={clone_pen:.2f}",
                )
                continue
        orderable_pattern_ids.append(pat.pattern_id)
        slot_fallback: str | None = None
        screen = build_screen(pat, ordered, assets_map=assets_map)
        if cfg.lse_hungarian_assignment:
            from travelogue.layout_engine.quality_features import build_quality_pool
            from travelogue.layout_engine.slot_assignment import refine_asset_order_hungarian

            quality = (
                build_quality_pool(list(assets_map.values()))
                if cfg.lse_quality_unified
                else None
            )
            refined, slot_fallback = refine_asset_order_hungarian(
                ordered,
                screen,
                assets_map,
                max_matrix_n=cfg.lse_slot_max_matrix_n,
                quality=quality,
            )
            if refined is not None:
                ordered = refined
                screen = build_screen(pat, ordered, assets_map=assets_map)
        geom_ok = screen_slots_geometry_ok(screen, aspects)
        if tc_enabled:
            from travelogue.layout_engine.contract.evaluator import (
                evaluate_contract_eligibility,
            )

            elig_ok, elig_reason, elig_detail = evaluate_contract_eligibility(
                screen,
                assets_map,
                pattern_id=pat.pattern_id,
                cfg=cfg,
                trip_photo_total=trip_photo_total,
            )
            main_ok, main_reason = elig_ok, elig_detail or elig_reason or "ok"
            reject_reason = elig_reason or "contract:eligibility_main_ar"
        else:
            main_ok, main_reason = screen_main_slot_eligible(
                screen,
                assets_map,
                pattern_id=pat.pattern_id,
                cfg=cfg,
            )
            reject_reason = "main_ar_ineligible"
        # LTN C8 · D-03 hard gates when measurable (area ratio is soft — see scorer).
        from travelogue.layout_engine.mosaic.slot_role_penalties import (
            main_ar_mismatch_gate_ok,
            sidebar_min_short_side_ok,
        )

        ar_ok = main_ar_mismatch_gate_ok(screen, assets_map)
        if ar_ok is False:
            _reject(
                rejected,
                pat.pattern_id,
                "main_ar_mismatch",
                detail="mismatch>1.4",
            )
            continue
        side_ok = sidebar_min_short_side_ok(pat.pattern_id)
        if side_ok is False:
            _reject(
                rejected,
                pat.pattern_id,
                "sidebar_min_short_side",
                detail="short_side<72px@428",
            )
            continue
        geom_ok = geom_ok and main_ok
        if not geom_ok and not main_ok:
            _reject(rejected, pat.pattern_id, reject_reason, detail=main_reason)
        elif not geom_ok:
            _reject(rejected, pat.pattern_id, "geometry_invalid")
        elif geom_ok and main_ok:
            # PR-C1 / SUP-06 · MTSO mixed routing: hard reject, never usage-undo.
            if (
                effective_mixed_hero_routing_enabled(cfg)
                and pat.pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
                and mixed_portrait_is_hero(
                    list(asset_ids),
                    aspects,
                    assets_map,
                    median_sharp=median_sharp,
                    layout_state=(
                        getattr(window_ctx, "layout_state", None)
                        if window_ctx is not None
                        else None
                    ),
                    cfg=cfg,
                )
            ):
                _reject(
                    rejected,
                    pat.pattern_id,
                    "usage_rule:mixed_portrait_is_hero",
                    detail="portrait_hero_is_max",
                )
                continue
            if window_ctx is not None:
                reject, rule_id, detail = evaluate_reject(
                    pat.pattern_id, window_ctx, screen=screen
                )
                if reject and rule_id:
                    reason = f"usage_rule:{rule_id}"
                    _reject(rejected, pat.pattern_id, reason, detail=detail)
                    feat = {**summary, "patternId": pat.pattern_id}
                    if slot_fallback:
                        feat["slotAssignmentFallback"] = slot_fallback
                    if route_source:
                        feat["candidateSource"] = route_source
                    usage_deferred.append(
                        (
                            ScreenCandidate(
                                pattern_id=pat.pattern_id,
                                ordered_asset_ids=ordered,
                                screen=screen,
                                feature_summary=feat,
                                hard_valid=True,
                            ),
                            rule_id,
                        )
                    )
                    continue
        feat = {**summary, "patternId": pat.pattern_id}
        if slot_fallback:
            feat["slotAssignmentFallback"] = slot_fallback
        if route_source:
            feat["candidateSource"] = route_source
        if tc_enabled:
            if square_relaxed:
                feat["squareRelaxed"] = True
            if contract_source == "fallback":
                # Explicit marker for AC-TPC-03
                feat["contractReasons"] = ["contract:mix_fallback"]
                feat["contractMixFallback"] = True
        out.append(
            ScreenCandidate(
                pattern_id=pat.pattern_id,
                ordered_asset_ids=ordered,
                screen=screen,
                feature_summary=feat,
                hard_valid=geom_ok,
            )
        )
    _restore_if_usage_emptied_candidates(out, rejected, usage_deferred, usage_hits)
    if cfg.deterministic_strict:
        out.sort(key=lambda c: (c.pattern_id, tuple(c.ordered_asset_ids)))
    shadow_payload: dict[str, Any] | None = None
    if tc is not None and getattr(tc, "shadow_log", False) and not tc_enabled:
        # Shadow only while contract path is off (W1). Enabling selection is W2+.
        # Reuse orderable ids from this pass — never re-run try_order.
        from travelogue.layout_engine.contract.mix_index import (
            format_mix_key,
            mix_key_from_aspects,
        )
        from travelogue.layout_engine.contract.shadow import index_pattern_ids_for_mix

        key = mix_key_from_aspects(asset_ids, aspects)
        index_ids = index_pattern_ids_for_mix(key)
        live_ids = sorted(orderable_pattern_ids)
        live_set, index_set = set(live_ids), set(index_ids)
        shadow_payload = {
            "windowMix": format_mix_key(key),
            "livePatternIds": live_ids,
            "indexPatternIds": index_ids,
            "onlyInLive": sorted(live_set - index_set),
            "onlyInIndex": sorted(index_set - live_set),
            "hasDiff": bool(live_set ^ index_set),
        }
    elif tc_enabled:
        shadow_payload = {
            "windowMix": window_mix_label,
            "candidateSource": route_source,
            "squareRelaxed": square_relaxed,
            "livePatternIds": sorted(orderable_pattern_ids),
            "hasDiff": False,
        }
    else:
        shadow_payload = {
            "candidateSource": route_source,
            "livePatternIds": sorted(orderable_pattern_ids),
            "hasDiff": False,
        }
    if shadow_payload is not None and "candidateSource" not in shadow_payload:
        shadow_payload["candidateSource"] = route_source
    return WindowCandidateResult(
        candidates=out,
        rejected=rejected,
        usage_rule_hits=usage_hits,
        contract_shadow=shadow_payload,
    )


def generate_five_candidates(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    **kwargs,
) -> list[ScreenCandidate]:
    """PRD §4.2 alias · five-slot window candidates."""
    if len(asset_ids) != 5:
        return []
    return generate_window_candidates(asset_ids, aspects, assets_map, **kwargs)
