"""Output Recipe V1 · types and errors (PRD-OUTPUT-RECIPE-V1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BandId = Literal["sparse", "ambiguous", "narrative"]
EngineId = Literal[
    "chapter_capture",
    "platform_segment",
    "photo_grid",
    "poster_bric",
    "collage_pages",
]
IntentId = Literal[
    "chat_longshot",
    "moments_scroll",
    "moments_grid",
    "xiaohongshu",
    "instagram_carousel",
    "poster_bric",
    "album_spread",
]
EntrypointId = Literal["preview", "shelf", "cli"]
SourceId = Literal[
    "band_default",
    "intent_choice",
    "trip_override",
    "session_override",
    "flag_disabled",
    "platform_alias",
    "portfolio_bypass",
]

# Phase A selectable intents (Ambiguous card · Phase A)
PHASE_A_INTENTS = frozenset({"chat_longshot", "moments_scroll"})
# Phase B Ambiguous 卡：发群 + 朋友圈连读（九宫格已从 Studio 下线，仅 CLI）
PHASE_B_INTENTS = frozenset({"chat_longshot", "moments_scroll"})
# Known intents (schema); moments_grid retained for CLI alias
ALL_INTENTS = frozenset(
    {
        "chat_longshot",
        "moments_scroll",
        "moments_grid",
        "xiaohongshu",
        "instagram_carousel",
        "poster_bric",
        "album_spread",
    }
)
# Phase B0 Writer 已交付 · 不再 unavailable
PHASE_A_UNAVAILABLE_INTENTS = frozenset()
PHASE_UNAVAILABLE_INTENTS = frozenset()  # reserved for future gates

INTENT_TO_PLATFORM: dict[str, str] = {
    "chat_longshot": "wechat_chat",
    "moments_scroll": "wechat_moments",
    "moments_grid": "moments_grid",
    "xiaohongshu": "xiaohongshu",
    "instagram_carousel": "instagram",
    "poster_bric": "poster_bric",
    "album_spread": "album_spread",
}

PLATFORM_TO_INTENT: dict[str, str] = {
    "wechat_chat": "chat_longshot",
    "wechat_moments": "moments_scroll",
    "moments_grid": "moments_grid",
    "xiaohongshu": "xiaohongshu",
    "instagram": "instagram_carousel",
    "poster_bric": "poster_bric",
    "album_spread": "album_spread",
}


class OutputRecipeError(ValueError):
    """Invalid recipe / intent / platform combination."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class BandThresholds:
    sparse_max: int = 9
    ambiguous_max: int = 30
    narrative_chapter_hint_at: int = 50


@dataclass(frozen=True)
class OutputRecipe:
    """Resolved job contract (PRD §6.2 · V1 minimal executable set)."""

    recipe_id: str
    preset_id: str
    intent: str
    engine: str
    band: str
    kept_n: int
    locale: str
    platform: str
    layout: str
    count_policy: dict[str, Any] = field(default_factory=dict)
    geometry: dict[str, Any] = field(default_factory=dict)
    pad_mode: str | None = None
    packing: str = "none"
    quality: dict[str, Any] = field(default_factory=lambda: {"scale": 2})
    publish_guide_key: str = ""
    user_hints: tuple[str, ...] = ()
    needs_intent: bool = False
    source: str = "band_default"
    instagram_preset_state: str | None = None
    cta_label: str = ""
    product_label: str = ""
    entrypoint: str = "preview"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["user_hints"] = list(self.user_hints)
        return d
