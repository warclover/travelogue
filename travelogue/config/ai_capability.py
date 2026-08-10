"""AI Capability Platform (ACP) configuration · PRD-AI-CAPABILITY-PLATFORM-V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool, cfg_int


@dataclass
class AiCapabilityCacheConfig:
    """Disk cache settings (W1a: dual-track with narrate_cache; unified API shell)."""

    dir: str = ".cache/ai"


@dataclass
class AiCapabilityConfig:
    """Engineering capability switch (independent of ``studio.ai_surface_enabled``).

    W1a default ``enabled=False`` so existing narrate / title_art route C paths
    keep their legacy gate semantics (zero regression). When ``True``, D-ACP-14
    AND gate applies to ACP-wrapped external calls.
    """

    enabled: bool = False
    max_calls_per_trip: int = 12
    timeout_sec: float = 8.0
    cache: AiCapabilityCacheConfig = field(default_factory=AiCapabilityCacheConfig)


def ai_capability_config_from_dict(raw: dict[str, Any] | None) -> AiCapabilityConfig:
    raw = raw or {}
    cache_raw = raw.get("cache") if isinstance(raw.get("cache"), dict) else {}
    timeout_raw = raw.get("timeout_sec", raw.get("timeoutSec", 8.0))
    try:
        timeout_sec = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_sec = 8.0
    return AiCapabilityConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        max_calls_per_trip=cfg_int(
            raw, "max_calls_per_trip", "maxCallsPerTrip", 12
        ),
        timeout_sec=max(0.5, timeout_sec),
        cache=AiCapabilityCacheConfig(
            dir=str(cache_raw.get("dir") or ".cache/ai"),
        ),
    )
