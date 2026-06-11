"""LTE datamodel (shared by registry, geometry, css_gen)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StageMargins:
    top: str | None = None
    right: str | None = None
    bottom: str | None = None
    left: str | None = None


@dataclass(frozen=True)
class TemplateStage:
    aspect: str
    grid: tuple[int, int] | None = None
    cols: tuple[float, ...] | None = None
    rows: tuple[float, ...] | None = None
    gap: str | None = None
    margins: StageMargins | None = None
    bleed: str | None = None


@dataclass(frozen=True)
class SlotAspectRange:
    min_aspect: float
    max_aspect: float


@dataclass(frozen=True)
class TemplateSlot:
    index: int
    rect: tuple[int, int, int, int]
    role: str
    fit: str | None = None
    visual_weight: float | None = None
    display_aspect: float | None = None
    inset: str | None = None
    aspect_range: SlotAspectRange | None = None
    crop_policy: str | None = None
    optional: bool = False


@dataclass(frozen=True)
class TemplateDef:
    id: str
    version: int
    status: str
    kind: str
    display_name: str
    stage: TemplateStage
    photo_count_min: int
    photo_count_max: int
    slots: tuple[TemplateSlot, ...]
    render_grid_class: str
    render_css_bundle: str
    description: str = ""
    aesthetic: str | None = None
    balance_policy: str | None = None
    mix_portrait: int | None = None
    mix_landscape: int | None = None
    scoring: dict[str, Any] = field(default_factory=dict)
    compatibility_hints: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    render_fit_policy: str | None = None
    rollout: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    max_fill_ratio: float | None = None
    bleed: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
