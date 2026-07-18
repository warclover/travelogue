"""Window-level candidate generation (M4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config import MosaicConfig, get_config
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.usage_context import WindowContext
from travelogue.layout_contract.usage_rules_registry import USAGE_RULE_UNDO_ORDER
from travelogue.layout_engine.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.layout_engine.mosaic.features import feature_summary_for_window
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
) -> list[ScreenCandidate]:
    return generate_window_candidates_with_rejections(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        registry=registry,
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
) -> WindowCandidateResult:
    asset_ids = _mosaic_eligible_asset_ids(asset_ids, assets_map)
    if len(asset_ids) not in effective_mosaic_window_sizes(cfg):
        return WindowCandidateResult(candidates=[], rejected=[])
    reg = registry or mosaic_registry()
    patterns = patterns_for_window_size(len(asset_ids), reg)
    summary = feature_summary_for_window(asset_ids, assets_map)
    out: list[ScreenCandidate] = []
    rejected: list[dict[str, Any]] = []
    usage_deferred: list[tuple[ScreenCandidate, str]] = []
    usage_hits: list[dict[str, Any]] = []
    orderable_pattern_ids: list[str] = []
    for pat in patterns:
        if mosaic_pattern_disabled(pat.pattern_id, cfg=cfg):
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
        main_ok, main_reason = screen_main_slot_eligible(
            screen,
            assets_map,
            pattern_id=pat.pattern_id,
            cfg=cfg,
        )
        geom_ok = geom_ok and main_ok
        if not geom_ok and not main_ok:
            _reject(rejected, pat.pattern_id, "main_ar_ineligible", detail=main_reason)
        elif not geom_ok:
            _reject(rejected, pat.pattern_id, "geometry_invalid")
        elif geom_ok and main_ok and window_ctx is not None:
            reject, rule_id, detail = evaluate_reject(
                pat.pattern_id, window_ctx, screen=screen
            )
            if reject and rule_id:
                reason = f"usage_rule:{rule_id}"
                _reject(rejected, pat.pattern_id, reason, detail=detail)
                feat = {**summary, "patternId": pat.pattern_id}
                if slot_fallback:
                    feat["slotAssignmentFallback"] = slot_fallback
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
    tc = getattr(cfg, "template_contract", None)
    if tc is not None and getattr(tc, "shadow_log", False) and not getattr(tc, "enabled", False):
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
