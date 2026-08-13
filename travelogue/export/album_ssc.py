"""Album subject-safe crop (SSC) — after slot fill, before render.

L1 failure chain (D-AEL-07 / 21): heterogeneous-AR same-card swap → contain.
L2: same-slot-count mature template swap; punch-in when crop.tighten.
Equal-AR grids skip AR-swap (AC-AEL-25). Default loop never calls mosaic_judge.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.config.album_editorial import EffectiveAel
from travelogue.export.card_grouper import CardPlan, assign_photos_to_slots
from travelogue.export.card_renderer import SlotCropHint
from travelogue.export.card_templates import CARD_TEMPLATES, CardTemplate
from travelogue.layout_engine.crop_solver import (
    CROP_RISK_CONTAIN_THRESHOLD,
    any_face_outside,
    cheap_crop_risk,
    crop_risk_for_pair,
    group_face_count,
    solve_slot_focal,
    solve_slot_tighten,
)

_AR_EPS = 0.05

AssetLookup = Callable[[Path], dict[str, Any] | None]


@dataclass(frozen=True)
class CardSscResult:
    photos: tuple[Path, ...]
    hints: tuple[SlotCropHint, ...]
    template: CardTemplate


def slots_are_equal_ar(template: CardTemplate, *, eps: float = _AR_EPS) -> bool:
    ars = [float(s.display_aspect) for s in template.slots]
    if len(ars) <= 1:
        return True
    return (max(ars) - min(ars)) <= eps


def _asset_for(path: Path, lookup: AssetLookup | None) -> dict[str, Any] | None:
    if lookup is None:
        return None
    asset = lookup(path)
    return asset if isinstance(asset, dict) else None


def _pair_is_unsafe(
    asset: dict[str, Any] | None,
    slot_ar: float,
    ael: EffectiveAel,
    *,
    risk: float | None = None,
    face_outside: bool | None = None,
    has_faces: bool | None = None,
) -> bool:
    if face_outside is None or has_faces is None or risk is None:
        solved = solve_slot_focal(asset, slot_ar)
        face_outside = any_face_outside(asset, solved.window)
        has_faces = bool(solved.safety.face_count) or group_face_count(asset) > 0
        risk = crop_risk_for_pair(asset, slot_ar)
    if ael.face_hard_gate and face_outside:
        return True
    if not has_faces and float(risk) >= CROP_RISK_CONTAIN_THRESHOLD:
        return True
    return False


def _evaluate_slot(
    asset: dict[str, Any] | None,
    slot_ar: float,
    *,
    deadline: float | None,
) -> tuple[bool, float, tuple[float, float], bool]:
    """Return ``(face_outside, risk, focal, skipped_solve)``."""
    now = time.monotonic()
    has_face_signal = group_face_count(asset) > 0
    cheap = cheap_crop_risk(asset, slot_ar)
    over_budget = deadline is not None and now >= deadline
    high_priority = has_face_signal or cheap >= CROP_RISK_CONTAIN_THRESHOLD
    if over_budget and not high_priority:
        focal = (0.5, 0.45)
        if isinstance(asset, dict):
            fp = asset.get("focalPoint") or {}
            if isinstance(fp, dict):
                try:
                    focal = (float(fp.get("x", 0.5)), float(fp.get("y", 0.45)))
                except (TypeError, ValueError):
                    pass
        return False, cheap, focal, True
    solved = solve_slot_focal(asset, slot_ar)
    risk = crop_risk_for_pair(asset, slot_ar)
    return (
        any_face_outside(asset, solved.window),
        float(risk),
        (solved.focal_x, solved.focal_y),
        False,
    )


def any_unsafe_slots(
    photos: Sequence[Path],
    template: CardTemplate,
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None,
) -> bool:
    return any(_unsafe_flags(photos, template, lookup, ael, deadline=deadline))


def _unsafe_flags(
    photos: Sequence[Path],
    template: CardTemplate,
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None,
) -> list[bool]:
    flags: list[bool] = []
    for path, slot in zip(photos, template.slots, strict=True):
        asset = _asset_for(path, lookup)
        clipped, risk, _focal, _skipped = _evaluate_slot(
            asset, float(slot.display_aspect), deadline=deadline
        )
        flags.append(
            _pair_is_unsafe(
                asset,
                float(slot.display_aspect),
                ael,
                risk=risk,
                face_outside=clipped,
                has_faces=group_face_count(asset) > 0 or clipped,
            )
        )
    return flags


def _try_heterogeneous_rebind(
    photos: list[Path],
    template: CardTemplate,
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None,
) -> list[Path]:
    """Greedy pairwise swaps across different slot ARs (AC-AEL-04/05/25)."""
    n = len(photos)
    ars = [float(s.display_aspect) for s in template.slots]
    order = list(photos)
    improved = True
    while improved:
        improved = False
        flags = _unsafe_flags(order, template, lookup, ael, deadline=deadline)
        if not any(flags):
            return order
        for i in range(n):
            if not flags[i]:
                continue
            for j in range(n):
                if i == j:
                    continue
                if abs(ars[i] - ars[j]) <= _AR_EPS:
                    continue
                trial = list(order)
                trial[i], trial[j] = trial[j], trial[i]
                trial_flags = _unsafe_flags(
                    trial, template, lookup, ael, deadline=deadline
                )
                if sum(trial_flags) < sum(flags):
                    order = trial
                    improved = True
                    break
            if improved:
                break
    return order


def _try_same_count_rebind(
    photos: list[Path],
    template: CardTemplate,
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None,
) -> tuple[list[Path], CardTemplate]:
    """L2: swap to another mature template of the same slot count if safer."""
    flags = _unsafe_flags(photos, template, lookup, ael, deadline=deadline)
    best_n = sum(flags)
    if best_n == 0:
        return photos, template
    best_photos, best_t = photos, template
    for sib in CARD_TEMPLATES.values():
        if sib.slot_count != template.slot_count or sib.id == template.id:
            continue
        trial = assign_photos_to_slots(list(photos), sib)
        n_bad = sum(_unsafe_flags(trial, sib, lookup, ael, deadline=deadline))
        if n_bad < best_n:
            best_photos, best_t, best_n = trial, sib, n_bad
            if n_bad == 0:
                break
    return best_photos, best_t


def apply_card_ssc(
    plan: CardPlan,
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None = None,
    lock_template: bool = False,
) -> CardSscResult:
    """Reorder photos within one card and emit per-slot cover/contain hints.

    No-ops when ``ael.crop`` is false. L2 may replace ``plan.template`` with
    another mature template of the same slot count unless ``lock_template``
    (AEL L3 probes must not be swapped back into the mature library).
    """
    photos = list(plan.photos)
    template = plan.template
    n = len(photos)
    if n != template.slot_count:
        raise ValueError(
            f"album_ssc: template {template.id} expects "
            f"{template.slot_count} photos, got {n}"
        )
    if not ael.crop:
        return CardSscResult(
            photos=tuple(photos),
            hints=tuple(SlotCropHint() for _ in range(n)),
            template=template,
        )

    if not slots_are_equal_ar(template):
        photos = _try_heterogeneous_rebind(
            photos, template, lookup, ael, deadline=deadline
        )
    if ael.roles and not lock_template:
        photos, template = _try_same_count_rebind(
            photos, template, lookup, ael, deadline=deadline
        )

    hints: list[SlotCropHint] = []
    for path, slot in zip(photos, template.slots, strict=True):
        asset = _asset_for(path, lookup)
        slot_ar = float(slot.display_aspect)
        clipped, risk, focal, _skipped = _evaluate_slot(
            asset, slot_ar, deadline=deadline
        )
        unsafe = _pair_is_unsafe(
            asset,
            slot_ar,
            ael,
            risk=risk,
            face_outside=clipped,
            has_faces=group_face_count(asset) > 0 or clipped,
        )
        if unsafe and ael.contain_on_fail:
            hints.append(SlotCropHint(fit="contain", focal=focal))
        else:
            window = None
            if ael.tighten:
                tight = solve_slot_tighten(
                    asset, slot_ar, group_face_min=ael.group_face_min
                )
                if tight is not None:
                    win = tight.window
                    window = (win.x0, win.y0, win.x1, win.y1)
            hints.append(SlotCropHint(fit="cover", focal=focal, window=window))
    return CardSscResult(photos=tuple(photos), hints=tuple(hints), template=template)
