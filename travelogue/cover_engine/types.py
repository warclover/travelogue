"""Cover Style Engine types (PRD §5.4.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CoverStyleStatus = Literal["draft", "active", "retired"]


@dataclass(frozen=True)
class CoverStyleProfile:
    prefer: dict[str, Any] = field(default_factory=dict)
    avoid: dict[str, Any] = field(default_factory=dict)
    text_safe_regions: list[dict[str, float]] = field(default_factory=list)
    title_max_lines: int = 2


@dataclass(frozen=True)
class CoverStyleRecord:
    id: str
    label: str
    status: CoverStyleStatus
    sort_order: int
    studio_blurb: str
    narrow_fallback: str = "veil-footer"
    closing_family: str | None = None
    css_hook: str = ""
    profile: CoverStyleProfile = field(default_factory=CoverStyleProfile)
    preview_fixtures: tuple[str, ...] = ()
    legacy_aliases: tuple[str, ...] = ()
    studio_label: str = ""  # optional Studio-facing label (A/G disambiguation)

    def __post_init__(self) -> None:
        if not self.css_hook:
            object.__setattr__(self, "css_hook", self.id)
        if not self.studio_label:
            object.__setattr__(self, "studio_label", self.label)


@dataclass(frozen=True)
class CoverJointExplain:
    source: str
    style_id: str
    asset_id: str
    joint: float = 0.0
    quality: float = 0.0
    fit: float = 0.0
    avoid_penalty: float = 0.0
    low_confidence: bool = False
