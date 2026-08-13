"""AEL L3 probe mix — allowlisted rectangular probes onto album_spread only.

``plan_cards`` still sees only the mature library. This module runs after
grouping: at most one probe per original spread, body share ≤ ``max_share``.
Empty allowlist is a no-op even when ``probes.enabled``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from travelogue.config.album_editorial import EffectiveAel
from travelogue.export.album_ssc import any_unsafe_slots, apply_card_ssc
from travelogue.export.card_grouper import CardPlan, assign_photos_to_slots, plan_cards
from travelogue.export.card_templates import PROBE_TEMPLATES, CardTemplate
from travelogue.layout_engine.crop_solver import group_face_count

AssetLookup = Callable[[Path], dict[str, Any] | None]
_log = logging.getLogger(__name__)

_SKINNY_PROBE_IDS = frozenset({"probe-tall", "probe-triptych"})


def is_probe_id(template_id: str) -> bool:
    return str(template_id) in PROBE_TEMPLATES


def _asset(path: Path, lookup: AssetLookup | None) -> dict[str, Any] | None:
    if lookup is None:
        return None
    asset = lookup(path)
    return asset if isinstance(asset, dict) else None


def _card_has_group(
    photos: Sequence[Path],
    lookup: AssetLookup | None,
    *,
    group_face_min: int,
) -> bool:
    return any(
        group_face_count(_asset(path, lookup)) >= group_face_min for path in photos
    )


def _mature_plans(photos: list[Path]) -> list[CardPlan]:
    """Re-chunk leftover photos through the mature library (any N is valid)."""
    if not photos:
        return []
    return plan_cards(photos, avoid_immediate_repeat=False)


def _allowlisted_probes(ael: EffectiveAel) -> list[CardTemplate]:
    out: list[CardTemplate] = []
    for pid in ael.allowlist:
        template = PROBE_TEMPLATES.get(str(pid))
        if template is not None:
            out.append(template)
    return out


def _probe_ssc_failed(
    ssc: Any,
    ael: EffectiveAel,
    lookup: AssetLookup | None,
    *,
    deadline: float | None,
) -> bool:
    """AC-AEL-15: cover still unsafe and contain is off → drop probe."""
    if not ael.crop or ael.contain_on_fail:
        return False
    return any_unsafe_slots(
        list(ssc.photos), ssc.template, lookup, ael, deadline=deadline
    )


def _ranked_probes(
    n: int,
    templates: Sequence[CardTemplate],
    used: set[str],
    *,
    photos: Sequence[Path],
    lookup: AssetLookup | None,
    group_face_min: int,
) -> list[CardTemplate]:
    has_group = _card_has_group(photos, lookup, group_face_min=group_face_min)
    eligible = []
    for template in templates:
        if template.slot_count > n:
            continue
        if has_group and template.id in _SKINNY_PROBE_IDS:
            continue
        eligible.append(template)
    eligible.sort(
        key=lambda t: (
            0 if t.id not in used else 1,
            0 if t.slot_count == n else 1,
            -t.slot_count,
        )
    )
    return eligible


def _split_photos(
    photos: list[Path],
    template: CardTemplate,
) -> tuple[list[Path], list[Path]]:
    k = template.slot_count
    chosen = list(photos[:k])
    rest = list(photos[k:])
    return chosen, rest


def try_probe_for_card(
    plan: CardPlan,
    templates: Sequence[CardTemplate],
    used: set[str],
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None,
) -> tuple[CardPlan, list[CardPlan]] | None:
    """Return ``(probe_plan, remainder_plans)`` or None if nothing fits."""
    photos = list(plan.photos)
    n = len(photos)
    for template in _ranked_probes(
        n,
        templates,
        used,
        photos=photos,
        lookup=lookup,
        group_face_min=ael.group_face_min,
    ):
        chosen, rest = _split_photos(photos, template)
        if len(chosen) != template.slot_count:
            continue
        try:
            probe_plan = CardPlan(
                template=template,
                photos=tuple(assign_photos_to_slots(chosen, template)),
            )
            ssc = apply_card_ssc(
                probe_plan, lookup, ael, deadline=deadline, lock_template=True
            )
            if _probe_ssc_failed(ssc, ael, lookup, deadline=deadline):
                continue
            committed = CardPlan(template=ssc.template, photos=ssc.photos)
            return committed, _mature_plans(rest)
        except Exception:
            _log.debug("skip probe %s on %s", template.id, plan.template.id, exc_info=True)
            continue
    return None


def mix_probe_cards(
    plans: list[CardPlan],
    lookup: AssetLookup | None,
    ael: EffectiveAel,
    *,
    deadline: float | None = None,
) -> list[CardPlan]:
    """Inject allowlisted probes. No-op when probes off or allowlist empty."""
    if not ael.probes or not ael.allowlist or ael.max_per_spread < 1:
        return plans
    templates = _allowlisted_probes(ael)
    if not templates:
        return plans
    max_total = int(len(plans) * float(ael.max_share))
    if max_total <= 0:
        return plans

    try:
        out: list[CardPlan] = []
        placed = 0
        used: set[str] = set()
        i = 0
        while i < len(plans):
            group = plans[i : i + 2]
            replaced = False
            for plan in group:
                if replaced or placed >= max_total:
                    out.append(plan)
                    continue
                fitted = try_probe_for_card(
                    plan,
                    templates,
                    used,
                    lookup,
                    ael,
                    deadline=deadline,
                )
                if fitted is None:
                    out.append(plan)
                    continue
                probe, extras = fitted
                out.append(probe)
                out.extend(extras)
                replaced = True
                placed += 1
                used.add(probe.template.id)
            i += 2
        return out
    except Exception:
        _log.exception("mix_probe_cards failed; keeping mature plans")
        return plans
