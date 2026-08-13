"""Person-safe cover crop solver · CSS object-fit:cover + object-position consistent.

Maps asset protect/face boxes into a slot's cover window and solves the
``object-position`` focal so faces stay intact. Falls back to centering the
protect box when no feasible offset exists.

Contain flip is a last resort for **face** clipping only — oversized half-body
``protectBox`` infeasibility must not destroy full-bleed cover contracts
(e.g. ``screen-landscape-1`` 单横铺满).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# Patterns whose product contract is full-bleed / strip cover (YAML fit:cover).
# Never flip to contain: letterboxing + contain-collapse CSS creates large paper
# margins that violate single-landscape and landscape-stack strip contracts.
_COVER_BLEED_NO_CONTAIN_FLIP: frozenset[str] = frozenset(
    {
        "screen-landscape-1",
        "screen-panorama-1",
        "screen-tall-1",
        # CSS-primary stacks: each strip uses --slot-aspect ≈ asset AR (not YAML
        # stage/rows ultra-wide 3.56). Contain flip + collapse → centered strips
        # with huge paper margins (demo-d6697c8dca landscape-2 dogfood).
        "screen-landscape-2",
        "screen-landscape-3",
    }
)

# Stack templates whose rendered slot AR follows the asset (render context
# ``--slot-aspect``), not ``slot_display_aspect`` from YAML stage×rows.
_CSS_NATIVE_SLOT_ASPECT_PATTERNS: frozenset[str] = frozenset(
    {
        "screen-landscape-2",
        "screen-landscape-3",
    }
)

# Shared crop_risk proxy (MSA PRD §6.5 / AEL D-AEL-11). Authority lives here;
# mosaic.msa_fit re-exports. Album export must import this module, not mosaic.
_ALPHA_MISMATCH = 0.85
_BETA_FOCAL_EDGE = 0.35
_GAMMA_PERSON = 0.55
_FOCAL_EDGE_MARGIN = 0.12
CROP_RISK_CONTAIN_THRESHOLD = 0.55


@dataclass(frozen=True)
class NormBox:
    """Normalized axis-aligned box in image coords (x,y,w,h) with values in 0..1."""

    x: float
    y: float
    w: float
    h: float

    @property
    def x1(self) -> float:
        return self.x + self.w

    @property
    def y1(self) -> float:
        return self.y + self.h

    @property
    def area(self) -> float:
        return max(0.0, self.w) * max(0.0, self.h)

    @property
    def cx(self) -> float:
        return self.x + self.w * 0.5

    @property
    def cy(self) -> float:
        return self.y + self.h * 0.5


@dataclass(frozen=True)
class CoverWindow:
    """Visible region of the asset under object-fit:cover (normalized 0..1)."""

    x0: float
    y0: float
    x1: float
    y1: float
    visible_w: float
    visible_h: float
    axis: str  # "x" | "y" | "none"

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class CropSafety:
    face_clipped: bool
    protect_containment: float
    has_person: bool
    face_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "faceClipped": self.face_clipped,
            "protectContainment": round(self.protect_containment, 4),
            "hasPerson": self.has_person,
            "faceCount": self.face_count,
        }


@dataclass(frozen=True)
class CropSolveResult:
    focal_x: float
    focal_y: float
    feasible: bool
    safety: CropSafety
    window: CoverWindow

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": round(self.focal_x, 6),
            "y": round(self.focal_y, 6),
            "feasible": self.feasible,
            "safety": self.safety.to_dict(),
        }


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _as_box(raw: Mapping[str, Any] | NormBox | None) -> NormBox | None:
    if raw is None:
        return None
    if isinstance(raw, NormBox):
        return raw
    try:
        x = float(raw.get("x", 0.0))
        y = float(raw.get("y", 0.0))
        w = float(raw.get("w", 0.0))
        h = float(raw.get("h", 0.0))
    except (TypeError, ValueError, AttributeError):
        return None
    if w <= 0 or h <= 0:
        return None
    x = _clamp01(x)
    y = _clamp01(y)
    w = min(w, 1.0 - x)
    h = min(h, 1.0 - y)
    if w <= 0 or h <= 0:
        return None
    return NormBox(x=x, y=y, w=w, h=h)


def _intersect_area(a: NormBox, win: CoverWindow) -> float:
    ix0 = max(a.x, win.x0)
    iy0 = max(a.y, win.y0)
    ix1 = min(a.x1, win.x1)
    iy1 = min(a.y1, win.y1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return (ix1 - ix0) * (iy1 - iy0)


def _fully_inside(box: NormBox, win: CoverWindow, *, eps: float = 1e-6) -> bool:
    return (
        box.x >= win.x0 - eps
        and box.y >= win.y0 - eps
        and box.x1 <= win.x1 + eps
        and box.y1 <= win.y1 + eps
    )


def _partially_outside(box: NormBox, win: CoverWindow, *, eps: float = 1e-6) -> bool:
    """True when the box overlaps the window but is not fully contained (half-face)."""
    inter = _intersect_area(box, win)
    if inter <= eps:
        return False
    return not _fully_inside(box, win, eps=eps)


def any_face_outside(asset: Mapping[str, Any] | None, window: CoverWindow) -> bool:
    """True if any face box is not fully inside ``window`` (includes fully cropped-away).

    Stricter than ``CropSafety.face_clipped``, which only flags *partial* clips.
    Album SSC uses this for the face/group hard gate (AC-AEL-04/05).
    """
    return any(not _fully_inside(f, window) for f in faces_from_asset(asset))


def cover_window(
    slot_ar: float,
    asset_ar: float,
    px: float = 0.5,
    py: float = 0.45,
) -> CoverWindow:
    """Visible cover window matching CSS ``object-position: px% py%`` semantics.

    When ``slot_ar >= asset_ar`` the image fills width and crops vertically:
    ``y0 = py * (1 - vh)``. Otherwise it fills height and crops horizontally:
    ``x0 = px * (1 - vw)``.
    """
    px = _clamp01(px)
    py = _clamp01(py)
    if slot_ar <= 0 or asset_ar <= 0:
        return CoverWindow(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, "none")
    if abs(slot_ar - asset_ar) < 1e-9:
        return CoverWindow(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, "none")
    if slot_ar >= asset_ar:
        vh = asset_ar / slot_ar
        vh = _clamp01(vh)
        slack = 1.0 - vh
        y0 = py * slack
        return CoverWindow(0.0, y0, 1.0, y0 + vh, 1.0, vh, "y")
    vw = slot_ar / asset_ar
    vw = _clamp01(vw)
    slack = 1.0 - vw
    x0 = px * slack
    return CoverWindow(x0, 0.0, x0 + vw, 1.0, vw, 1.0, "x")


def union_boxes(boxes: Sequence[NormBox]) -> NormBox | None:
    if not boxes:
        return None
    x0 = min(b.x for b in boxes)
    y0 = min(b.y for b in boxes)
    x1 = max(b.x1 for b in boxes)
    y1 = max(b.y1 for b in boxes)
    return NormBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def faces_from_asset(asset: Mapping[str, Any] | None) -> list[NormBox]:
    """Normalized face boxes: ``faces`` → union from ``salientBox``."""
    if not asset:
        return []
    raw_faces = asset.get("faces")
    out: list[NormBox] = []
    if isinstance(raw_faces, (list, tuple)):
        for item in raw_faces:
            if isinstance(item, Mapping):
                box = _as_box(item)
                if box is not None:
                    out.append(box)
            elif isinstance(item, (list, tuple)) and len(item) >= 4:
                # Pixel boxes require width/height — skip unless already normalized-looking
                try:
                    x, y, w, h = (float(item[0]), float(item[1]), float(item[2]), float(item[3]))
                except (TypeError, ValueError):
                    continue
                if max(x, y, w, h) <= 1.0 + 1e-6:
                    box = _as_box({"x": x, "y": y, "w": w, "h": h})
                    if box is not None:
                        out.append(box)
    if out:
        return out
    sb = _as_box(asset.get("salientBox") if isinstance(asset.get("salientBox"), Mapping) else None)
    return [sb] if sb is not None else []


def protect_box_from_asset(asset: Mapping[str, Any] | None) -> NormBox | None:
    """Compatibility chain: protectBox → faces union → salientBox → None."""
    if not asset:
        return None
    pb = asset.get("protectBox")
    if isinstance(pb, Mapping):
        box = _as_box(pb)
        if box is not None:
            return box
    faces = faces_from_asset(asset)
    if faces:
        return union_boxes(faces)
    return _as_box(asset.get("salientBox") if isinstance(asset.get("salientBox"), Mapping) else None)


def asset_aspect(asset: Mapping[str, Any] | None) -> float | None:
    if not asset:
        return None
    for wk, hk in (("width", "height"), ("nativeWidth", "nativeHeight"), ("w", "h")):
        try:
            w = float(asset.get(wk))  # type: ignore[arg-type]
            h = float(asset.get(hk))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if w > 0 and h > 0:
            return w / h
    return None


def prefer_focal_from_asset(asset: Mapping[str, Any] | None) -> tuple[float, float]:
    if not asset:
        return 0.5, 0.45
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5)) if isinstance(fp, Mapping) else 0.5
        fy = float(fp.get("y", 0.45)) if isinstance(fp, Mapping) else 0.45
    except (TypeError, ValueError):
        return 0.5, 0.45
    return _clamp01(fx), _clamp01(fy)


def crop_safety(
    *,
    window: CoverWindow,
    faces: Sequence[NormBox],
    protect: NormBox | None,
) -> CropSafety:
    has_person = bool(faces) or protect is not None
    face_clipped = any(_partially_outside(f, window) for f in faces)
    if protect is None or protect.area <= 1e-12:
        containment = 1.0 if not has_person else (0.0 if face_clipped else 1.0)
    else:
        containment = _intersect_area(protect, window) / protect.area
    return CropSafety(
        face_clipped=bool(face_clipped),
        protect_containment=_clamp01(containment),
        has_person=has_person,
        face_count=len(faces),
    )


def _solve_axis(
    *,
    protect: NormBox,
    visible: float,
    low: float,
    high: float,
    prefer: float,
) -> tuple[float, bool]:
    """Solve position ``p`` so protect ``[low, high]`` fits in window of size ``visible``.

    Window start = ``p * (1 - visible)``. Returns ``(p, feasible)``.
    """
    slack = 1.0 - visible
    if slack <= 1e-9:
        return _clamp01(prefer), True
    # p * slack <= low  →  p <= low / slack
    # p * slack >= high - visible  →  p >= (high - visible) / slack
    p_min = (high - visible) / slack
    p_max = low / slack
    if p_min > p_max + 1e-9:
        # Infeasible: center protect in the window
        center = (low + high) * 0.5
        # window mid = p*slack + visible/2  == center
        p = (center - visible * 0.5) / slack
        return _clamp01(p), False
    p_min = max(0.0, p_min)
    p_max = min(1.0, p_max)
    if p_min > p_max:
        return _clamp01((p_min + p_max) * 0.5), False
    prefer = _clamp01(prefer)
    if prefer < p_min:
        return p_min, True
    if prefer > p_max:
        return p_max, True
    return prefer, True


def solve_slot_focal(
    asset: Mapping[str, Any] | None,
    slot_ar: float,
    *,
    prefer: tuple[float, float] | None = None,
) -> CropSolveResult:
    """Solve cover object-position so the protect/face region stays intact."""
    prefer_xy = prefer if prefer is not None else prefer_focal_from_asset(asset)
    px0, py0 = _clamp01(prefer_xy[0]), _clamp01(prefer_xy[1])
    ar = asset_aspect(asset)
    faces = faces_from_asset(asset)
    protect = protect_box_from_asset(asset)

    if ar is None or slot_ar <= 0:
        win = cover_window(1.0, 1.0, px0, py0)
        safety = crop_safety(window=win, faces=faces, protect=protect)
        return CropSolveResult(px0, py0, True, safety, win)

    if protect is None and not faces:
        win = cover_window(slot_ar, ar, px0, py0)
        safety = crop_safety(window=win, faces=faces, protect=protect)
        return CropSolveResult(px0, py0, True, safety, win)

    target = protect if protect is not None else union_boxes(faces)
    if target is None:
        raise RuntimeError("crop_solver: protect/faces union unexpectedly empty")

    if slot_ar >= ar:
        vh = ar / slot_ar
        vh = _clamp01(vh)
        py, feasible = _solve_axis(
            protect=target,
            visible=vh,
            low=target.y,
            high=target.y1,
            prefer=py0,
        )
        px = px0
    else:
        vw = slot_ar / ar
        vw = _clamp01(vw)
        px, feasible = _solve_axis(
            protect=target,
            visible=vw,
            low=target.x,
            high=target.x1,
            prefer=px0,
        )
        py = py0

    win = cover_window(slot_ar, ar, px, py)
    safety = crop_safety(window=win, faces=faces, protect=protect)
    return CropSolveResult(px, py, feasible, safety, win)


def focal_near_edge(asset: Mapping[str, Any] | None, margin: float = _FOCAL_EDGE_MARGIN) -> bool:
    if not asset:
        return False
    fp = asset.get("focalPoint") or {}
    if not isinstance(fp, Mapping):
        return False
    x, y = fp.get("x"), fp.get("y")
    if x is None or y is None:
        return False
    try:
        xf, yf = float(x), float(y)
    except (TypeError, ValueError):
        return False
    return bool(xf < margin or xf > 1.0 - margin or yf < margin or yf > 1.0 - margin)


def aspect_mismatch(photo_r: float, slot_r: float) -> float:
    """``1 - min/max`` in [0, 1]."""
    if photo_r <= 0 or slot_r <= 0:
        return 0.0
    return 1.0 - (min(photo_r, slot_r) / max(photo_r, slot_r))


def group_face_count(asset: Mapping[str, Any] | None) -> int:
    """D-AEL-28: ``max(quality.faceCount, len(faces))``. Both 0 → not a group."""
    if not asset:
        return 0
    n_faces = 0
    raw_faces = asset.get("faces")
    if isinstance(raw_faces, (list, tuple)):
        n_faces = len(raw_faces)
    qn = 0
    quality = asset.get("quality")
    if isinstance(quality, Mapping):
        try:
            qn = int(quality.get("faceCount") or 0)
        except (TypeError, ValueError):
            qn = 0
    return max(qn, n_faces)


def crop_risk_for_pair(
    asset: Mapping[str, Any] | None,
    slot_display_aspect: float,
    *,
    alpha: float = _ALPHA_MISMATCH,
    beta: float = _BETA_FOCAL_EDGE,
    gamma: float = _GAMMA_PERSON,
) -> float:
    """Cover-crop risk proxy (MSA PRD §6.5) + person-safe face IoU after solve."""
    pr = asset_aspect(asset)
    if pr is None or slot_display_aspect <= 0:
        return 0.0
    mismatch = aspect_mismatch(pr, float(slot_display_aspect))
    edge = 1.0 if asset is not None and focal_near_edge(asset) else 0.0
    base = alpha * mismatch + beta * edge

    solved = solve_slot_focal(asset, float(slot_display_aspect))
    safety = solved.safety
    # Hard floor only when faces are actually clipped after solve. Oversized
    # half-body protect infeasibility is a soft signal (protectContainment),
    # not a contain mandate — otherwise 3:2 heroes in 16:9 bleed get letterboxed.
    if safety.face_clipped:
        return round(_clamp01(max(base, 0.92)), 4)
    person_pen = 0.0
    if safety.has_person:
        person_pen = gamma * (1.0 - float(safety.protect_containment))
        if not solved.feasible:
            person_pen = max(person_pen, 0.45)
    return round(_clamp01(base + person_pen), 4)


def cheap_crop_risk(asset: Mapping[str, Any] | None, slot_display_aspect: float) -> float:
    """AR-mismatch + focal-edge only (no solve). Used when SSC hits max_solve_ms."""
    pr = asset_aspect(asset)
    if pr is None or slot_display_aspect <= 0:
        return 0.0
    mismatch = aspect_mismatch(pr, float(slot_display_aspect))
    edge = 1.0 if asset is not None and focal_near_edge(asset) else 0.0
    return round(_clamp01(_ALPHA_MISMATCH * mismatch + _BETA_FOCAL_EDGE * edge), 4)


def _allow_contain_flip(screen: Mapping[str, Any] | None) -> bool:
    """False for full-bleed single-landscape / stack strips that must stay cover."""
    pid = str((screen or {}).get("patternId") or "")
    return pid not in _COVER_BLEED_NO_CONTAIN_FLIP


def css_native_slot_aspect(
    pattern_id: str,
    asset: Mapping[str, Any] | None,
) -> float | None:
    """Slot AR used by CSS for CSS-primary stack strips (``--slot-aspect``).

    ``screen-landscape-2/3`` render each strip at the asset's native AR, not the
    YAML stage×rows ultra-wide (~3.56). Crop math must use the same AR or it
    false-positive faceClipped and flips to contain.
    """
    if str(pattern_id or "") not in _CSS_NATIVE_SLOT_ASPECT_PATTERNS:
        return None
    return asset_aspect(asset)


def apply_slot_crop_focals(
    screen: dict[str, Any],
    *,
    assets_map: Mapping[str, Any] | None = None,
    contain_on_unsafe: bool = True,
) -> list[dict[str, Any]]:
    """Mutate ``slots[].cropFocal`` (+ ``cropSafety``) for cover slots.

    When ``contain_on_unsafe`` is true and the solved cover still **clips a face**,
    flip ``fit`` to ``contain`` (except full-bleed / landscape-stack cover contracts).

    Protect-box infeasibility alone does **not** flip: half-body pads often
    exceed a narrow cover window while faces still fit after solve.
    """
    assets_map = assets_map or {}
    allow_flip = contain_on_unsafe and _allow_contain_flip(screen)
    pattern_id = str(screen.get("patternId") or "")
    summaries: list[dict[str, Any]] = []
    for slot in screen.get("slots") or []:
        if not isinstance(slot, dict):
            continue
        fit = str(slot.get("fit") or "cover").lower()
        try:
            sr = float(slot.get("displayAspect") or 0.0)
        except (TypeError, ValueError):
            sr = 0.0
        aid = slot.get("assetId")
        asset = assets_map.get(aid) if aid else None
        asset_m = asset if isinstance(asset, Mapping) else None

        native = css_native_slot_aspect(pattern_id, asset_m)
        if native is not None and native > 0:
            sr = float(native)
            slot["displayAspect"] = round(sr, 4)

        if fit != "cover" or sr <= 0 or asset_m is None:
            slot.pop("cropFocal", None)
            slot.pop("cropSafety", None)
            summaries.append(
                {
                    "slot": slot.get("slot"),
                    "assetId": aid,
                    "skipped": True,
                    "reason": "not_cover" if fit != "cover" else "missing",
                }
            )
            continue

        result = solve_slot_focal(asset_m, sr)
        slot["cropFocal"] = {"x": round(result.focal_x, 6), "y": round(result.focal_y, 6)}
        slot["cropSafety"] = result.safety.to_dict()
        # Drop stale flip flags when re-solving a previously flipped slot.
        slot.pop("cropContain", None)
        flipped = False
        if allow_flip and result.safety.face_clipped and not slot.get("msaContain"):
            slot["fit"] = "contain"
            slot["cropContain"] = True
            flipped = True
        summaries.append(
            {
                "slot": slot.get("slot"),
                "assetId": aid,
                "cropFocal": dict(slot["cropFocal"]),
                "feasible": result.feasible,
                "safety": result.safety.to_dict(),
                "containFlipped": flipped,
            }
        )
    return summaries


_TIGHTEN_HEADROOM = 0.35
_TIGHTEN_FEET_FACE_H = 6.0
_TIGHTEN_BUST_BELOW = 1.8
_TIGHTEN_SIDE = 0.4


def _keep_feet_box(asset: Mapping[str, Any] | None) -> NormBox | None:
    faces = faces_from_asset(asset)
    if not faces:
        return None
    fu = union_boxes(faces)
    if fu is None:
        return None
    protect = protect_box_from_asset(asset)
    salient = None
    if asset is not None:
        salient = _as_box(
            asset.get("salientBox") if isinstance(asset.get("salientBox"), Mapping) else None
        )
    y0 = max(0.0, fu.y - _TIGHTEN_HEADROOM * fu.h)
    y1 = min(1.0, fu.y1 + _TIGHTEN_FEET_FACE_H * fu.h)
    x0 = max(0.0, fu.x - _TIGHTEN_SIDE * fu.w)
    x1 = min(1.0, fu.x1 + _TIGHTEN_SIDE * fu.w)
    extra = protect if protect is not None else salient
    if extra is not None:
        y1 = min(1.0, max(y1, extra.y1))
        x0 = min(x0, extra.x)
        x1 = max(x1, extra.x1)
    if x1 <= x0 or y1 <= y0:
        return None
    return NormBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def _bust_box(asset: Mapping[str, Any] | None) -> NormBox | None:
    faces = faces_from_asset(asset)
    if not faces:
        return None
    fu = union_boxes(faces)
    if fu is None:
        return None
    y0 = max(0.0, fu.y - 0.4 * fu.h)
    y1 = min(1.0, fu.y1 + _TIGHTEN_BUST_BELOW * fu.h)
    x0 = max(0.0, fu.x - 0.45 * fu.w)
    x1 = min(1.0, fu.x1 + 0.45 * fu.w)
    if x1 <= x0 or y1 <= y0:
        return None
    return NormBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def tightest_window_for_box(
    box: NormBox | None,
    slot_ar: float,
    asset_ar: float | None,
) -> CoverWindow | None:
    """Smallest slot-AR rectangle in normalized image space that contains ``box``."""
    if box is None or slot_ar <= 0 or asset_ar is None or asset_ar <= 0:
        return None
    if box.w <= 0 or box.h <= 0:
        return None
    ratio = slot_ar / asset_ar
    if ratio <= 0:
        return None
    if box.w / box.h < ratio:
        ww, wh = box.h * ratio, box.h
    else:
        ww, wh = box.w, box.w / ratio
    if ww > 1.0 or wh > 1.0:
        scale = min(1.0 / ww, 1.0 / wh)
        ww *= scale
        wh *= scale
        if ww + 1e-6 < box.w or wh + 1e-6 < box.h:
            return None
    x0 = min(max(0.0, box.cx - ww / 2.0), 1.0 - ww)
    y0 = min(max(0.0, box.cy - wh / 2.0), 1.0 - wh)
    if box.x < x0:
        x0 = max(0.0, min(box.x, 1.0 - ww))
    if box.x1 > x0 + ww:
        x0 = max(0.0, min(box.x1 - ww, 1.0 - ww))
    if box.y < y0:
        y0 = max(0.0, min(box.y, 1.0 - wh))
    if box.y1 > y0 + wh:
        y0 = max(0.0, min(box.y1 - wh, 1.0 - wh))
    win = CoverWindow(x0, y0, x0 + ww, y0 + wh, ww, wh, "tight")
    if not _fully_inside(box, win):
        return None
    return win


@dataclass(frozen=True)
class TightenResult:
    window: CoverWindow
    mode: str  # "keep_feet" | "bust"


def solve_slot_tighten(
    asset: Mapping[str, Any] | None,
    slot_ar: float,
    *,
    group_face_min: int = 3,
) -> TightenResult | None:
    """Punch-in: keep-feet window first, bust fallback (D-AEL-32).

    Groups do not punch in. If L1 cover already clips a face, return None
    so SSC contain/swap owns the slot.
    """
    if group_face_count(asset) >= max(1, int(group_face_min)):
        return None
    if not faces_from_asset(asset):
        return None
    cover = solve_slot_focal(asset, slot_ar)
    if any_face_outside(asset, cover.window):
        return None
    ar = asset_aspect(asset)
    cover_area = cover.window.w * cover.window.h
    feet_win = tightest_window_for_box(_keep_feet_box(asset), slot_ar, ar)
    if (
        feet_win is not None
        and not any_face_outside(asset, feet_win)
        and (feet_win.w * feet_win.h) < cover_area - 1e-6
    ):
        return TightenResult(window=feet_win, mode="keep_feet")
    bust_win = tightest_window_for_box(_bust_box(asset), slot_ar, ar)
    if (
        bust_win is not None
        and not any_face_outside(asset, bust_win)
        and (bust_win.w * bust_win.h) < cover_area - 1e-6
    ):
        return TightenResult(window=bust_win, mode="bust")
    return None
