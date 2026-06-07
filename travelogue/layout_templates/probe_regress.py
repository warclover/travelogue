"""Synthetic probe regression for LTE templates (V-P16-07 · admission S5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.layout_templates.geometry import slot_aspect_table
from travelogue.layout_templates.validator import validate_template_def

if TYPE_CHECKING:
    from travelogue.layout_templates.registry import LayoutTemplateEngine

# Standard probe aspect ratios (width/height)
PROBE_ASPECTS: dict[str, float] = {
    "portrait-34": 3 / 4,
    "portrait-916": 9 / 16,
    "landscape-32": 3 / 2,
    "landscape-169": 16 / 9,
    "square-11": 1.0,
}

# Person/focal-aware saliency probes (PRD §8 · saliency-retention)
PROBE_PROFILES: tuple[dict, ...] = (
    {"name": "neutral-center", "aspect": 16 / 9, "focal": (0.5, 0.45), "tags": []},
    {"name": "portrait-person", "aspect": 3 / 4, "focal": (0.5, 0.35), "tags": ["person"]},
    {"name": "landscape-person", "aspect": 16 / 9, "focal": (0.55, 0.42), "tags": ["person"]},
    {"name": "square-subject", "aspect": 1.0, "focal": (0.48, 0.40), "tags": ["person"]},
)


def _probe_fit_distance(slot_ar: float, asset_ar: float) -> float:
    return abs(slot_ar - asset_ar) / max(slot_ar, asset_ar, 1e-6)


def _cover_focal_retention(
    slot_ar: float,
    asset_ar: float,
    *,
    focal_x: float = 0.5,
    focal_y: float = 0.45,
) -> float:
    """Saliency proxy: focal point visible under object-fit cover with center crop."""
    fx = max(0.0, min(1.0, focal_x))
    fy = max(0.0, min(1.0, focal_y))
    if slot_ar <= 0 or asset_ar <= 0:
        return 0.0
    if slot_ar >= asset_ar:
        visible_h = asset_ar / slot_ar
        y0 = (1.0 - visible_h) / 2.0
        y1 = y0 + visible_h
        if y0 <= fy <= y1:
            return 1.0
        dist = min(abs(fy - y0), abs(fy - y1))
        return max(0.0, 1.0 - dist * 4.0)
    visible_w = slot_ar / asset_ar
    x0 = (1.0 - visible_w) / 2.0
    x1 = x0 + visible_w
    if x0 <= fx <= x1:
        return 1.0
    dist = min(abs(fx - x0), abs(fx - x1))
    return max(0.0, 1.0 - dist * 4.0)


def _profile_saliency_retention(slot_ar: float, profile: dict) -> float:
    fx, fy = profile.get("focal") or (0.5, 0.45)
    asset_ar = float(profile["aspect"])
    retention = _cover_focal_retention(slot_ar, asset_ar, focal_x=float(fx), focal_y=float(fy))
    tags = profile.get("tags") or []
    if "person" in tags and retention < 0.75:
        retention *= 0.85
    return retention


def _worst_saliency_for_slot(slot_ar: float) -> float:
    return min(_profile_saliency_retention(slot_ar, profile) for profile in PROBE_PROFILES)


def run_probe_for_template(
    engine: LayoutTemplateEngine,
    template_id: str,
    *,
    warn_threshold: float = 0.35,
    saliency_warn_threshold: float = 0.55,
) -> dict:
    """Geometry + saliency probe for one template (admission S5)."""
    try:
        t = engine.get(template_id)
    except KeyError:
        return {
            "ok": False,
            "templateId": template_id,
            "warnings": [f"{template_id}: template not found"],
            "probeCount": 0,
        }
    if t.kind == "stack":
        return {
            "ok": True,
            "templateId": template_id,
            "skipped": True,
            "reason": "stack template",
            "warnings": [],
            "probeCount": 0,
        }
    report = validate_template_def(t, mode="ci")
    warnings: list[str] = []
    results: list[dict] = []
    for slot in slot_aspect_table(t):
        worst = max(_probe_fit_distance(slot.display_aspect, ar) for ar in PROBE_ASPECTS.values())
        worst_retention = _worst_saliency_for_slot(slot.display_aspect)
        results.append(
            {
                "templateId": template_id,
                "slot": slot.index,
                "role": slot.role,
                "slotAspect": round(slot.display_aspect, 4),
                "worstProbeDistance": round(worst, 4),
                "worstSaliencyRetention": round(worst_retention, 4),
            }
        )
        if worst > warn_threshold:
            warnings.append(
                f"{template_id} slot {slot.index} worstProbeDistance={worst:.3f} > {warn_threshold}"
            )
        if worst_retention < saliency_warn_threshold:
            warnings.append(
                f"{template_id} slot {slot.index} worstSaliencyRetention={worst_retention:.3f} "
                f"< {saliency_warn_threshold}"
            )
    if not report.ok:
        warnings.append(
            f"{template_id} validator errors: {[i.code for i in report.issues if i.level != 'warn']}"
        )
    return {
        "ok": len(warnings) == 0,
        "templateId": template_id,
        "probeCount": len(results),
        "warnings": warnings,
        "samples": results[:10],
    }


def run_probe_regress(
    engine: LayoutTemplateEngine,
    *,
    only_active: bool = True,
    warn_threshold: float = 0.35,
    saliency_warn_threshold: float = 0.55,
) -> dict:
    results: list[dict] = []
    warnings: list[str] = []
    for tid in sorted(engine._templates):
        t = engine._templates[tid]
        if only_active and t.status in ("deprecated", "disabled"):
            continue
        if t.kind == "stack":
            continue
        one = run_probe_for_template(
            engine,
            tid,
            warn_threshold=warn_threshold,
            saliency_warn_threshold=saliency_warn_threshold,
        )
        warnings.extend(one.get("warnings") or [])
        results.extend(one.get("samples") or [])
    return {
        "ok": len(warnings) == 0,
        "probeCount": len(results),
        "warnings": warnings,
        "samples": results[:20],
    }
