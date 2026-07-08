"""Layout scoring DTOs and pure helpers (layout kernel · M-B4 follow-up)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

FEATURED_BEAM_BONUS_PER_ASSET = 0.15
FEATURED_HERO_SEPARATION_HALVED = 0.5


def moment_secondary_plan_bonus(
    screens: list[dict],
    *,
    arc_segment: str | None,
    secondary_ids: set[str] | frozenset[str],
    boost: float,
) -> float:
    """Peak-chapter spread boost for moment pool secondaries (PRD §7.3 · max 1 hit/plan)."""
    if boost <= 0 or not secondary_ids or arc_segment != "peak":
        return 0.0
    for screen in screens:
        slot_ids = {
            str(s.get("assetId"))
            for s in (screen.get("slots") or [])
            if s.get("assetId")
        }
        if slot_ids & secondary_ids:
            return boost
    return 0.0


@dataclass(frozen=True)
class ScoringWeights:
    aspect_match: float = 0.0
    sharpness: float = 0.0
    hero_separation: float = 0.0
    temporal_coherence: float = 0.0
    diversity: float = 0.0
    arc_fit: float = 0.0
    burst_integrity: float = 0.0
    luminance_continuity: float = 0.0
    subject_run: float = 0.0
    tone_continuity: float = 0.0
    layout_rhythm: float = 0.0
    gravity_balance: float = 0.0
    category_coherence: float = 0.0
    cohort_coherence: float = 0.0

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> ScoringWeights:
        if not raw:
            return cls()
        defaults = cls()
        return cls(
            aspect_match=float(raw.get("aspect_match", defaults.aspect_match)),
            sharpness=float(raw.get("sharpness", defaults.sharpness)),
            hero_separation=float(raw.get("hero_separation", defaults.hero_separation)),
            temporal_coherence=float(raw.get("temporal_coherence", defaults.temporal_coherence)),
            diversity=float(raw.get("diversity", defaults.diversity)),
            arc_fit=float(raw.get("arc_fit", defaults.arc_fit)),
            burst_integrity=float(raw.get("burst_integrity", defaults.burst_integrity)),
            luminance_continuity=float(raw.get("luminance_continuity", defaults.luminance_continuity)),
            subject_run=float(raw.get("subject_run", defaults.subject_run)),
            tone_continuity=float(raw.get("tone_continuity", defaults.tone_continuity)),
            layout_rhythm=float(raw.get("layout_rhythm", defaults.layout_rhythm)),
            gravity_balance=float(raw.get("gravity_balance", defaults.gravity_balance)),
            category_coherence=float(raw.get("category_coherence", defaults.category_coherence)),
            cohort_coherence=float(raw.get("cohort_coherence", defaults.cohort_coherence)),
        )

    def normalized(self) -> ScoringWeights:
        total = (
            self.aspect_match
            + self.sharpness
            + self.hero_separation
            + self.temporal_coherence
            + self.diversity
            + self.arc_fit
            + self.burst_integrity
            + self.luminance_continuity
            + self.subject_run
            + self.tone_continuity
            + self.layout_rhythm
            + self.gravity_balance
            + self.category_coherence
            + self.cohort_coherence
        )
        if total <= 1e-9:
            return self
        return ScoringWeights(
            aspect_match=self.aspect_match / total,
            sharpness=self.sharpness / total,
            hero_separation=self.hero_separation / total,
            temporal_coherence=self.temporal_coherence / total,
            diversity=self.diversity / total,
            arc_fit=self.arc_fit / total,
            burst_integrity=self.burst_integrity / total,
            luminance_continuity=self.luminance_continuity / total,
            subject_run=self.subject_run / total,
            tone_continuity=self.tone_continuity / total,
            layout_rhythm=self.layout_rhythm / total,
            gravity_balance=self.gravity_balance / total,
            category_coherence=self.category_coherence / total,
            cohort_coherence=self.cohort_coherence / total,
        )

    def is_aspect_only(self) -> bool:
        others = (
            self.sharpness,
            self.hero_separation,
            self.temporal_coherence,
            self.diversity,
            self.arc_fit,
            self.burst_integrity,
            self.luminance_continuity,
            self.subject_run,
            self.tone_continuity,
            self.layout_rhythm,
            self.gravity_balance,
            self.category_coherence,
            self.cohort_coherence,
        )
        return self.aspect_match >= 1.0 - 1e-9 and sum(others) < 1e-9


@dataclass
class ScoreBreakdown:
    total: float = 0.0
    aspect_match: float = 0.0
    sharpness: float = 0.0
    hero_separation: float = 0.0
    temporal_coherence: float = 0.0
    diversity: float = 0.0
    arc_fit: float = 0.0
    burst_integrity: float = 0.0
    luminance_continuity: float = 0.0
    subject_run: float = 0.0
    tone_continuity: float = 0.0
    layout_rhythm: float = 0.0
    gravity_balance: float = 0.0
    category_coherence: float = 0.0
    cohort_coherence: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "total": round(self.total, 6),
            "aspect_match": round(self.aspect_match, 6),
            "sharpness": round(self.sharpness, 6),
            "hero_separation": round(self.hero_separation, 6),
            "temporal_coherence": round(self.temporal_coherence, 6),
            "diversity": round(self.diversity, 6),
            "arc_fit": round(self.arc_fit, 6),
            "burst_integrity": round(self.burst_integrity, 6),
            "luminance_continuity": round(self.luminance_continuity, 6),
            "subject_run": round(self.subject_run, 6),
            "tone_continuity": round(self.tone_continuity, 6),
            "layout_rhythm": round(self.layout_rhythm, 6),
            "gravity_balance": round(self.gravity_balance, 6),
            "category_coherence": round(self.category_coherence, 6),
            "cohort_coherence": round(self.cohort_coherence, 6),
        }


@dataclass
class IncrementalScoreState:
    """P7-D2 · cache per-screen scores for shared beam plan prefixes."""

    prefix_parts: dict[tuple[Any, ...], tuple[list[ScoreBreakdown], list[str]]] = field(
        default_factory=dict
    )


def screen_dominant_tone(screen: dict, assets_by_id: Mapping[str, dict]) -> str | None:
    tones: list[str] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        tone = (assets_by_id.get(aid) or {}).get("dominantTone")
        if isinstance(tone, str) and tone.startswith("#"):
            tones.append(tone)
    if not tones:
        return None
    return tones[0]

def median_sharpness(assets: list[dict]) -> float:
    from travelogue.media.quality import asset_sharpness

    values = [asset_sharpness(a) for a in assets if asset_sharpness(a) > 0]
    if not values:
        return 0.0
    values.sort()
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def sort_bucket_asset_ids(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    from travelogue.media.quality import asset_sharpness

    items = [(aid, assets_by_id.get(aid, {})) for aid in bucket]
    items.sort(key=lambda x: x[1].get("takenAt") or "")
    result: list[str] = []
    i = 0
    while i < len(items):
        aid, a = items[i]
        bg = a.get("burstGroupId")
        if bg:
            group_ids = [aid]
            j = i + 1
            while j < len(items) and items[j][1].get("burstGroupId") == bg:
                group_ids.append(items[j][0])
                j += 1
            group_ids.sort(key=lambda x: -asset_sharpness(assets_by_id.get(x, {})))
            result.extend(group_ids)
            i = j
        else:
            result.append(aid)
            i += 1
    return result
