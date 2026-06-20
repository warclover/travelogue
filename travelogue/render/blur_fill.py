"""Blurred letterbox fill when contain leaves visible margins (PRD §3.4 · R-P16-15)."""

from __future__ import annotations

DEFAULT_STAGE_ASPECT = 16 / 9
# Relative |ΔAR| / max(AR) above which contain shows visible pillar/letter bands.
LETTERBOX_AR_THRESHOLD = 0.035

# Single-slot patterns whose contain path shrinks slot height but the screen
# stays full content-rail width — max-height cap can still leave pillar bands.
_VH_CAP_BLUR_PATTERNS = frozenset({"screen-portrait-1", "screen-plate"})
_INTRINSIC_CONTAIN_HINTS = frozenset(
    {"person-pair", "person-triple", "portrait-row-editorial"}
)


def parse_aspect_ratio(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v if v > 0 else None
    text = str(value).strip().replace(":", "/")
    if not text:
        return None
    if "/" in text:
        parts = [p.strip() for p in text.split("/", 1)]
        if len(parts) == 2:
            try:
                num, den = float(parts[0]), float(parts[1])
                if num > 0 and den > 0:
                    return num / den
            except ValueError:
                return None
    try:
        v = float(text)
        return v if v > 0 else None
    except ValueError:
        return None


def resolve_stage_aspect_ratio(
    *,
    layout_geo: dict,
    viewport_fit: bool,
    screen_aspect_css: str | None,
    skip_stage_aspect: bool,
    layout_hint: str | None = None,
) -> float:
    """Effective stage w/h used for letterbox prediction."""
    if (layout_hint or "").strip() == "person-grid-8":
        return DEFAULT_STAGE_ASPECT
    if not skip_stage_aspect:
        if layout_geo.get("stageAspect"):
            parsed = parse_aspect_ratio(str(layout_geo["stageAspect"]))
            if parsed:
                return parsed
        if screen_aspect_css and not viewport_fit:
            parsed = parse_aspect_ratio(screen_aspect_css)
            if parsed:
                return parsed
    return DEFAULT_STAGE_ASPECT


def letterbox_expected(
    enclosure_ar: float,
    asset_ar: float,
    *,
    threshold: float = LETTERBOX_AR_THRESHOLD,
) -> bool:
    if enclosure_ar <= 0 or asset_ar <= 0:
        return False
    return abs(enclosure_ar - asset_ar) / max(enclosure_ar, asset_ar) > threshold


def uses_intrinsic_contain_layout(
    *,
    pattern_id: str,
    layout_hint: str | None,
    n_slots: int,
    export_layout: str,
    is_plate: bool,
) -> bool:
    """True when CSS shrinks grid tiles — contain leaves no slot-level bands."""
    hint = (layout_hint or "").strip()
    if hint in _INTRINSIC_CONTAIN_HINTS:
        return True
    if hint == "person-grid-8":
        return False
    if n_slots > 1:
        return True
    return False


def uses_vh_cap_pillarbox(
    *,
    pattern_id: str,
    export_layout: str,
    is_plate: bool,
    fit: str,
) -> bool:
    """Portrait singles on web: full-width screen + max-height cap → side bands."""
    if fit != "contain" or export_layout == "mobile":
        return False
    effective = "screen-plate" if is_plate else pattern_id
    return effective in _VH_CAP_BLUR_PATTERNS


def slot_enclosure_aspect_ratio(
    *,
    stage_ar: float,
    layout_hint: str | None,
    n_slots: int,
    grid_class: str,
) -> float:
    hint = (layout_hint or "").strip()
    if hint == "person-grid-8" or "portrait-2x4" in grid_class:
        # 4×2 grid on 16:9 → each cell w/4 × h/2 → AR = stage_ar / 2
        return stage_ar / 2.0
    return stage_ar


def should_blur_fill_slot(
    *,
    fit: str,
    asset: dict | None,
    pattern_id: str,
    layout_hint: str | None,
    n_slots: int,
    export_layout: str,
    grid_class: str,
    stage_ar: float,
    is_plate: bool,
    asset_aspect: float,
) -> bool:
    if fit != "contain" or not asset:
        return False
    if uses_intrinsic_contain_layout(
        pattern_id=pattern_id,
        layout_hint=layout_hint,
        n_slots=n_slots,
        export_layout=export_layout,
        is_plate=is_plate,
    ):
        return False
    if uses_vh_cap_pillarbox(
        pattern_id=pattern_id,
        export_layout=export_layout,
        is_plate=is_plate,
        fit=fit,
    ):
        return True
    enclosure = slot_enclosure_aspect_ratio(
        stage_ar=stage_ar,
        layout_hint=layout_hint,
        n_slots=n_slots,
        grid_class=grid_class,
    )
    return letterbox_expected(enclosure, asset_aspect)
