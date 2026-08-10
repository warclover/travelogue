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
class IntentBriefConfig:
    """Intent Brief Agent feature flag (W2 · default off for NR)."""

    enabled: bool = False


@dataclass
class LayoutCriticConfig:
    """Layout Critic Agent feature flag (W3 · default off for NR)."""

    enabled: bool = False


@dataclass
class MosaicJudgeConfig:
    """Mosaic Judge Agent (W3 skeleton · D-ACP-15 post-beam async; default off)."""

    enabled: bool = False
    tie_epsilon: float = 0.03
    max_calls_per_trip: int = 4


@dataclass
class AiEvalConfig:
    """Eval / unlock-gate / blind-review knobs (W4)."""

    blind_review_sample_rate: float = 0.1
    unlock_min_samples: int = 30
    unlock_config_conversion_rate: float = 0.40
    unlock_narrate_success_rate: float = 0.70
    unlock_channel_copy_rate: float = 0.30


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
    intent_brief: IntentBriefConfig = field(default_factory=IntentBriefConfig)
    layout_critic: LayoutCriticConfig = field(default_factory=LayoutCriticConfig)
    mosaic_judge: MosaicJudgeConfig = field(default_factory=MosaicJudgeConfig)
    eval: AiEvalConfig = field(default_factory=AiEvalConfig)


def _subdict(raw: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        val = raw.get(key)
        if isinstance(val, dict):
            return val
    return {}


def ai_capability_config_from_dict(raw: dict[str, Any] | None) -> AiCapabilityConfig:
    raw = raw or {}
    cache_raw = raw.get("cache") if isinstance(raw.get("cache"), dict) else {}
    ib_raw = _subdict(raw, "intent_brief", "intentBrief")
    lc_raw = _subdict(raw, "layout_critic", "layoutCritic")
    mj_raw = _subdict(raw, "mosaic_judge", "mosaicJudge")
    eval_raw = _subdict(raw, "eval")
    timeout_raw = raw.get("timeout_sec", raw.get("timeoutSec", 8.0))
    try:
        timeout_sec = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_sec = 8.0
    tie_raw = mj_raw.get("tie_epsilon", mj_raw.get("tieEpsilon", 0.03))
    try:
        tie_epsilon = float(tie_raw)
    except (TypeError, ValueError):
        tie_epsilon = 0.03

    def _f(d: dict[str, Any], *keys: str, default: float) -> float:
        for k in keys:
            if k in d and d[k] is not None:
                try:
                    return float(d[k])
                except (TypeError, ValueError):
                    pass
        return default

    sample_rate = _f(
        eval_raw, "blind_review_sample_rate", "blindReviewSampleRate", default=0.1
    )
    return AiCapabilityConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        max_calls_per_trip=cfg_int(
            raw, "max_calls_per_trip", "maxCallsPerTrip", 12
        ),
        timeout_sec=max(0.5, timeout_sec),
        cache=AiCapabilityCacheConfig(
            dir=str(cache_raw.get("dir") or ".cache/ai"),
        ),
        intent_brief=IntentBriefConfig(
            enabled=cfg_bool(ib_raw, "enabled", "enabled", False),
        ),
        layout_critic=LayoutCriticConfig(
            enabled=cfg_bool(lc_raw, "enabled", "enabled", False),
        ),
        mosaic_judge=MosaicJudgeConfig(
            enabled=cfg_bool(mj_raw, "enabled", "enabled", False),
            tie_epsilon=max(0.0, tie_epsilon),
            max_calls_per_trip=max(
                0,
                cfg_int(mj_raw, "max_calls_per_trip", "maxCallsPerTrip", 4),
            ),
        ),
        eval=AiEvalConfig(
            blind_review_sample_rate=max(0.0, min(1.0, sample_rate)),
            unlock_min_samples=max(
                1, cfg_int(eval_raw, "unlock_min_samples", "unlockMinSamples", 30)
            ),
            unlock_config_conversion_rate=_f(
                eval_raw,
                "unlock_config_conversion_rate",
                "unlockConfigConversionRate",
                default=0.40,
            ),
            unlock_narrate_success_rate=_f(
                eval_raw,
                "unlock_narrate_success_rate",
                "unlockNarrateSuccessRate",
                default=0.70,
            ),
            unlock_channel_copy_rate=_f(
                eval_raw,
                "unlock_channel_copy_rate",
                "unlockChannelCopyRate",
                default=0.30,
            ),
        ),
    )
