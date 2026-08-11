"""Cover Craft Focus (CCF) feature flag — one-click rollback for hero-set narrowing + craft CSS."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


#: HTML ``data-cover-craft`` value when CCF craft CSS pack is active.
CRAFT_ATTR_VALUE = "ccf-v1"


@dataclass
class CoverCraftConfig:
    #: Master switch. ``False`` restores five assignable styles and skips craft CSS attr.
    enabled: bool = True
    #: When enabled, only Hero Set is assignable / offered in Studio.
    hero_only: bool = True
    #: When enabled, render emits ``data-cover-craft="ccf-v1"`` for CSS increments.
    craft_css: bool = True


def _env_tri_state() -> bool | None:
    raw = (os.environ.get("TRAVELOGUE_COVER_CRAFT") or "").strip().lower()
    if not raw:
        return None
    if raw in ("0", "false", "off", "no"):
        return False
    if raw in ("1", "true", "on", "yes"):
        return True
    return None


def cover_craft_config_from_dict(raw: dict[str, Any] | None) -> CoverCraftConfig:
    raw = raw or {}
    cfg = CoverCraftConfig(
        enabled=bool(raw.get("enabled", True)),
        hero_only=bool(raw.get("hero_only", raw.get("heroOnly", True))),
        craft_css=bool(raw.get("craft_css", raw.get("craftCss", True))),
    )
    env = _env_tri_state()
    if env is False:
        cfg.enabled = False
    elif env is True:
        cfg.enabled = True
    return cfg


def is_cover_craft_enabled(cfg: CoverCraftConfig | None = None) -> bool:
    if cfg is not None:
        return bool(cfg.enabled)
    try:
        from travelogue.config import get_config

        return bool(get_config().cover_craft.enabled)
    except Exception:
        env = _env_tri_state()
        if env is not None:
            return env
        return True


def is_cover_craft_hero_only(cfg: CoverCraftConfig | None = None) -> bool:
    if cfg is None:
        try:
            from travelogue.config import get_config

            cfg = get_config().cover_craft
        except Exception:
            return is_cover_craft_enabled(None)
    return bool(cfg.enabled and cfg.hero_only)


def is_cover_craft_css_enabled(cfg: CoverCraftConfig | None = None) -> bool:
    if cfg is None:
        try:
            from travelogue.config import get_config

            cfg = get_config().cover_craft
        except Exception:
            return is_cover_craft_enabled(None)
    return bool(cfg.enabled and cfg.craft_css)
