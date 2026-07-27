"""Mobile render transforms for screens engine (PRD portrait-row-editorial §5 · 4mix §12.4 · P2VF)."""

from __future__ import annotations

from travelogue.layout_engine.editorial.four_mix import PATTERN_EDITORIAL_4MIX
from travelogue.layout_engine.planner.portrait_2_picker import PORTRAIT_2_FAMILY_IDS

PORTRAIT_TRIPLE_MOBILE_EXPAND = frozenset(
    {"screen-portrait-3", "screen-portrait-3-editorial"}
)
PORTRAIT_PAIR_MOBILE_EXPAND = PORTRAIT_2_FAMILY_IDS

_MOBILE_EXPAND_STRIP_KEYS = frozenset(
    {
        "patternId",
        "slots",
        "layoutHint",
        "layoutGeometry",
        "copy",
        "copyMeta",
        "portrait2Picker",
    }
)


def should_expand_screens_for_mobile(
    export_layout: str,
    *,
    is_longshot: bool,
) -> bool:
    return export_layout == "mobile" and not is_longshot


def should_expand_portrait_triple_for_mobile(
    export_layout: str,
    *,
    is_longshot: bool,
) -> bool:
    """Backward-compatible alias."""
    return should_expand_screens_for_mobile(export_layout, is_longshot=is_longshot)


def expand_portrait_triple_screen(screen: dict) -> list[dict]:
    """One triple screen → three screen-portrait-1 (slot order preserved)."""
    slots = screen.get("slots") or []
    if len(slots) != 3:
        return [screen]
    base = {k: v for k, v in screen.items() if k not in _MOBILE_EXPAND_STRIP_KEYS}
    out: list[dict] = []
    for slot in slots:
        single = dict(base)
        single["patternId"] = "screen-portrait-1"
        single["slots"] = [dict(slot)]
        out.append(single)
    return out


def _single_pattern_for_4mix_slot(slot: dict, *, slot_index: int) -> str:
    role = str(slot.get("role") or "").strip()
    if role == "landscape":
        return "screen-landscape-1"
    if role == "portrait":
        return "screen-portrait-1"
    return "screen-landscape-1" if slot_index in (0, 3) else "screen-portrait-1"


def expand_editorial_4mix_screen(screen: dict) -> list[dict]:
    """One 4mix screen → four singles TL→TR→BL→BR (slot order preserved)."""
    slots = screen.get("slots") or []
    if len(slots) != 4:
        return [screen]
    base = {k: v for k, v in screen.items() if k not in _MOBILE_EXPAND_STRIP_KEYS}
    out: list[dict] = []
    for slot_index, slot in enumerate(slots):
        single = dict(base)
        single["patternId"] = _single_pattern_for_4mix_slot(slot, slot_index=slot_index)
        single["slots"] = [dict(slot)]
        out.append(single)
    return out


def expand_portrait_pair_screen(screen: dict) -> list[dict]:
    """P2VF D-08 · one portrait-2 family screen → two screen-portrait-1 (L→R)."""
    slots = screen.get("slots") or []
    if len(slots) != 2:
        return [screen]
    base = {k: v for k, v in screen.items() if k not in _MOBILE_EXPAND_STRIP_KEYS}
    out: list[dict] = []
    for slot in slots:
        single = dict(base)
        single["patternId"] = "screen-portrait-1"
        single["slots"] = [dict(slot)]
        out.append(single)
    return out


def expand_screens_for_mobile(screens: list[dict]) -> list[dict]:
    expanded: list[dict] = []
    for sc in screens:
        pid = str(sc.get("patternId") or "")
        slots = sc.get("slots") or []
        if pid in PORTRAIT_TRIPLE_MOBILE_EXPAND and len(slots) == 3:
            expanded.extend(expand_portrait_triple_screen(sc))
        elif pid == PATTERN_EDITORIAL_4MIX and len(slots) == 4:
            expanded.extend(expand_editorial_4mix_screen(sc))
        elif pid in PORTRAIT_PAIR_MOBILE_EXPAND and len(slots) == 2:
            expanded.extend(expand_portrait_pair_screen(sc))
        else:
            expanded.append(sc)
    return expanded


def expand_portrait_triples_for_mobile(screens: list[dict]) -> list[dict]:
    """Backward-compatible alias."""
    return expand_screens_for_mobile(screens)
