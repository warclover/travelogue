"""LTN D3 · product layout role table (PRD §10) ↔ narrativeRole.

Product / review vocabulary uses short aliases (plate / 1col / stack-3 / …).
Canonical persisted enum remains ``narrativeRole`` (ADR-020).
"""

from __future__ import annotations

from typing import Any, Literal

from travelogue.layout_contract.narrative_contract import (
    NARRATIVE_ROLES,
    NarrativeRole,
    derive_narrative_role,
    ensure_narrative_contract,
)

# Review / render vocabulary (R-D3).
ProductLayoutRole = Literal[
    "plate",
    "1col",
    "stack-3",
    "2col",
    "mosaic-hero",
    "mosaic-flat",
    "breath",
]

PRODUCT_LAYOUT_ROLES: frozenset[str] = frozenset(
    {
        "plate",
        "1col",
        "stack-3",
        "2col",
        "mosaic-hero",
        "mosaic-flat",
        "breath",
    }
)

NARRATIVE_TO_PRODUCT: dict[str, ProductLayoutRole] = {
    "plate": "plate",
    "hero_single": "1col",
    "stack": "stack-3",
    "pair": "2col",
    "mosaic_hero": "mosaic-hero",
    "mosaic_flat": "mosaic-flat",
    "breath": "breath",
}

PRODUCT_TO_NARRATIVE: dict[str, NarrativeRole] = {
    "plate": "plate",
    "1col": "hero_single",
    "stack-3": "stack",
    "2col": "pair",
    "mosaic-hero": "mosaic_hero",
    "mosaic-flat": "mosaic_flat",
    "breath": "breath",
}

# PRD §10 product contract (comment / review SSOT for engineering).
LAYOUT_ROLE_TABLE: tuple[dict[str, str], ...] = (
    {
        "productRole": "plate",
        "narrativeRole": "plate",
        "patternHint": "章扉 / 未识别默认",
        "duty": "章界 / 找「第几天」",
        "density": "低",
    },
    {
        "productRole": "1col",
        "narrativeRole": "hero_single",
        "patternHint": "landscape-1 / portrait-1",
        "duty": "纪念权、情绪锚点",
        "density": "低",
    },
    {
        "productRole": "2col",
        "narrativeRole": "pair",
        "patternHint": "portrait-2 / 对照混排",
        "duty": "成对人物 / 左右对照",
        "density": "低",
    },
    {
        "productRole": "stack-3",
        "narrativeRole": "stack",
        "patternHint": "stack-3 / 混三",
        "duty": "同场推进（须同质）",
        "density": "中",
    },
    {
        "productRole": "mosaic-hero",
        "narrativeRole": "mosaic_hero",
        "patternHint": "mosaic-4/5/6 hero",
        "duty": "同场景证据墙（高潮）",
        "density": "稀",
    },
    {
        "productRole": "mosaic-flat",
        "narrativeRole": "mosaic_flat",
        "patternHint": "landscape-4 / portrait-4 等权",
        "duty": "仅 fallback / 显式签名位",
        "density": "应↓",
    },
    {
        "productRole": "breath",
        "narrativeRole": "breath",
        "patternHint": "breath / L2 pause",
        "duty": "语义留白（≠空屏凑缝）",
        "density": "稀",
    },
)


def product_role_for(narrative_role: str | None) -> ProductLayoutRole:
    """Map ADR-020 narrativeRole → product alias; unknown → plate."""
    key = str(narrative_role or "").strip()
    if key in NARRATIVE_TO_PRODUCT:
        return NARRATIVE_TO_PRODUCT[key]
    return "plate"


def narrative_role_for_product(product_role: str | None) -> NarrativeRole:
    key = str(product_role or "").strip()
    if key in PRODUCT_TO_NARRATIVE:
        return PRODUCT_TO_NARRATIVE[key]
    return "plate"


def resolve_layout_roles(screen: dict[str, Any] | None) -> tuple[str, str]:
    """Return ``(narrativeRole, productRole)`` for a screen (read-time defaults)."""
    if not isinstance(screen, dict):
        return "plate", "plate"
    ensure_narrative_contract(screen)
    role = str(screen.get("narrativeRole") or "")
    if role not in NARRATIVE_ROLES:
        pid = str(screen.get("patternId") or "")
        slots = screen.get("slots") or []
        n = len(slots) if isinstance(slots, list) else 0
        role = derive_narrative_role(pid, slot_count=n)
    return role, product_role_for(role)
