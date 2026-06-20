"""Mobile render transforms for screens engine (PRD portrait-row-editorial §5)."""

from __future__ import annotations

PORTRAIT_TRIPLE_MOBILE_EXPAND = frozenset(
    {"screen-portrait-3", "screen-portrait-3-editorial"}
)


def should_expand_portrait_triple_for_mobile(
    export_layout: str,
    *,
    is_longshot: bool,
) -> bool:
    return export_layout == "mobile" and not is_longshot


def expand_portrait_triple_screen(screen: dict) -> list[dict]:
    """One triple screen → three screen-portrait-1 (slot order preserved)."""
    slots = screen.get("slots") or []
    if len(slots) != 3:
        return [screen]
    base = {
        k: v
        for k, v in screen.items()
        if k not in ("patternId", "slots", "layoutHint", "layoutGeometry")
    }
    out: list[dict] = []
    for slot in slots:
        single = dict(base)
        single["patternId"] = "screen-portrait-1"
        single["slots"] = [dict(slot)]
        out.append(single)
    return out


def expand_portrait_triples_for_mobile(screens: list[dict]) -> list[dict]:
    expanded: list[dict] = []
    for sc in screens:
        pid = str(sc.get("patternId") or "")
        if pid in PORTRAIT_TRIPLE_MOBILE_EXPAND and len(sc.get("slots") or []) == 3:
            expanded.extend(expand_portrait_triple_screen(sc))
        else:
            expanded.append(sc)
    return expanded
