"""Resolve effective LSE capabilities from config + Strategy Pack."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AppConfig
from travelogue.config.layout import LayoutStrategyCapabilitiesConfig
from travelogue.layout_engine.registry import StrategyPack


def capabilities_from_pack(pack: StrategyPack | None) -> LayoutStrategyCapabilitiesConfig:
    if pack is None:
        return LayoutStrategyCapabilitiesConfig()
    features = pack.raw.get("features") if isinstance(pack.raw.get("features"), dict) else {}
    rhythm = pack.raw.get("rhythm") if isinstance(pack.raw.get("rhythm"), dict) else {}
    beat = str(rhythm.get("beat_profile", "flat") or "flat")
    slot_mode = str((pack.raw.get("slot_assignment") or {}).get("mode", "greedy") or "greedy")
    return LayoutStrategyCapabilitiesConfig(
        saliency_scoring=bool(features.get("saliency_scoring", False)),
        tone_harmony=bool(features.get("tone_harmony", False)),
        beat_profile=beat,
        hungarian_assignment=slot_mode == "hungarian",
        quality_unified=bool(features.get("quality_unified", False)),
    )


def effective_capabilities(
    cfg: AppConfig,
    pack: StrategyPack | None = None,
) -> LayoutStrategyCapabilitiesConfig:
    """Config overrides win; pack fills defaults when LSE fields are off/flat."""
    base = cfg.layout.strategy_engine.capabilities
    pack_caps = capabilities_from_pack(pack)
    return LayoutStrategyCapabilitiesConfig(
        saliency_scoring=bool(base.saliency_scoring or pack_caps.saliency_scoring),
        tone_harmony=bool(base.tone_harmony or pack_caps.tone_harmony),
        beat_profile=base.beat_profile if base.beat_profile not in ("", "flat") else pack_caps.beat_profile,
        hungarian_assignment=bool(base.hungarian_assignment or pack_caps.hungarian_assignment),
        quality_unified=bool(getattr(base, "quality_unified", False) or getattr(pack_caps, "quality_unified", False)),
        segment_order_optimizer=base.segment_order_optimizer,
        implicit_feedback_export=base.implicit_feedback_export,
        pace_profile=base.pace_profile,
        highlight_windows=base.highlight_windows,
        editorial_hints=base.editorial_hints,
    )
