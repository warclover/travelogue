"""LSE pattern blacklist (pack policy + runtime overrides)."""

from __future__ import annotations

from typing import Any

from travelogue.config import AppConfig
from travelogue.layout_engine.adapter import lse_enabled, resolve_pack
from travelogue.layout_engine.runtime_store import effective_disable_patterns


def effective_pattern_blacklist(
    cfg: AppConfig,
    *,
    pack: Any | None = None,
) -> tuple[str, ...]:
    """Merged pattern IDs excluded from MCS candidate registry."""
    if not lse_enabled(cfg):
        return ()
    active = pack if pack is not None else resolve_pack(cfg)
    ids: list[str] = []
    if active is not None:
        pol = active.raw.get("pattern_policy") or {}
        for key in ("blacklist", "lte_overrides_disable"):
            raw = pol.get(key) or []
            if isinstance(raw, list):
                ids.extend(str(x) for x in raw if x)
    ids.extend(effective_disable_patterns(cfg))
    return tuple(dict.fromkeys(ids))
