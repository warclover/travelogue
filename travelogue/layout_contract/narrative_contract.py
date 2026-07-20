"""LTN B1 / ADR-020 · Narrative Contract defaults on layoutScreen."""

from __future__ import annotations

from typing import Any, Literal

NarrativeRole = Literal[
    "plate",
    "hero_single",
    "stack",
    "pair",
    "mosaic_hero",
    "mosaic_flat",
    "breath",
]

NARRATIVE_ROLES: frozenset[str] = frozenset(
    {"plate", "hero_single", "stack", "pair", "mosaic_hero", "mosaic_flat", "breath"}
)

_PAIR_PATTERNS = frozenset(
    {
        "screen-portrait-2",
        "screen-landscape-2",
        "screen-square-2",
        "screen-portrait-2-landscape-2",
    }
)
_STACK_PATTERNS = frozenset(
    {
        "screen-portrait-3",
        "screen-portrait-3-editorial",
        "screen-landscape-3",
        "screen-square-3",
        "screen-portrait-1-landscape-2",
    }
)
_HERO_SINGLE_PATTERNS = frozenset(
    {
        "screen-portrait-1",
        "screen-landscape-1",
        "screen-square-1",
        "screen-panorama-1",
        "screen-tall-1",
        "screen-full-frame",
    }
)


def _pattern_has_main_role(pattern_id: str) -> bool:
    try:
        from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

        return ScreenLayoutPlannerState.pattern_has_main_role(pattern_id)
    except Exception:
        return "mosaic" in pattern_id and "hero" in pattern_id


def derive_narrative_role(pattern_id: str, *, slot_count: int = 0) -> NarrativeRole:
    pid = str(pattern_id or "")
    if pid == "screen-breath-pause" or "breath" in pid:
        return "breath"
    if pid in _HERO_SINGLE_PATTERNS or (slot_count == 1 and "mosaic" not in pid):
        return "hero_single"
    if pid in _PAIR_PATTERNS:
        return "pair"
    if pid in _STACK_PATTERNS:
        return "stack"
    if "mosaic" in pid:
        if _pattern_has_main_role(pid):
            return "mosaic_hero"
        return "mosaic_flat"
    return "plate"


def derive_preserve_group(pattern_id: str, *, slot_count: int = 0) -> bool:
    """ADR-020 D4 · mosaic / main-role screens default to preserving group feel."""
    pid = str(pattern_id or "")
    if not pid or "breath" in pid:
        return False
    if slot_count <= 1 and "mosaic" not in pid:
        return False
    if "mosaic" in pid:
        return True
    if _pattern_has_main_role(pid):
        return True
    return False


def derive_representative_asset_id(screen: dict[str, Any]) -> str | None:
    slots = [s for s in (screen.get("slots") or []) if isinstance(s, dict)]
    for sl in slots:
        if sl.get("role") == "main" and sl.get("assetId"):
            return str(sl["assetId"])
    for sl in slots:
        if sl.get("assetId"):
            return str(sl["assetId"])
    return None


def ensure_narrative_contract(
    screen: dict[str, Any],
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Fill Narrative Contract fields; explicit values win unless ``overwrite``.

    Safe for old trips (migration-on-read/write). Does not invent sceneId.
    """
    if not isinstance(screen, dict):
        return screen
    pid = str(screen.get("patternId") or "")
    slots = [s for s in (screen.get("slots") or []) if isinstance(s, dict)]
    n = len(slots)

    if overwrite or "narrativeRole" not in screen:
        screen["narrativeRole"] = derive_narrative_role(pid, slot_count=n)
    elif screen.get("narrativeRole") not in NARRATIVE_ROLES:
        screen["narrativeRole"] = derive_narrative_role(pid, slot_count=n)

    if overwrite or "preserveGroup" not in screen:
        screen["preserveGroup"] = derive_preserve_group(pid, slot_count=n)

    if overwrite or not screen.get("groupId"):
        sid = str(screen.get("screenId") or "").strip()
        if sid:
            screen["groupId"] = sid

    if overwrite or "representativeAssetId" not in screen:
        rep = derive_representative_asset_id(screen)
        if rep:
            screen["representativeAssetId"] = rep
        elif "representativeAssetId" in screen and not screen.get("representativeAssetId"):
            screen.pop("representativeAssetId", None)

    if overwrite or "exportHints" not in screen:
        screen["exportHints"] = {}
    elif not isinstance(screen.get("exportHints"), dict):
        screen["exportHints"] = {}

    # Conflict rule (ADR-020 D6): preserveGroup=true forbids flatten hint.
    hints = screen.get("exportHints")
    if (
        isinstance(hints, dict)
        and screen.get("preserveGroup") is True
        and str(hints.get("longshotMode") or "") == "flatten"
    ):
        hints = dict(hints)
        hints.pop("longshotMode", None)
        hints["conflictDropped"] = "longshotMode=flatten"
        screen["exportHints"] = hints

    return screen


def ensure_narrative_contract_on_chapters(
    chapters: list[dict[str, Any]] | None,
    *,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """Apply contract defaults to every screen in chapters (in place)."""
    out = list(chapters or [])
    for ch in out:
        if not isinstance(ch, dict):
            continue
        screens = ch.get("screens")
        if not isinstance(screens, list):
            continue
        for sc in screens:
            if isinstance(sc, dict):
                ensure_narrative_contract(sc, overwrite=overwrite)
    return out
