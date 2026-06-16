"""P17 golden layout metrics · AC-P17-16～19 probes (PRD §12)."""

from __future__ import annotations

import statistics
from copy import deepcopy
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig
from travelogue.curation.asset_subject import asset_has_person
from travelogue.curation.layout_metrics import pattern_diversity_p50
from travelogue.curation.layout_scoring import screen_dominant_tone
from travelogue.curation.mosaic.metrics import _MIXED_LAYOUT_PATTERNS
from travelogue.curation.screen_layout_state import is_portrait_single_pattern
from travelogue.layout_engine.features import salient_retention_for_slot
from travelogue.layout_engine.highlight_windows import (
    detect_highlight_windows,
    highlight_window_score,
)
from travelogue.layout_engine.quality_features import QualityPool, build_quality_pool
from travelogue.layout_engine.segment_order import same_person_run_lengths
from travelogue.layout_engine.tone_adjacency import _hard_cut_exempt
from travelogue.media.color_metrics import delta_e_cie76

FACE_INTACT_THRESHOLD = 0.55


def _is_mixed_screen(screen: dict) -> bool:
    pid = str(screen.get("patternId") or "")
    if pid in _MIXED_LAYOUT_PATTERNS:
        return True
    slots = screen.get("slots") or []
    if len(slots) < 2:
        return False
    aspects: set[str] = set()
    for sl in slots:
        ar = sl.get("displayAspect")
        if ar is not None:
            try:
                aspects.add("wide" if float(ar) >= 1.05 else "tall")
            except (TypeError, ValueError):
                pass
    return len(aspects) >= 2


def _is_hero_pattern(pattern_id: str) -> bool:
    pid = str(pattern_id or "")
    return "hero" in pid or "main-hero" in pid


def _is_hero_first_screen(screen: dict) -> bool:
    pid = str(screen.get("patternId") or "")
    slots = screen.get("slots") or []
    if _is_hero_pattern(pid):
        return True
    if is_portrait_single_pattern(pid):
        return True
    return len(slots) == 1


def mixed_face_intact_rate(chapters: list[dict], assets_by_id: dict[str, dict]) -> float | None:
    """Share of person+cover/contain slots on mixed screens with salient retention ≥ threshold."""
    intact = 0
    total = 0
    for ch in chapters:
        for scr in ch.get("screens") or []:
            if not _is_mixed_screen(scr):
                continue
            for sl in scr.get("slots") or []:
                fit = str(sl.get("fit") or "cover")
                if fit not in ("cover", "contain"):
                    continue
                aid = sl.get("assetId")
                if not aid:
                    continue
                asset = assets_by_id.get(str(aid)) or {}
                if not asset_has_person(asset):
                    continue
                total += 1
                if salient_retention_for_slot(sl, asset) >= FACE_INTACT_THRESHOLD:
                    intact += 1
    if total == 0:
        return None
    return round(intact / total, 4)


def mixed_salient_retention_p50(chapters: list[dict], assets_by_id: dict[str, dict]) -> float | None:
    """p50 salient retention on cover slots in mixed screens."""
    values: list[float] = []
    for ch in chapters:
        for scr in ch.get("screens") or []:
            if not _is_mixed_screen(scr):
                continue
            for sl in scr.get("slots") or []:
                if str(sl.get("fit") or "cover") != "cover":
                    continue
                aid = sl.get("assetId")
                if not aid:
                    continue
                asset = assets_by_id.get(str(aid)) or {}
                values.append(salient_retention_for_slot(sl, asset))
    if not values:
        return None
    return round(statistics.median(values), 4)


def chapter_hero_first_screen_rate(chapters: list[dict]) -> float | None:
    """First content screen per chapter that is hero / single-slot."""
    hits = 0
    total = 0
    for ch in chapters:
        screens = ch.get("screens") or []
        if not screens:
            continue
        total += 1
        if _is_hero_first_screen(screens[0]):
            hits += 1
    if total == 0:
        return None
    return round(hits / total, 4)


def adjacent_tone_delta_p50(chapters: list[dict], assets_by_id: dict[str, dict]) -> float | None:
    """p50 Lab ΔE between consecutive screens (hard-cut exempt pairs skipped)."""
    deltas: list[float] = []
    prev: dict | None = None
    for ch in chapters:
        for scr in ch.get("screens") or []:
            if prev is not None and not _hard_cut_exempt(prev, scr, assets_by_id):
                ta = screen_dominant_tone(prev, assets_by_id)
                tb = screen_dominant_tone(scr, assets_by_id)
                if ta and tb:
                    deltas.append(delta_e_cie76(ta, tb))
            prev = scr
    if not deltas:
        return None
    return round(statistics.median(deltas), 4)


def _first_screen_main_asset_id(screen: dict) -> str | None:
    slots = screen.get("slots") or []
    if not slots:
        return None
    for sl in slots:
        if str(sl.get("role") or "").lower() in ("main", "hero"):
            aid = sl.get("assetId")
            if aid:
                return str(aid)
    aid = slots[0].get("assetId")
    return str(aid) if aid else None


def _asset_quality_composite(pool: QualityPool, asset_id: str) -> float:
    q = pool.for_asset(str(asset_id))
    return round((q.aesthetic_pct + q.sharp_pct) / 2.0, 4)


def chapter_first_hero_quality_p50(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
) -> float | None:
    """AC-P17-17b · median quality percentile on chapter-opening hero/single screens."""
    pool = build_quality_pool(list(assets_by_id.values()))
    values: list[float] = []
    for ch in chapters:
        screens = ch.get("screens") or []
        if not screens or not _is_hero_first_screen(screens[0]):
            continue
        aid = _first_screen_main_asset_id(screens[0])
        if aid and aid in assets_by_id:
            values.append(_asset_quality_composite(pool, aid))
    if not values:
        return None
    return round(statistics.median(values), 4)


def highlight_main_quality_delta_pp(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
) -> float | None:
    """AC-P17-26 · highlight window mean quality − non-highlight mean (pp)."""
    pool = build_quality_pool(list(assets_by_id.values()))
    highlight_scores: list[float] = []
    other_scores: list[float] = []
    for ch in chapters:
        order = [
            str(item.get("assetId"))
            for item in (ch.get("items") or [])
            if item.get("assetId")
        ]
        if not order:
            for scr in ch.get("screens") or []:
                for sl in scr.get("slots") or []:
                    aid = sl.get("assetId")
                    if aid:
                        order.append(str(aid))
        if len(order) < 5:
            continue
        windows = detect_highlight_windows(order, assets_by_id, quality=pool, max_windows=2)
        in_highlight: set[str] = set()
        for window in windows:
            in_highlight.update(window)
            highlight_scores.append(highlight_window_score(list(window), assets_by_id, quality=pool))
        for aid in order:
            if aid in in_highlight:
                continue
            q = pool.for_asset(aid)
            other_scores.append((q.aesthetic_pct + q.sharp_pct) / 2.0)
    if not highlight_scores or not other_scores:
        return None
    hl = sum(highlight_scores) / len(highlight_scores)
    rest = sum(other_scores) / len(other_scores)
    return round((hl - rest) * 100, 2)


def same_person_run_p50(chapters: list[dict], assets_by_id: dict[str, dict]) -> float | None:
    """p50 consecutive person-tag run length across chapter reading order (CAP-06)."""
    order: list[str] = []
    for ch in chapters:
        screens = ch.get("screens") or []
        if screens:
            ch_order = [
                str(sl["assetId"])
                for scr in screens
                for sl in (scr.get("slots") or [])
                if sl.get("assetId")
            ]
        else:
            ch_order = [
                str(item.get("assetId"))
                for item in (ch.get("items") or [])
                if item.get("assetId")
            ]
        order.extend(ch_order)
    if not order:
        return None
    runs = same_person_run_lengths(order, assets_by_id)
    if not runs:
        return None
    return round(statistics.median(runs), 4)


def compute_layout_golden_metrics(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
) -> dict[str, float | None]:
    return {
        "layout.mixed.face_intact_rate": mixed_face_intact_rate(chapters, assets_by_id),
        "layout.mixed.salient_retention_p50": mixed_salient_retention_p50(
            chapters, assets_by_id
        ),
        "layout.beat.hero_first_screen_rate": chapter_hero_first_screen_rate(chapters),
        "layout.tone.adjacent_delta_e_p50": adjacent_tone_delta_p50(chapters, assets_by_id),
        "layout.chapter.pattern_diversity_p50": pattern_diversity_p50(chapters),
        "layout.segment.same_person_run_p50": same_person_run_p50(chapters, assets_by_id),
        "layout.beat.first_hero_quality_p50": chapter_first_hero_quality_p50(
            chapters, assets_by_id
        ),
        "layout.highlight.main_quality_delta_pp": highlight_main_quality_delta_pp(
            chapters, assets_by_id
        ),
    }


def curate_trip_chapters(
    trip: dict,
    *,
    work_dir: Path,
    cfg: AppConfig,
) -> list[dict]:
    """Run clustering + curate and return layout chapters (fixture replay helper)."""
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate
    from travelogue.layout_engine.sandbox import _prepare_trip

    body = _prepare_trip(trip)
    work_dir.mkdir(parents=True, exist_ok=True)
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    return deepcopy(body.get("chapters") or [])


def assets_map_from_trip(trip: dict) -> dict[str, dict]:
    return {str(a["id"]): a for a in (trip.get("assets") or []) if a.get("id")}


def evaluate_ac_delta(
    baseline: dict[str, float | None],
    candidate: dict[str, float | None],
) -> dict[str, Any]:
    """Compare golden metrics for AC-P17-16～19 style gates."""

    def _delta(key: str) -> float | None:
        b, c = baseline.get(key), candidate.get(key)
        if b is None or c is None:
            return None
        return round(float(c) - float(b), 4)

    face_delta = _delta("layout.mixed.face_intact_rate")
    salient_delta = _delta("layout.mixed.salient_retention_p50")
    hero_delta = _delta("layout.beat.hero_first_screen_rate")
    tone_b = baseline.get("layout.tone.adjacent_delta_e_p50")
    tone_c = candidate.get("layout.tone.adjacent_delta_e_p50")
    tone_rel: float | None = None
    if tone_b is not None and tone_c is not None and float(tone_b) > 0:
        tone_rel = round((float(tone_c) - float(tone_b)) / float(tone_b), 4)

    diversity_b = baseline.get("layout.chapter.pattern_diversity_p50")
    diversity_c = candidate.get("layout.chapter.pattern_diversity_p50")

    def _gate(passed: bool | None, *, measurable: bool) -> bool | None:
        if not measurable:
            return None
        return passed

    ac16_measurable = face_delta is not None
    ac17_measurable = hero_delta is not None
    ac18_measurable = tone_rel is not None
    ac19_measurable = face_delta is not None and salient_delta is not None
    run_b = baseline.get("layout.segment.same_person_run_p50")
    run_c = candidate.get("layout.segment.same_person_run_p50")
    ac20_measurable = run_b is not None and run_c is not None
    ac20_passed = ac20_measurable and float(run_c) >= float(run_b) * 1.15

    hero_q_b = baseline.get("layout.beat.first_hero_quality_p50")
    hero_q_c = candidate.get("layout.beat.first_hero_quality_p50")
    beat_lifted = hero_delta is not None and hero_delta >= 0.08
    ac17b_measurable = beat_lifted and hero_q_b is not None and hero_q_c is not None
    ac17b_passed = ac17b_measurable and float(hero_q_c) >= float(hero_q_b)

    hl_c = candidate.get("layout.highlight.main_quality_delta_pp")
    ac26_measurable = hl_c is not None
    ac26_passed = ac26_measurable and float(hl_c) >= 8.0

    return {
        "AC-P17-16": {
            "passed": _gate(face_delta is not None and face_delta >= 0.03, measurable=ac16_measurable),
            "measurable": ac16_measurable,
            "deltaPp": round(face_delta * 100, 2) if face_delta is not None else None,
            "requiredPp": 3.0,
        },
        "AC-P17-17": {
            "passed": _gate(hero_delta is not None and hero_delta >= 0.08, measurable=ac17_measurable),
            "measurable": ac17_measurable,
            "deltaPp": round(hero_delta * 100, 2) if hero_delta is not None else None,
            "requiredPp": 8.0,
        },
        "AC-P17-17b": {
            "passed": _gate(ac17b_passed, measurable=ac17b_measurable),
            "measurable": ac17b_measurable,
            "baselineQualityP50": hero_q_b,
            "candidateQualityP50": hero_q_c,
        },
        "AC-P17-18": {
            "passed": _gate(tone_rel is not None and tone_rel <= -0.10, measurable=ac18_measurable),
            "measurable": ac18_measurable,
            "relativeDelta": tone_rel,
            "requiredRelative": -0.10,
        },
        "AC-P17-19": {
            "passed": _gate(
                face_delta is not None
                and face_delta >= 0.05
                and salient_delta is not None
                and salient_delta >= 0.05,
                measurable=ac19_measurable,
            ),
            "measurable": ac19_measurable,
            "faceDeltaPp": round(face_delta * 100, 2) if face_delta is not None else None,
            "salientDeltaPp": round(salient_delta * 100, 2) if salient_delta is not None else None,
            "requiredPp": 5.0,
        },
        "AC-P17-20": {
            "passed": _gate(ac20_passed, measurable=ac20_measurable),
            "measurable": ac20_measurable,
            "baselineP50": run_b,
            "candidateP50": run_c,
            "requiredRelative": 1.15,
        },
        "AC-P17-26": {
            "passed": _gate(ac26_passed, measurable=ac26_measurable),
            "measurable": ac26_measurable,
            "deltaPp": hl_c,
            "requiredPp": 8.0,
        },
        "dogfood": {
            "face_intact_delta_pp": round(face_delta * 100, 2) if face_delta is not None else None,
            "pattern_diversity_p50_baseline": diversity_b,
            "pattern_diversity_p50_candidate": diversity_c,
            "pattern_diversity_ok": (
                diversity_b is not None
                and diversity_c is not None
                and float(diversity_c) >= float(diversity_b)
            ),
        },
    }
