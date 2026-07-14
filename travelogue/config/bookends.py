"""Bookends Engine configuration (PRD §9 · B1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BookendsPairingConfig:
    require_hard: bool = True
    soft_weight: float = 0.35
    near_dup_seconds: float = 3.0


@dataclass
class BookendsTitleSafeConfig:
    """B2a: opening_hard_gate defaults true (AC-BE-14)."""

    opening_hard_gate: bool = True


@dataclass
class BookendsPluginsConfig:
    opening_vl_rerank: bool = False
    closing_vl_rerank: bool = False


@dataclass
class BookendsConfig:
    enabled: bool = True
    pairing_version: str = "v1"  # off | v1
    opening_quality_version: str = "v2"
    closing_scorer_version: str = "v1"
    lock_after_resolve: bool = True
    mobile_closing: bool = False  # R-BE-10
    pairing: BookendsPairingConfig = field(default_factory=BookendsPairingConfig)
    title_safe: BookendsTitleSafeConfig = field(default_factory=BookendsTitleSafeConfig)
    plugins: BookendsPluginsConfig = field(default_factory=BookendsPluginsConfig)
    telemetry: bool = True


def bookends_config_from_dict(raw: dict[str, Any] | None) -> BookendsConfig:
    raw = raw or {}
    pairing_raw = raw.get("pairing") if isinstance(raw.get("pairing"), dict) else {}
    title_raw = raw.get("title_safe") if isinstance(raw.get("title_safe"), dict) else {}
    if not title_raw and isinstance(raw.get("titleSafe"), dict):
        title_raw = raw["titleSafe"]
    plugins_raw = raw.get("plugins") if isinstance(raw.get("plugins"), dict) else {}

    hard_gate = title_raw.get(
        "opening_hard_gate",
        title_raw.get("openingHardGate", True),
    )

    return BookendsConfig(
        enabled=bool(raw.get("enabled", True)),
        pairing_version=str(raw.get("pairing_version", raw.get("pairingVersion", "v1"))),
        opening_quality_version=str(
            raw.get("opening_quality_version", raw.get("openingQualityVersion", "v2"))
        ),
        closing_scorer_version=str(
            raw.get("closing_scorer_version", raw.get("closingScorerVersion", "v1"))
        ),
        lock_after_resolve=bool(
            raw.get("lock_after_resolve", raw.get("lockAfterResolve", True))
        ),
        mobile_closing=bool(raw.get("mobile_closing", raw.get("mobileClosing", False))),
        pairing=BookendsPairingConfig(
            require_hard=bool(pairing_raw.get("require_hard", pairing_raw.get("requireHard", True))),
            soft_weight=float(pairing_raw.get("soft_weight", pairing_raw.get("softWeight", 0.35))),
            near_dup_seconds=float(
                pairing_raw.get("near_dup_seconds", pairing_raw.get("nearDupSeconds", 3.0))
            ),
        ),
        title_safe=BookendsTitleSafeConfig(opening_hard_gate=bool(hard_gate)),
        plugins=BookendsPluginsConfig(
            opening_vl_rerank=bool(
                plugins_raw.get("opening_vl_rerank", plugins_raw.get("openingVlRerank", False))
            ),
            closing_vl_rerank=bool(
                plugins_raw.get("closing_vl_rerank", plugins_raw.get("closingVlRerank", False))
            ),
        ),
        telemetry=bool(raw.get("telemetry", True)),
    )
