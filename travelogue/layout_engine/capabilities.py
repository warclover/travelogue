"""Resolve effective LSE capabilities from config + Strategy Pack."""

from __future__ import annotations

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
    seg_order = pack.raw.get("segment_order") if isinstance(pack.raw.get("segment_order"), dict) else {}
    feedback = pack.raw.get("feedback") if isinstance(pack.raw.get("feedback"), dict) else {}
    highlight = pack.raw.get("highlight_windows") if isinstance(pack.raw.get("highlight_windows"), dict) else {}
    editorial = pack.raw.get("editorial_hints") if isinstance(pack.raw.get("editorial_hints"), dict) else {}
    return LayoutStrategyCapabilitiesConfig(
        saliency_scoring=bool(features.get("saliency_scoring", False)),
        tone_harmony=bool(features.get("tone_harmony", False)),
        beat_profile=beat,
        hungarian_assignment=slot_mode == "hungarian",
        quality_unified=bool(features.get("quality_unified", False)),
        segment_order_optimizer=bool(seg_order.get("enabled", False)),
        implicit_feedback_export=bool(feedback.get("enabled", False)),
        highlight_windows=bool(highlight.get("enabled", False)),
        editorial_hints=bool(editorial.get("enabled", False)),
    )


def capability_flags_snapshot(
    cfg: AppConfig,
    pack: StrategyPack | None = None,
) -> dict[str, bool | str]:
    """FR-P17-TRACE capability_flags for trip.curation.layoutStrategy."""
    caps = effective_capabilities(cfg, pack)
    return {
        "saliencyScoring": bool(caps.saliency_scoring),
        "toneHarmony": bool(caps.tone_harmony),
        "beatProfile": str(caps.beat_profile or "flat"),
        "hungarianAssignment": bool(caps.hungarian_assignment),
        "qualityUnified": bool(caps.quality_unified),
        "segmentOrderOptimizer": bool(caps.segment_order_optimizer),
        "implicitFeedbackExport": bool(caps.implicit_feedback_export),
        "highlightWindows": bool(caps.highlight_windows),
        "editorialHints": bool(caps.editorial_hints),
    }


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
        segment_order_optimizer=bool(
            base.segment_order_optimizer or pack_caps.segment_order_optimizer
        ),
        implicit_feedback_export=bool(
            base.implicit_feedback_export or pack_caps.implicit_feedback_export
        ),
        pace_profile=base.pace_profile,
        highlight_windows=bool(base.highlight_windows or pack_caps.highlight_windows),
        editorial_hints=bool(base.editorial_hints or pack_caps.editorial_hints),
    )
