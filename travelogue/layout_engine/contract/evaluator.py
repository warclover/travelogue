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
    """Prefer ``constraints.eligibility``; else bridge ``mainSlotPolicy``."""
    constraints = _template_constraints(pattern_id)
    elig = constraints.get("eligibility")
    if isinstance(elig, dict) and elig:
        return dict(elig), "eligibility"
    policy = constraints.get("mainSlotPolicy")
    if isinstance(policy, dict) and policy:
        return dict(policy), "mainSlotPolicy"
    return None, "none"


def _hero_area_from_template(pattern_id: str) -> float | None:
    """Hero area as col_frac × row_frac on the template stage grid (MGQ BLK-09)."""
    try:
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
    except (KeyError, AttributeError, TypeError):
        return None
    grid = template.stage.grid if template.stage else None
    if not grid or len(grid) != 2:
        return None
    cols_n, rows_n = int(grid[0]), int(grid[1])
    if cols_n <= 0 or rows_n <= 0:
        return None
    main_slot = None
    for slot in template.slots:
        if str(slot.role or "").lower() == "main":
            main_slot = slot
            break
    if main_slot is None and template.slots:
        # Heaviest visualWeight, else first slot
        main_slot = max(
            template.slots,
            key=lambda s: (s.visual_weight is not None, s.visual_weight or 0.0, -s.index),
        )
    if main_slot is None:
        return None
    c0, c1, r0, r1 = main_slot.rect
    col_frac = (c1 - c0 + 1) / float(cols_n)
    row_frac = (r1 - r0 + 1) / float(rows_n)
    return col_frac * row_frac


def _evaluate_eligibility_dict(
    pattern_id: str,
    spec: dict[str, Any],
    *,
    trip_photo_total: int = 0,
) -> tuple[bool, str | None, str | None]:
    band = spec.get("heroAreaBand") or spec.get("hero_area_band")
    if isinstance(band, (list, tuple)) and len(band) == 2:
        area = _hero_area_from_template(pattern_id)
        if area is not None:
            lo, hi = float(band[0]), float(band[1])
            # photoCountScale softens floor at large trip sizes (optional)
            scale = spec.get("photoCountScale") or spec.get("photo_count_scale")
            if isinstance(scale, dict) and trip_photo_total > 0:
                ref = int(scale.get("referenceCount") or scale.get("reference_count") or 20)
                floor_factor = float(
                    scale.get("floorFactorAt50") or scale.get("floor_factor_at_50") or 1.0
                )
                if trip_photo_total >= 50 and floor_factor < 1.0:
                    lo = lo * floor_factor
                elif trip_photo_total > ref:
                    # linear ease toward floor_factor between ref and 50
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


def _fallback_feasible(template_key: MixKey, window_key: MixKey) -> bool:
    """BLK-TPC-01 letter-wise: required(x) ≤ available(x) (no flexible pool in V1 exact roles)."""
    for ti, wi in zip(template_key, window_key, strict=True):
        if ti > wi:
            return False
    return sum(template_key) == sum(window_key)


def contract_pattern_ids_for_window(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    *,
    registry: dict[str, MosaicPattern] | None = None,
) -> tuple[list[str], str]:
    """
    Return (pattern_ids, source) where source is ``exact`` | ``fallback`` | ``miss``.

    Exact: bag-of-mix hit in inverted index ∩ mosaic registry.
    Fallback: same N, letter-feasible templates from mosaic registry (stable id order).
    """
    reg = registry or mosaic_registry()
    key = mix_key_from_aspects(list(asset_ids), aspects)
    exact = [pid for pid in index_pattern_ids_for_mix(key) if pid in reg]
    if exact:
        return exact, "exact"

    # Fallback: same window size, letter-feasible *active* LTE templates in mosaic registry.
    n = len(asset_ids)
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    active = {t.id for t in engine.list_active(enforce_quotas=False)}
    fallback: list[str] = []
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
        if _fallback_feasible(tkey, key):
            fallback.append(pid)
    if fallback:
        return sorted(set(fallback)), "fallback"
    return [], "miss"


def patterns_for_contract_window(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
    *,
    registry: dict[str, MosaicPattern] | None = None,
) -> tuple[list[MosaicPattern], str, str]:
    """Resolve MosaicPattern list + source + window mix label."""
    reg = registry or mosaic_registry()
    key = mix_key_from_aspects(list(asset_ids), aspects)
    ids, source = contract_pattern_ids_for_window(
        list(asset_ids), aspects, registry=reg
    )
    patterns = [reg[pid] for pid in ids if pid in reg]
    return patterns, source, format_mix_key(key)
