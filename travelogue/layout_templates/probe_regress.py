"""Synthetic probe regression for LTE templates (V-P16-07 · admission S5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.layout_engine.crop_solver import (
    NormBox,
    cover_window,
    solve_slot_focal,
)
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

# Role → probe aspects the slot can actually receive. A slot only ever holds
# assets whose orientation matches its role, so geometric fit must be measured
# against the *compatible* probe subset — never against the opposite extreme.
#
# Measuring worst-fit against ALL aspects has a hard mathematical floor of
# 0.4375 (a square slot is equidistant from 9:16 and 16:9), so the historical
# warn_threshold of 0.35 was geometrically unreachable and flagged every slot
# unconditionally (88/88), making ``--strict-geometry`` impossible to pass.
ROLE_PROBE_KEYS: dict[str, tuple[str, ...]] = {
    "portrait": ("portrait-34", "portrait-916"),
    "landscape": ("landscape-32", "landscape-169"),
    "main": ("landscape-32", "landscape-169"),
    "hero": ("landscape-32", "landscape-169"),
    "tile": ("landscape-32", "landscape-169"),
    "square": ("square-11",),
}


def _role_probe_aspects(role: str) -> tuple[float, ...]:
    """Probe aspects compatible with ``role`` (falls back to all if unknown)."""
    keys = ROLE_PROBE_KEYS.get((role or "").lower())
    if not keys:
        return tuple(PROBE_ASPECTS.values())
    return tuple(PROBE_ASPECTS[k] for k in keys)


# Person/protect-aware profiles (PRD §8 · saliency-retention + face safety)
PROBE_PROFILES: tuple[dict, ...] = (
    {
        "name": "neutral-center",
        "aspect": 16 / 9,
        "focal": (0.5, 0.45),
        "tags": [],
        "faces": (),
        "protect": None,
    },
    {
        "name": "portrait-bust",
        "aspect": 3 / 4,
        "focal": (0.5, 0.32),
        "tags": ["person"],
        "faces": (NormBox(0.35, 0.12, 0.30, 0.22),),
        "protect": NormBox(0.28, 0.04, 0.44, 0.55),
    },
    {
        "name": "group-three",
        "aspect": 3 / 2,
        "focal": (0.5, 0.40),
        "tags": ["person"],
        # Compact travel group (people close together) — wide spreads belong
        # in true landscape slots (≥~1.25), not near-square mid cells.
        "faces": (
            NormBox(0.28, 0.28, 0.14, 0.20),
            NormBox(0.43, 0.25, 0.14, 0.20),
            NormBox(0.58, 0.30, 0.14, 0.20),
        ),
        "protect": NormBox(0.22, 0.16, 0.56, 0.52),
    },
    {
        "name": "edge-standing",
        "aspect": 16 / 9,
        "focal": (0.18, 0.42),
        "tags": ["person"],
        "faces": (NormBox(0.08, 0.22, 0.14, 0.28),),
        "protect": NormBox(0.04, 0.12, 0.22, 0.70),
    },
    {
        "name": "profile-side",
        "aspect": 3 / 4,
        "focal": (0.62, 0.35),
        "tags": ["person"],
        "faces": (NormBox(0.48, 0.18, 0.28, 0.24),),
        "protect": NormBox(0.40, 0.08, 0.42, 0.58),
    },
)


def _profiles_for_slot(slot_ar: float, role: str) -> tuple[dict, ...]:
    """Only probe person profiles whose asset orientation matches the slot role.

    Putting a wide group shot into a tall portrait tip is a planner mistake, not
    a geometry defect — role-filter keeps the face-clip gate actionable.
    """
    role_l = (role or "").lower()
    portraitish = role_l == "portrait" or (
        role_l in ("main", "hero") and slot_ar < 1.0
    )
    landscapish = role_l in ("landscape", "tile") or (
        role_l in ("main", "hero") and slot_ar >= 1.0
    )
    out: list[dict] = []
    for profile in PROBE_PROFILES:
        tags = profile.get("tags") or []
        ar = float(profile["aspect"])
        if not tags:
            out.append(profile)
            continue
        if portraitish and ar <= 1.05:
            out.append(profile)
        elif landscapish and ar >= 0.95:
            out.append(profile)
        elif not portraitish and not landscapish:
            out.append(profile)
    return tuple(out) if out else PROBE_PROFILES


def _probe_fit_distance(slot_ar: float, asset_ar: float) -> float:
    return abs(slot_ar - asset_ar) / max(slot_ar, asset_ar, 1e-6)


def _cover_focal_retention(
    slot_ar: float,
    asset_ar: float,
    *,
    focal_x: float = 0.5,
    focal_y: float = 0.45,
) -> float:
    """Saliency proxy under CSS object-position percentage (not center crop)."""
    fx = max(0.0, min(1.0, focal_x))
    fy = max(0.0, min(1.0, focal_y))
    if slot_ar <= 0 or asset_ar <= 0:
        return 0.0
    win = cover_window(slot_ar, asset_ar, fx, fy)
    if win.axis == "none":
        return 1.0
    if win.axis == "y":
        if win.y0 - 1e-9 <= fy <= win.y1 + 1e-9:
            return 1.0
        dist = min(abs(fy - win.y0), abs(fy - win.y1))
        return max(0.0, 1.0 - dist * 4.0)
    if win.x0 - 1e-9 <= fx <= win.x1 + 1e-9:
        return 1.0
    dist = min(abs(fx - win.x0), abs(fx - win.x1))
    return max(0.0, 1.0 - dist * 4.0)


def _profile_as_asset(profile: dict) -> dict:
    ar = float(profile["aspect"])
    # Synthetic pixel size preserving aspect
    w = 1600.0
    h = w / ar
    fx, fy = profile.get("focal") or (0.5, 0.45)
    asset: dict = {
        "width": w,
        "height": h,
        "focalPoint": {"x": float(fx), "y": float(fy)},
        "tags": list(profile.get("tags") or []),
    }
    faces = profile.get("faces") or ()
    if faces:
        asset["faces"] = [
            {"x": f.x, "y": f.y, "w": f.w, "h": f.h}
            for f in faces
            if isinstance(f, NormBox)
        ]
    protect = profile.get("protect")
    if isinstance(protect, NormBox):
        asset["protectBox"] = {
            "x": protect.x,
            "y": protect.y,
            "w": protect.w,
            "h": protect.h,
        }
    return asset


def _profile_saliency_retention(slot_ar: float, profile: dict) -> float:
    asset = _profile_as_asset(profile)
    if asset.get("faces") or asset.get("protectBox"):
        solved = solve_slot_focal(asset, slot_ar)
        if solved.safety.face_clipped:
            return 0.0
        return float(solved.safety.protect_containment)
    fx, fy = profile.get("focal") or (0.5, 0.45)
    return _cover_focal_retention(
        slot_ar, float(profile["aspect"]), focal_x=float(fx), focal_y=float(fy)
    )


def _profile_face_clipped(slot_ar: float, profile: dict) -> bool:
    asset = _profile_as_asset(profile)
    if not (asset.get("faces") or asset.get("protectBox")):
        return False
    solved = solve_slot_focal(asset, slot_ar)
    return bool(solved.safety.face_clipped)


def _worst_saliency_for_slot(slot_ar: float, role: str = "") -> float:
    profiles = _profiles_for_slot(slot_ar, role)
    return min(_profile_saliency_retention(slot_ar, profile) for profile in profiles)


def _worst_face_clipped_for_slot(slot_ar: float, role: str = "") -> bool:
    profiles = _profiles_for_slot(slot_ar, role)
    return any(_profile_face_clipped(slot_ar, profile) for profile in profiles)


# Role-aware fit-distance ceiling. The GA corpus tops out at 0.75 (the legacy
# reverse-migrated ``screen-portrait-3`` — three portraits crammed into a 9:16
# stage, whose hard center crop is verified focal-safe: saliency retention 1.0).
# 0.80 sits just above that baseline so the gate ratchets against genuinely new
# geometry regressions (a slot grossly mismatched to its role) while accepting
# the existing intentional dense grids.
GEOMETRY_WARN_THRESHOLD = 0.80


def run_probe_for_template(
    engine: LayoutTemplateEngine,
    template_id: str,
    *,
    warn_threshold: float = GEOMETRY_WARN_THRESHOLD,
    saliency_warn_threshold: float = 0.55,
) -> dict:
    """Geometry + saliency + face-clip probe for one template (admission S5)."""
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
        probe_ars = _role_probe_aspects(slot.role)
        worst = max(_probe_fit_distance(slot.display_aspect, ar) for ar in probe_ars)
        worst_retention = _worst_saliency_for_slot(slot.display_aspect, slot.role)
        face_clipped = _worst_face_clipped_for_slot(slot.display_aspect, slot.role)
        results.append(
            {
                "templateId": template_id,
                "slot": slot.index,
                "role": slot.role,
                "slotAspect": round(slot.display_aspect, 4),
                "worstProbeDistance": round(worst, 4),
                "worstSaliencyRetention": round(worst_retention, 4),
                "worstFaceClipped": bool(face_clipped),
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
        if face_clipped:
            warnings.append(
                f"{template_id} slot {slot.index} worstFaceClipped=true "
                f"(person-safe cover infeasible for at least one probe profile)"
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
    warn_threshold: float = GEOMETRY_WARN_THRESHOLD,
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
