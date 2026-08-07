"""Opening 白名单与 placement preset (PRD §5.4 · D-CAL-10)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlacementPreset:
    opening_style_id: str
    label: str
    rect: dict[str, float]  # 画布归一化坐标 x/y/w/h


#: 首发仅 veil-footer；folio-overlap 已注册但默认不在 DEFAULT_ENABLED_STYLES 内
#: （D-CAL-10：W2 狗粮后再开）。其它 styleId 不注册 → 非白名单，强制不叠加。
WHITELIST: dict[str, PlacementPreset] = {
    "veil-footer": PlacementPreset(
        opening_style_id="veil-footer",
        label="雾带上方留白区",
        rect={"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22},
    ),
    "folio-overlap": PlacementPreset(
        opening_style_id="folio-overlap",
        label="folio 题区约定矩形",
        rect={"x": 0.10, "y": 0.42, "w": 0.80, "h": 0.20},
    ),
}

DEFAULT_ENABLED_STYLES: frozenset[str] = frozenset({"veil-footer"})


def is_whitelisted(style_id: str, *, enabled_styles: frozenset[str] | None = None) -> bool:
    allowed = enabled_styles if enabled_styles is not None else DEFAULT_ENABLED_STYLES
    return bool(style_id) and style_id in WHITELIST and style_id in allowed


def placement_preset(style_id: str) -> PlacementPreset | None:
    return WHITELIST.get(style_id)
