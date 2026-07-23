"""TPC W2 · TemplateContract evaluator (mix exact + eligibility bridge).

Default path remains off via ``mosaic.template_contract.enabled=false``.
When enabled: mix inverted index → (caller) usage_rules → eligibility.
``mainSlotPolicy`` is bridged when ``constraints.eligibility`` is absent
(W2; delete bridge in W3 — AC-TPC-04).
"""

from __future__ import annotations

import logging
from typing import Any, Literal, Mapping

from travelogue.config import MosaicConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_engine.contract.eligibility_normalize import (
    normalize_eligibility_spec,
)
from travelogue.layout_engine.contract.mix_index import (
    MixKey,
    format_mix_key,
    mix_key_from_aspects,
    mix_key_from_template,
)
from travelogue.layout_engine.contract.shadow import index_pattern_ids_for_mix
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.main_eligibility import screen_main_slot_eligible
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern

_log = logging.getLogger(__name__)

EligibilitySource = Literal["eligibility", "mainSlotPolicy", "none"]

# Patterns that already emitted a deprecation log this process (noise control).
_BRIDGED_DEPRECATION_SEEN: set[str] = set()


def reset_evaluator_state_for_tests() -> None:
    _BRIDGED_DEPRECATION_SEEN.clear()


def _template_constraints(pattern_id: str) -> dict[str, Any]:
    try:
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
        raw = template.constraints or {}
        return dict(raw) if isinstance(raw, dict) else {}
    except (KeyError, AttributeError, TypeError):
        return {}


def resolve_eligibility_spec(pattern_id: str) -> tuple[dict[str, Any] | None, EligibilitySource]:
    """Prefer ``constraints.eligibility``; else bridge ``mainSlotPolicy``.

    Both specs are normalized to camelCase (AC-TPC-18) so callers read one spelling.
    """
    constraints = _template_constraints(pattern_id)
    elig = constraints.get("eligibility")
    if isinstance(elig, dict) and elig:
        return normalize_eligibility_spec(elig), "eligibility"
    policy = constraints.get("mainSlotPolicy")
    if isinstance(policy, dict) and policy:
        return normalize_eligibility_spec(policy), "mainSlotPolicy"
    return None, "none"


def _hero_area_from_template(pattern_id: str) -> float | None:
    """Hero area as col_frac × row_frac (weighted tracks · MGQ BLK-09)."""
    try:
        from travelogue.layout_templates.geometry import _track_weights
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
    except (KeyError, AttributeError, TypeError):
        return None
    if not template.stage:
        return None
    main_slot = None
    for slot in template.slots:
        if str(slot.role or "").lower() == "main":
            main_slot = slot
            break
    if main_slot is None and template.slots:
        main_slot = max(
            template.slots,
            key=lambda s: (s.visual_weight is not None, s.visual_weight or 0.0, -s.index),
        )
    if main_slot is None or not main_slot.rect:
        return None
    c0, c1, r0, r1 = main_slot.rect
    cols, rows = _track_weights(template.stage)
    col_sum, row_sum = sum(cols), sum(rows)
    if col_sum <= 0 or row_sum <= 0:
        return None
    col_frac = sum(cols[c0 - 1 : c1]) / col_sum
    row_frac = sum(rows[r0 - 1 : r1]) / row_sum
    return float(col_frac * row_frac)


def _evaluate_eligibility_dict(
    pattern_id: str,
    spec: dict[str, Any],
    *,
    trip_photo_total: int = 0,
) -> tuple[bool, str | None, str | None]:
    # Single spelling for the whole function (AC-TPC-18); idempotent if already normalized.
    spec = normalize_eligibility_spec(spec)
    canvas = spec.get("canvasAr")
    if isinstance(canvas, (list, tuple)) and len(canvas) == 2:
        try:
            from travelogue.layout_templates.geometry import parse_aspect_ratio
            from travelogue.layout_templates.registry import get_engine

            stage_ar = parse_aspect_ratio(get_engine().get(pattern_id).stage.aspect)
            lo_c, hi_c = float(canvas[0]), float(canvas[1])
            if stage_ar < lo_c or stage_ar > hi_c:
                return (
                    False,
                    "contract:eligibility_canvas_ar",
                    f"canvasAr={stage_ar:.4f} band=[{lo_c:.4f},{hi_c:.4f}]",
                )
        except (KeyError, AttributeError, TypeError, ValueError):
            _log.warning(
                "tpc.eligibility: canvasAr check failed for %s (invalid template)",
                pattern_id,
                exc_info=True,
            )
            return False, "contract:invalid_template", "canvasAr check failed"

    band = spec.get("heroAreaBand")
    scale = spec.get("photoCountScale")
    need_area = isinstance(band, (list, tuple)) and len(band) == 2
    need_area = need_area or isinstance(scale, dict)
    area = _hero_area_from_template(pattern_id) if need_area else None

    # Unified maxHeroAreaAtRef ceiling (was duplicated in the band + scale-only
    # branches). Applies whenever photoCountScale is declared and we have an area.
    if isinstance(scale, dict) and trip_photo_total > 0 and area is not None:
        ref = int(scale.get("referenceCount") or 20)
        max_at_ref = scale.get("maxHeroAreaAtRef")
        if max_at_ref is not None and trip_photo_total >= ref and area > float(max_at_ref):
            return (
                False,
                "contract:eligibility_count_scale",
                f"heroArea={area:.4f} > maxHeroAreaAtRef={float(max_at_ref):.4f}",
            )

    if isinstance(band, (list, tuple)) and len(band) == 2 and area is not None:
        lo, hi = float(band[0]), float(band[1])
        if isinstance(scale, dict) and trip_photo_total > 0:
            ref = int(scale.get("referenceCount") or 20)
            floor_factor = float(scale.get("floorFactorAt50") or 1.0)
            if trip_photo_total >= 50 and floor_factor < 1.0:
                lo = lo * floor_factor
            elif trip_photo_total > ref:
                t = min(1.0, (trip_photo_total - ref) / max(1, 50 - ref))
                lo = lo * (1.0 - t * (1.0 - floor_factor))
        if area < lo or area > hi:
            return (
                False,
                "contract:eligibility_hero_band",
                f"heroArea={area:.4f} band=[{lo:.4f},{hi:.4f}]",
            )
    return True, None, None


def evaluate_contract_eligibility(
    screen: dict,
    assets_map: dict[str, dict],
    *,
    pattern_id: str,
    cfg: MosaicConfig,
    trip_photo_total: int = 0,
) -> tuple[bool, str | None, str | None]:
    """
    Returns (ok, reject_reason, detail).

    Undeclared eligibility ≡ no hard reject (MGQ BLK-11).
    ``mainSlotPolicy`` bridge logs deprecation once per pattern_id.
    """
    spec, source = resolve_eligibility_spec(pattern_id)
    if source == "none":
        return True, None, None

    if source == "mainSlotPolicy":
        if pattern_id not in _BRIDGED_DEPRECATION_SEEN:
            _BRIDGED_DEPRECATION_SEEN.add(pattern_id)
            _log.info(
                "tpc.deprecation: bridging mainSlotPolicy → eligibility for %s "
                "(migrate YAML in W3; AC-TPC-04)",
                pattern_id,
            )
        ok, detail = screen_main_slot_eligible(
            screen,
            assets_map,
            pattern_id=pattern_id,
            cfg=cfg,
        )
        if ok:
            return True, None, None
        return False, "contract:eligibility_main_ar", detail or "main_ar_ineligible"

    assert spec is not None
    ok, reason, detail = _evaluate_eligibility_dict(
        pattern_id, spec, trip_photo_total=trip_photo_total
    )
    if not ok:
        return False, reason, detail
    # Native eligibility may still require main AR kinds if declared alongside
    if spec.get("eligibleAspectKinds") or spec.get("forbidKinds"):
        ok2, detail2 = screen_main_slot_eligible(
            screen, assets_map, pattern_id=pattern_id, cfg=cfg
        )
        if not ok2:
            return False, "contract:eligibility_main_ar", detail2
    return True, None, None


def _fallback_feasible(template_key: MixKey, window_key: MixKey) -> tuple[bool, bool]:
    """BLK-TPC-01 letter-wise feasibility + square relaxation (S→P then S→L).

    Returns ``(ok, square_relaxed)``. Template S slots may only be filled by window S
    (no P/L → S). Extra window S may fill remaining P then L demand.
    """
    if sum(template_key) != sum(window_key):
        return False, False
    tl, tp, ts = template_key
    wl, wp, ws = window_key
    if ts > ws:
        return False, False
    rem_s = ws - ts
    need_l, need_p = tl, tp
    avail_l, avail_p = wl, wp
    take_l = min(need_l, avail_l)
    need_l -= take_l
    take_p = min(need_p, avail_p)
    need_p -= take_p
    square_relaxed = False
    if need_p > 0 and rem_s > 0:
        take = min(need_p, rem_s)
        need_p -= take
        rem_s -= take
        square_relaxed = True
    if need_l > 0 and rem_s > 0:
        take = min(need_l, rem_s)
        need_l -= take
        rem_s -= take
        square_relaxed = True
    if need_l > 0 or need_p > 0:
        return False, False
    return True, square_relaxed


def contract_pattern_ids_for_window(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    *,
    registry: dict[str, MosaicPattern] | None = None,
) -> tuple[list[str], str, bool, list[dict[str, Any]]]:
    """
    Return (pattern_ids, source, square_relaxed, infeasible_rejects).

    source is ``exact`` | ``fallback`` | ``miss``.
    """
    if registry is None:
        # Contract resolution sees all active LTE templates (incl. experimental).
        # Emit-time admission stays in lifecycle_admit / mosaic_registry.
        from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
        from travelogue.layout_templates.registry import get_engine

        registry = {
            t.id: export_mosaic_pattern(t)
            for t in get_engine().list_active(enforce_quotas=False)
        }
    reg = registry
    key = mix_key_from_aspects(list(asset_ids), aspects)
    # mosaic_only=False: include experimental percent=0 SKUs for contract matching
    # (emit-time admission remains lifecycle_admit / mosaic_registry).
    exact = [
        pid for pid in index_pattern_ids_for_mix(key, mosaic_only=False) if pid in reg
    ]
    if exact:
        return exact, "exact", False, []

    n = len(asset_ids)
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    active = {t.id for t in engine.list_active(enforce_quotas=False)}
    fallback: list[str] = []
    infeasible: list[dict[str, Any]] = []
    square_any = False
    for pid, pat in sorted(reg.items()):
        if pat.slot_count != n or pid not in active:
            continue
        try:
            tmpl = engine.get(pid)
        except KeyError:
            continue
        tkey = mix_key_from_template(tmpl)
        if tkey is None:
            continue
        ok, relaxed = _fallback_feasible(tkey, key)
        if ok:
            fallback.append(pid)
            square_any = square_any or relaxed
        else:
            infeasible.append(
                {
                    "templateId": pid,
                    "reason": "contract:infeasible_mix",
                    "detail": f"template={format_mix_key(tkey)} window={format_mix_key(key)}",
                }
            )
    if fallback:
        return sorted(set(fallback)), "fallback", square_any, infeasible
    return [], "miss", False, infeasible


def patterns_for_contract_window(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    *,
    registry: dict[str, MosaicPattern] | None = None,
) -> tuple[list[MosaicPattern], str, str, bool, list[dict[str, Any]]]:
    """Resolve patterns + source + mix label + squareRelaxed + infeasible rejects."""
    if registry is None:
        # Align with contract_pattern_ids_for_window: include experimental SKUs.
        # Default mosaic_registry() excludes experimental until template_experiments.
        from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
        from travelogue.layout_templates.registry import get_engine

        reg = {
            t.id: export_mosaic_pattern(t)
            for t in get_engine().list_active(enforce_quotas=False)
        }
    else:
        reg = registry
    key = mix_key_from_aspects(list(asset_ids), aspects)
    ids, source, square_relaxed, infeasible = contract_pattern_ids_for_window(
        list(asset_ids), aspects, registry=reg
    )
    patterns = [reg[pid] for pid in ids if pid in reg]
    return patterns, source, format_mix_key(key), square_relaxed, infeasible
