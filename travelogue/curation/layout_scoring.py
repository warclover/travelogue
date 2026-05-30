"""Layout candidate scoring (V2 PRD §4). Default weights yield legacy-equivalent ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from travelogue.curation.layout_planner import AspectKind

# PRD-EXPERIENCE appendix A §4 · beam + userTier
FEATURED_BEAM_BONUS_PER_ASSET = 0.15
FEATURED_HERO_SEPARATION_HALVED = 0.5

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
        )
        return self.aspect_match >= 1.0 - 1e-9 and sum(others) < 1e-9


PHASE2_WEIGHTS = ScoringWeights(
    aspect_match=0.15,
    sharpness=0.05,
    temporal_coherence=0.12,
    burst_integrity=0.08,
    diversity=0.10,
    arc_fit=0.12,
    hero_separation=0.06,
).normalized()

# Phase-3a: adds luminance continuity + soft subject run
PHASE3_WEIGHTS = ScoringWeights(
    aspect_match=0.13,
    sharpness=0.05,
    temporal_coherence=0.10,
    burst_integrity=0.08,
    diversity=0.08,
    arc_fit=0.10,
    hero_separation=0.06,
    luminance_continuity=0.08,
    subject_run=0.06,
).normalized()

# Phase-3b: dominantTone ΔE spread (requires ingest backfill)
PHASE3B_WEIGHTS = ScoringWeights(
    aspect_match=0.12,
    sharpness=0.05,
    temporal_coherence=0.09,
    burst_integrity=0.08,
    diversity=0.07,
    arc_fit=0.09,
    hero_separation=0.06,
    luminance_continuity=0.06,
    tone_continuity=0.08,
    subject_run=0.05,
    layout_rhythm=0.05,
).normalized()

# Phase-6: cross-screen focal gravity continuity (M25-B)
PHASE6_WEIGHTS = ScoringWeights(
    aspect_match=0.11,
    sharpness=0.05,
    temporal_coherence=0.08,
    burst_integrity=0.08,
    diversity=0.07,
    arc_fit=0.08,
    hero_separation=0.06,
    luminance_continuity=0.06,
    tone_continuity=0.07,
    subject_run=0.05,
    layout_rhythm=0.05,
    gravity_balance=0.05,
).normalized()


def _weights_raw_sum(weights: ScoringWeights) -> float:
    return (
        weights.aspect_match
        + weights.sharpness
        + weights.hero_separation
        + weights.temporal_coherence
        + weights.diversity
        + weights.arc_fit
        + weights.burst_integrity
        + weights.luminance_continuity
        + weights.subject_run
        + weights.tone_continuity
        + weights.layout_rhythm
        + weights.gravity_balance
    )


def resolve_scoring_weights(
    weights: ScoringWeights,
    *,
    scoring_enabled: bool,
    has_color_metrics: bool,
    enable_gravity_balance: bool = True,
) -> ScoringWeights:
    """P5-C1 / D7 / P6-D1: default weight presets when config weights are all zero."""
    if not scoring_enabled:
        return weights
    if weights.is_aspect_only():
        return weights
    if _weights_raw_sum(weights) <= 1e-9:
        if enable_gravity_balance:
            return PHASE6_WEIGHTS
        return PHASE3B_WEIGHTS if has_color_metrics else PHASE3_WEIGHTS
    if enable_gravity_balance and weights.gravity_balance <= 1e-9:
        patched = ScoringWeights(**{**weights.__dict__, "gravity_balance": 0.05})
        return patched.normalized()
    return weights


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
        }


def _aspect_kind_for_slot(slot: dict, aspects: Mapping[str, AspectKind]) -> AspectKind | None:
    aid = slot.get("assetId")
    if not aid:
        return None
    return aspects.get(aid)


def score_aspect_match(screen: dict, aspects: Mapping[str, AspectKind]) -> float:
    """1.0 when slot roles match asset aspect kinds; partial credit per slot."""
    slots = screen.get("slots") or []
    if not slots:
        return 0.0
    hits = 0
    for slot in slots:
        role = (slot.get("role") or "").lower()
        kind = _aspect_kind_for_slot(slot, aspects)
        if kind is None:
            continue
        if role == "portrait" and kind in ("portrait", "tall"):
            hits += 1
        elif role == "landscape" and kind in ("landscape", "panorama"):
            hits += 1
        elif role in ("", "any", "fill") or not role:
            hits += 1
        elif role == "square" and kind == "square":
            hits += 1
    return hits / len(slots)


def score_sharpness(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    slots = screen.get("slots") or []
    scores: list[float] = []
    for slot in slots:
        aid = slot.get("assetId")
        if not aid:
            continue
        asset = assets_by_id.get(aid) or {}
        q = (asset.get("quality") or {}).get("sharpness")
        if q is None:
            scores.append(0.5)
        else:
            scores.append(min(1.0, max(0.0, float(q))))
    return sum(scores) / len(scores) if scores else 0.5


def score_temporal_coherence(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    from datetime import datetime

    slots = screen.get("slots") or []
    times: list[datetime] = []
    for slot in slots:
        aid = slot.get("assetId")
        if not aid:
            continue
        taken = (assets_by_id.get(aid) or {}).get("takenAt")
        if not taken:
            continue
        try:
            times.append(datetime.fromisoformat(str(taken).replace("Z", "+00:00")))
        except ValueError:
            continue
    if len(times) < 2:
        return 1.0
    span = (max(times) - min(times)).total_seconds()
    if span <= 60:
        return 1.0
    if span <= 3600:
        return 0.8
    if span <= 86400:
        return 0.5
    return 0.2


def score_burst_integrity(screens: list[dict], assets_by_id: Mapping[str, dict]) -> float:
    """Fraction of ingest burst groups kept intact within a single screen."""
    from travelogue.curation.burst_utils import ingest_burst_group_id

    groups: dict[str, list[str]] = {}
    for screen in screens:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if not aid:
                continue
            gid = ingest_burst_group_id(assets_by_id.get(aid) or {})
            if gid:
                groups.setdefault(gid, []).append(aid)

    if not groups:
        return 1.0

    preserved = 0
    for _gid, aids in groups.items():
        screen_ids: set[int] = set()
        for si, screen in enumerate(screens):
            slot_aids = {s.get("assetId") for s in (screen.get("slots") or [])}
            if set(aids) & slot_aids:
                screen_ids.add(si)
        if len(screen_ids) <= 1:
            preserved += 1
    return preserved / len(groups)


def asset_mean_luma(asset: dict) -> float:
    """Mean luminance in [0,1]; uses quality.meanLuma or tag heuristics."""
    q = asset.get("quality") or {}
    raw = q.get("meanLuma")
    if raw is not None:
        return min(1.0, max(0.0, float(raw)))
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    if tags & {"night", "dark", "indoor"}:
        return 0.22
    if tags & {"sunset", "golden", "dusk"}:
        return 0.55
    if tags & {"snow", "bright", "beach", "sky"}:
        return 0.82
    return 0.5


def screen_mean_luma(screen: dict, assets_by_id: Mapping[str, dict]) -> float:
    values: list[float] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if aid and aid in assets_by_id:
            values.append(asset_mean_luma(assets_by_id[aid]))
    return sum(values) / len(values) if values else 0.5


def score_luminance_continuity(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
    *,
    l_max: float = 0.35,
) -> float:
    """Adjacent-screen mean luminance smoothness (Phase 3a spread guard)."""
    if len(screens) < 2:
        return 1.0
    lumas = [screen_mean_luma(s, assets_by_id) for s in screens]
    penalties: list[float] = []
    for i in range(len(lumas) - 1):
        delta = abs(lumas[i + 1] - lumas[i])
        penalties.append(min(1.0, max(0.0, delta / l_max)))
    return 1.0 - sum(penalties) / len(penalties)


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


def score_tone_continuity(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Adjacent-screen ΔE (CIE76) triangular window [10, 40], peak 25."""
    from travelogue.media.color_metrics import delta_e_cie76, triangular_score

    if len(screens) < 2:
        return 1.0
    scores: list[float] = []
    for i in range(len(screens) - 1):
        ta = screen_dominant_tone(screens[i], assets_by_id)
        tb = screen_dominant_tone(screens[i + 1], assets_by_id)
        if not ta or not tb:
            continue
        de = delta_e_cie76(ta, tb)
        scores.append(triangular_score(de, low=10.0, peak=25.0, high=40.0))
    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def score_subject_run_soft(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
    *,
    target_run: int = 3,
    tolerance: int = 1,
) -> float:
    """Soft subject runs: allow up to `tolerance` outlier shots inside a run."""
    from travelogue.curation.subject_tagging import subject_class_for_asset

    if len(asset_ids) < 2:
        return 1.0
    classes = [subject_class_for_asset(assets_by_id.get(aid) or {}) for aid in asset_ids]
    runs: list[tuple[str, int, int]] = []
    i = 0
    while i < len(classes):
        cls = classes[i]
        j = i + 1
        outliers = 0
        while j < len(classes):
            if classes[j] == cls:
                j += 1
                continue
            if outliers < tolerance:
                outliers += 1
                j += 1
                continue
            break
        effective = (j - i) - outliers * 0.5
        runs.append((cls, int(effective), outliers))
        i = j if j > i else i + 1

    if not runs:
        return 0.5
    scores = [min(1.0, eff / target_run) for _cls, eff, _out in runs if eff > 0]
    return sum(scores) / len(scores) if scores else 0.5


def _asset_order_from_screens(screens: list[dict]) -> list[str]:
    order: list[str] = []
    for screen in screens:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if aid and aid not in order:
                order.append(aid)
    return order


def _asset_visual_center(asset: dict) -> tuple[float, float]:
    box = asset.get("salientBox")
    if isinstance(box, dict):
        x = float(box.get("x", 0.5))
        y = float(box.get("y", 0.5))
        w = float(box.get("w", 0.0))
        h = float(box.get("h", 0.0))
        return (
            min(1.0, max(0.0, x + w / 2.0)),
            min(1.0, max(0.0, y + h / 2.0)),
        )
    fp = asset.get("focalPoint") or {}
    return float(fp.get("x", 0.5)), float(fp.get("y", 0.45))


def screen_visual_center(screen: dict, assets_by_id: Mapping[str, dict]) -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        cx, cy = _asset_visual_center(assets_by_id.get(aid) or {})
        xs.append(cx)
        ys.append(cy)
    if not xs:
        return 0.5, 0.45
    return sum(xs) / len(xs), sum(ys) / len(ys)


def score_gravity_balance(
    screens: list[dict],
    assets_by_id: Mapping[str, dict],
    *,
    max_delta: float = 0.35,
) -> float:
    """P6-D1 · adjacent-screen focal center continuity (higher = smoother flow)."""
    from travelogue.curation.longshot_filter import _is_breath_screen

    centers: list[tuple[float, float]] = []
    for screen in screens:
        if _is_breath_screen(screen):
            continue
        if not any(s.get("assetId") for s in (screen.get("slots") or [])):
            continue
        centers.append(screen_visual_center(screen, assets_by_id))
    if len(centers) < 2:
        return 1.0
    penalties: list[float] = []
    for i in range(len(centers) - 1):
        dx = centers[i + 1][0] - centers[i][0]
        dy = centers[i + 1][1] - centers[i][1]
        delta = (dx * dx + dy * dy) ** 0.5
        penalties.append(min(1.0, max(0.0, delta / max_delta)))
    return 1.0 - sum(penalties) / len(penalties)


def score_layout_rhythm(screens: list[dict]) -> float:
    """P5-R1 · penalize consecutive same layout; reward hero/grid alternation."""
    from travelogue.curation.longshot_filter import _is_breath_screen, _screen_kind

    scores: list[float] = []
    prev_kind: str | None = None
    prev_pid: str | None = None
    for screen in screens:
        if _is_breath_screen(screen):
            continue
        slots = screen.get("slots") or []
        if not any(s.get("assetId") for s in slots):
            continue
        kind = _screen_kind(screen)
        pid = str(screen.get("patternId") or "")
        if prev_kind is None:
            prev_kind, prev_pid = kind, pid
            continue
        if pid and pid == prev_pid:
            scores.append(0.0)
        elif kind == prev_kind:
            scores.append(0.35)
        else:
            scores.append(1.0)
        prev_kind, prev_pid = kind, pid
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def score_screen(
    screen: dict,
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    arc_segment: str | None = None,
    arc_profile: str = "dynamic",
    hero_asset_ids: set[str] | None = None,
    prior_pattern_ids: list[str] | None = None,
    featured_beam: bool = False,
    intent_arc_boost: float = 0.0,
) -> ScoreBreakdown:
    """Per-screen base score (aspect, sharpness, hero, temporal, diversity, arc).

    ``ScoreBreakdown.total`` here covers only single-screen dimensions. Cross-screen
    terms (burst_integrity, luminance/tone continuity, subject_run) are aggregated in
    ``score_screen_plan`` only.
    """
    bd = ScoreBreakdown()
    bd.aspect_match = score_aspect_match(screen, aspects)
    bd.sharpness = score_sharpness(screen, assets_by_id)
    bd.temporal_coherence = score_temporal_coherence(screen, assets_by_id)
    if hero_asset_ids:
        slot_ids = {s.get("assetId") for s in (screen.get("slots") or []) if s.get("assetId")}
        overlap = slot_ids & hero_asset_ids
        if overlap:
            if featured_beam and any(
                (assets_by_id.get(aid) or {}).get("userTier") == "featured" for aid in overlap
            ):
                bd.hero_separation = FEATURED_HERO_SEPARATION_HALVED
            else:
                bd.hero_separation = 0.0
        else:
            bd.hero_separation = 1.0
    else:
        bd.hero_separation = 1.0
    pid = screen.get("patternId")
    if prior_pattern_ids and pid:
        bd.diversity = 0.0 if pid in prior_pattern_ids[-2:] else 1.0
    else:
        bd.diversity = 1.0
    if arc_segment:
        from travelogue.curation.arc_patterns import arc_pattern_bonus

        bd.arc_fit = arc_pattern_bonus(pid or "", arc_segment, profile=arc_profile)
        if intent_arc_boost > 0:
            bd.arc_fit = min(1.0, bd.arc_fit + intent_arc_boost)
    else:
        bd.arc_fit = 0.5
    bd.total = (
        weights.aspect_match * bd.aspect_match
        + weights.sharpness * bd.sharpness
        + weights.hero_separation * bd.hero_separation
        + weights.temporal_coherence * bd.temporal_coherence
        + weights.diversity * bd.diversity
        + weights.arc_fit * bd.arc_fit
    )
    return bd


def score_screen_plan(
    screens: list[dict],
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    arc_segment: str | None = None,
    arc_profile: str = "dynamic",
    hero_asset_ids: set[str] | None = None,
    subject_run_tolerance: int = 1,
    featured_beam: bool = False,
    intent_arc_boost: float = 0.0,
    enable_gravity_balance: bool = True,
) -> ScoreBreakdown:
    """Aggregate score for a full screen sequence in one day bucket / chapter."""
    if not screens:
        return ScoreBreakdown()
    weights = weights.normalized()
    prior: list[str] = []
    parts: list[ScoreBreakdown] = []
    for screen in screens:
        bd = score_screen(
            screen,
            aspects=aspects,
            assets_by_id=assets_by_id,
            weights=weights,
            arc_segment=arc_segment,
            arc_profile=arc_profile,
            hero_asset_ids=hero_asset_ids,
            prior_pattern_ids=prior,
            featured_beam=featured_beam,
            intent_arc_boost=intent_arc_boost,
        )
        parts.append(bd)
        prior.append(screen.get("patternId") or "")

    burst = score_burst_integrity(screens, assets_by_id)
    luma = score_luminance_continuity(screens, assets_by_id)
    tone = score_tone_continuity(screens, assets_by_id)
    subject = score_subject_run_soft(
        _asset_order_from_screens(screens),
        assets_by_id,
        tolerance=subject_run_tolerance,
    )
    rhythm = score_layout_rhythm(screens)
    gravity = score_gravity_balance(screens, assets_by_id) if enable_gravity_balance else 1.0
    avg = ScoreBreakdown()
    n = len(parts)
    for bd in parts:
        avg.aspect_match += bd.aspect_match / n
        avg.sharpness += bd.sharpness / n
        avg.hero_separation += bd.hero_separation / n
        avg.temporal_coherence += bd.temporal_coherence / n
        avg.diversity += bd.diversity / n
        avg.arc_fit += bd.arc_fit / n
    avg.burst_integrity = burst
    avg.luminance_continuity = luma
    avg.tone_continuity = tone
    avg.subject_run = subject
    avg.layout_rhythm = rhythm
    avg.gravity_balance = gravity
    avg.total = (
        weights.aspect_match * avg.aspect_match
        + weights.sharpness * avg.sharpness
        + weights.hero_separation * avg.hero_separation
        + weights.temporal_coherence * avg.temporal_coherence
        + weights.diversity * avg.diversity
        + weights.arc_fit * avg.arc_fit
        + weights.burst_integrity * avg.burst_integrity
        + weights.luminance_continuity * avg.luminance_continuity
        + weights.tone_continuity * avg.tone_continuity
        + weights.subject_run * avg.subject_run
        + weights.layout_rhythm * avg.layout_rhythm
        + weights.gravity_balance * avg.gravity_balance
    )
    if featured_beam:
        featured_n = 0
        for screen in screens:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if aid and (assets_by_id.get(aid) or {}).get("userTier") == "featured":
                    featured_n += 1
        avg.total += featured_n * FEATURED_BEAM_BONUS_PER_ASSET
    return avg


def rank_screens(
    screens: list[dict],
    *,
    aspects: Mapping[str, AspectKind],
    assets_by_id: Mapping[str, dict],
    weights: ScoringWeights,
    **kwargs: Any,
) -> list[tuple[dict, ScoreBreakdown]]:
    """Return screens sorted by total score descending (stable tie-break by input order)."""
    scored = [
        (s, score_screen(s, aspects=aspects, assets_by_id=assets_by_id, weights=weights, **kwargs))
        for s in screens
    ]
    return sorted(scored, key=lambda x: (-x[1].total, screens.index(x[0])))
