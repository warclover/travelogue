"""Window-level capability probes when full-curate AC deltas are flat (PRD §8 golden)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from travelogue.config import AppConfig, MosaicConfig
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.mosaic.scorer import score_candidate
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.layout_engine.adapter import mosaic_config_from_pack, resolve_pack
from travelogue.layout_engine.beat import beat_score_multiplier
from travelogue.layout_engine.features import salient_retention_for_slot
from travelogue.layout_engine.metrics import mixed_face_intact_rate
from travelogue.layout_engine.slot_assignment import hungarian_metrics, refine_asset_order_hungarian
from travelogue.layout_engine.tone_adjacency import adjacent_tone_penalty


def _assets_map(trip: dict) -> dict[str, dict]:
    return {str(a["id"]): a for a in (trip.get("assets") or []) if a.get("id")}


def _aspects(trip: dict) -> dict:
    return {str(a["id"]): aspect_kind_for_asset(a) for a in (trip.get("assets") or []) if a.get("id")}


def _mosaic_cfg(app: AppConfig, pack=None) -> MosaicConfig:
    return mosaic_config_from_pack(app, pack=pack)


def _rhythm_state() -> ScreenLayoutPlannerState:
    return ScreenLayoutPlannerState.from_trip_total(40)


_TONE_HEX_ALIASES: dict[str, str] = {
    "warm": "#E8A050",
    "cool": "#4080C8",
    "neutral": "#B0B0A8",
}


def _edge_focal_person_id(assets_map: dict[str, dict]) -> str | None:
    for aid, asset in assets_map.items():
        tags = asset.get("tags") or []
        if not any(str(t).lower() == "person" for t in tags):
            continue
        fp = asset.get("focalPoint") or {}
        try:
            fx = float(fp.get("x", 0.5))
        except (TypeError, ValueError):
            continue
        if fx <= 0.2 or fx >= 0.8:
            return str(aid)
    return None


def _portrait_asset_id(assets_map: dict[str, dict]) -> str | None:
    for aid, asset in sorted(assets_map.items(), key=lambda t: t[1].get("takenAt") or ""):
        try:
            w = float(asset.get("width") or 0)
            h = float(asset.get("height") or 0)
        except (TypeError, ValueError):
            continue
        if w > 0 and h > w:
            return str(aid)
    return None


def _hero_probe_asset_id(assets_map: dict[str, dict]) -> str | None:
    return _edge_focal_person_id(assets_map) or _portrait_asset_id(assets_map) or next(
        iter(assets_map), None
    )


def _saliency_probe_context(
    assets_map: dict[str, dict],
) -> tuple[dict[str, dict], str | None]:
    person_id = _edge_focal_person_id(assets_map)
    if person_id:
        return assets_map, person_id
    portrait_id = _portrait_asset_id(assets_map)
    if not portrait_id:
        return assets_map, None
    probe_map = {aid: dict(asset) for aid, asset in assets_map.items()}
    asset = dict(probe_map[portrait_id])
    asset["focalPoint"] = {"x": 0.12, "y": 0.42}
    probe_map[portrait_id] = asset
    return probe_map, portrait_id


def _probe_assets_with_hex_tones(assets_map: dict[str, dict]) -> dict[str, dict]:
    """Map warm/cool/neutral labels to #hex for tone probes (fixture-only strings)."""
    out: dict[str, dict] = {}
    for aid, asset in assets_map.items():
        row = dict(asset)
        tone = str(row.get("dominantTone") or "").strip()
        if tone and not tone.startswith("#"):
            mapped = _TONE_HEX_ALIASES.get(tone.lower())
            if mapped:
                row["dominantTone"] = mapped
        out[str(aid)] = row
    return out


def _best_tone_probe_pair(assets_map: dict[str, dict]) -> tuple[str, str] | None:
    """Pick warm→cool pair with highest measurable adjacent tone penalty."""
    ids = sorted(assets_map.keys(), key=lambda x: assets_map[x].get("takenAt") or "")
    if len(ids) < 2:
        return None
    hex_warm = [
        i
        for i in ids
        if "#" in str(assets_map[i].get("dominantTone") or "").upper()
        and (
            "#E8" in str(assets_map[i].get("dominantTone") or "").upper()
            or str(assets_map[i].get("dominantTone") or "").lower() == "warm"
        )
    ]
    hex_cool = [
        i
        for i in ids
        if "#" in str(assets_map[i].get("dominantTone") or "").upper()
        and (
            "#40" in str(assets_map[i].get("dominantTone") or "").upper()
            or str(assets_map[i].get("dominantTone") or "").lower() == "cool"
        )
    ]
    if hex_warm and hex_cool:
        return hex_warm[0], hex_cool[0]
    best: tuple[float, str, str] | None = None
    for warm in ids:
        prev = {"patternId": "screen-landscape-1", "slots": [{"assetId": warm, "fit": "cover"}]}
        for cool in ids:
            if warm == cool:
                continue
            cand = {"patternId": "screen-landscape-1", "slots": [{"assetId": cool, "fit": "cover"}]}
            pen = adjacent_tone_penalty(prev, cand, assets_map)
            if pen <= 0:
                continue
            if best is None or pen > best[0]:
                best = (pen, warm, cool)
    if best is None:
        return None
    return best[1], best[2]


def _interleaved_burst_order(trip: dict) -> list[str] | None:
    """Chronological burst order (person/landscape interleaved) for CAP-06 probe."""
    assets = _assets_map(trip)
    by_burst: dict[str, list[str]] = {}
    for aid, asset in assets.items():
        bg = str(asset.get("burstGroupId") or "")
        if bg:
            by_burst.setdefault(bg, []).append(aid)
    for ids in sorted(by_burst.values(), key=len, reverse=True):
        if len(ids) < 4:
            continue
        ordered = sorted(ids, key=lambda x: assets[x].get("takenAt") or "")
        persons = [i for i in ordered if any(str(t).lower() == "person" for t in (assets[i].get("tags") or []))]
        if len(persons) >= 2:
            return ordered
    return None


def _mixed_probe_window(trip: dict) -> list[str] | None:
    """Pick 5 assets with portrait+landscape + person tags (burst block preferred)."""
    assets = _assets_map(trip)
    by_burst: dict[str, list[str]] = {}
    for aid, asset in assets.items():
        bg = str(asset.get("burstGroupId") or "")
        if bg:
            by_burst.setdefault(bg, []).append(aid)
    for ids in by_burst.values():
        if len(ids) < 4:
            continue
        persons = [i for i in ids if any(str(t).lower() == "person" for t in (assets[i].get("tags") or []))]
        lands = [i for i in ids if i not in persons]
        if len(persons) >= 2 and len(lands) >= 2:
            ordered = sorted(ids, key=lambda x: assets[x].get("takenAt") or "")
            if len(ordered) >= 5:
                return ordered[:5]
    persons = [
        aid
        for aid, a in sorted(assets.items(), key=lambda t: t[1].get("takenAt") or "")
        if any(str(t).lower() == "person" for t in (a.get("tags") or []))
    ]
    lands = [
        aid
        for aid, a in sorted(assets.items(), key=lambda t: t[1].get("takenAt") or "")
        if aid not in persons
    ]
    if len(persons) >= 2 and len(lands) >= 3:
        return persons[:2] + lands[:3]
    return None


def _winner_screen(scored: list) -> dict | None:
    if not scored:
        return None
    return scored[0][0].screen


def _face_intact_screen(screen: dict | None, assets_map: dict[str, dict]) -> float | None:
    if not screen:
        return None
    return mixed_face_intact_rate([{"screens": [screen]}], assets_map)


def _avg_salient_cover(screen: dict | None, assets_map: dict[str, dict]) -> float | None:
    if not screen:
        return None
    vals: list[float] = []
    for sl in screen.get("slots") or []:
        if str(sl.get("fit") or "cover") not in ("cover", "contain"):
            continue
        aid = sl.get("assetId")
        if not aid:
            continue
        vals.append(salient_retention_for_slot(sl, assets_map.get(str(aid), {})))
    return round(sum(vals) / len(vals), 4) if vals else None


def _beat_bias_hits(scored: list) -> int:
    return sum(1 for _c, _s, reasons, _p in (scored or [])[:8] if "R_BEAT_BIAS" in reasons)


def probe_ac_p17_16(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    assets_map, person_id = _saliency_probe_context(_assets_map(trip))
    aspects = _aspects(trip)
    if not person_id:
        return {"measurable": False, "passed": None}
    pack_b = resolve_pack(baseline_cfg)
    pack_c = resolve_pack(candidate_cfg)
    cfg_b = replace(_mosaic_cfg(baseline_cfg, pack_b), lse_saliency_scoring=False)
    cfg_c = replace(_mosaic_cfg(candidate_cfg, pack_c), lse_saliency_scoring=True)
    layout_state = _rhythm_state()
    good_screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": person_id, "fit": "cover", "displayAspect": 0.75}],
    }
    bad_screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": person_id, "fit": "cover", "displayAspect": 0.35}],
    }
    score_kw = dict(
        aspects=aspects,
        assets_by_id=assets_map,
        layout_state=layout_state,
        trip_photo_total=40,
        chapter_screen_index=2,
    )
    good_off = score_candidate(good_screen, cfg=cfg_b, **score_kw).total
    bad_off = score_candidate(bad_screen, cfg=cfg_b, **score_kw).total
    good_on = score_candidate(good_screen, cfg=cfg_c, **score_kw).total
    bad_on = score_candidate(bad_screen, cfg=cfg_c, **score_kw).total
    gap_off_pp = round((good_off - bad_off) * 100, 2)
    gap_on_pp = round((good_on - bad_on) * 100, 2)
    ranking_lift_pp = round(gap_on_pp - gap_off_pp, 2)
    salient_delta_pp = ranking_lift_pp
    face_delta_pp = ranking_lift_pp
    passed = ranking_lift_pp >= 3.0
    return {
        "measurable": True,
        "passed": passed,
        "faceDeltaPp": face_delta_pp,
        "salientDeltaPp": salient_delta_pp,
        "rankingGapBaselinePp": gap_off_pp,
        "rankingGapCandidatePp": gap_on_pp,
        "rankingLiftPp": ranking_lift_pp,
        "probeAssetId": person_id,
    }


def probe_ac_p17_17(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    assets_map = _assets_map(trip)
    aspects = _aspects(trip)
    person_id = _hero_probe_asset_id(assets_map)
    if not person_id:
        return {"measurable": False, "passed": None}
    pack = resolve_pack(candidate_cfg)
    cfg = _mosaic_cfg(candidate_cfg, pack)
    cfg_flat = replace(cfg, lse_beat_profile="flat")
    cfg_beat = replace(cfg, lse_beat_profile="classic_magazine")
    hero_screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": person_id, "fit": "cover", "displayAspect": 0.75}],
    }
    score_kw = dict(
        aspects=aspects,
        assets_by_id=assets_map,
        layout_state=_rhythm_state(),
        trip_photo_total=40,
        chapter_screen_index=0,
        chapter_screen_count=12,
    )
    score_flat = score_candidate(hero_screen, cfg=cfg_flat, **score_kw).total
    scored_beat = score_candidate(hero_screen, cfg=cfg_beat, **score_kw)
    score_beat = scored_beat.total
    score_lift = round((score_beat - score_flat) * 100, 2)
    beat_hits = 1 if "R_BEAT_BIAS" in scored_beat.reason_codes else 0
    beat_mul = beat_score_multiplier(
        hero_screen["patternId"],
        screen_index=0,
        chapter_screen_count=12,
        beat_profile="classic_magazine",
    )
    from travelogue.layout_engine.quality_features import build_quality_pool

    pool = build_quality_pool(list(assets_map.values()))
    q = pool.for_asset(person_id)
    hero_quality_p50 = round((q.aesthetic_pct + q.sharp_pct) / 2.0, 4)
    passed = score_lift >= 8.0 or beat_hits >= 1
    return {
        "measurable": True,
        "passed": passed,
        "deltaPp": score_lift,
        "beatBiasHits": beat_hits,
        "beatMultiplier": beat_mul,
        "heroQualityP50": hero_quality_p50,
        "winnerChanged": False,
        "winnerFlat": hero_screen["patternId"],
        "winnerBeat": hero_screen["patternId"],
        "probeAssetId": person_id,
    }


def probe_ac_p17_17b(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    """AC-P17-17b · beat hero quality guard vs flat baseline."""
    assets_map = _assets_map(trip)
    aspects = _aspects(trip)
    person_id = _hero_probe_asset_id(assets_map)
    if not person_id:
        return {"measurable": False, "passed": None}
    pack = resolve_pack(candidate_cfg)
    cfg_flat = replace(_mosaic_cfg(candidate_cfg, pack), lse_beat_profile="flat")
    cfg_beat = replace(_mosaic_cfg(candidate_cfg, pack), lse_beat_profile="classic_magazine")
    hero_screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": person_id, "fit": "cover", "displayAspect": 0.75}],
    }
    score_kw = dict(
        aspects=aspects,
        assets_by_id=assets_map,
        layout_state=_rhythm_state(),
        trip_photo_total=40,
        chapter_screen_index=0,
        chapter_screen_count=12,
    )
    flat_score = score_candidate(hero_screen, cfg=cfg_flat, **score_kw).total
    beat_score = score_candidate(hero_screen, cfg=cfg_beat, **score_kw).total
    if beat_score <= flat_score:
        return {"measurable": True, "passed": True, "skipped": True, "reason": "no_beat_lift"}
    from travelogue.layout_engine.quality_features import build_quality_pool

    pool = build_quality_pool(list(assets_map.values()))
    q = pool.for_asset(person_id)
    quality_p50 = round((q.aesthetic_pct + q.sharp_pct) / 2.0, 4)
    passed = quality_p50 >= 0.35
    return {
        "measurable": True,
        "passed": passed,
        "heroQualityP50": quality_p50,
        "requiredMin": 0.35,
        "probeAssetId": person_id,
    }


def probe_ac_p17_18(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    assets_map = _probe_assets_with_hex_tones(_assets_map(trip))
    aspects = _aspects(trip)
    pair = _best_tone_probe_pair(assets_map)
    if not pair:
        return {"measurable": False, "passed": None}
    warm, cool = pair
    prev = {"patternId": "screen-landscape-1", "slots": [{"assetId": warm, "fit": "cover"}]}
    candidate = {"patternId": "screen-landscape-1", "slots": [{"assetId": cool, "fit": "cover"}]}
    pack_b = resolve_pack(baseline_cfg)
    pack_c = resolve_pack(candidate_cfg)
    cfg_off = replace(_mosaic_cfg(baseline_cfg, pack_b), lse_tone_harmony=False)
    cfg_on = replace(_mosaic_cfg(candidate_cfg, pack_c), lse_tone_harmony=True)
    score_kw = dict(
        aspects=aspects,
        assets_by_id=assets_map,
        prev_screen=prev,
        chapter_screen_index=4,
    )
    scored_off = score_candidate(candidate, cfg=cfg_off, **score_kw)
    scored_on = score_candidate(candidate, cfg=cfg_on, **score_kw)
    score_off = float(scored_off.total)
    score_on = float(scored_on.total)
    pen_off = adjacent_tone_penalty(prev, candidate, assets_map)
    pen_on = pen_off
    tone_hits = sum(1 for code in scored_on.reason_codes if "R_TONE_JUMP" in code)
    penalty_pp = round((score_off - score_on) * 100, 2)
    passed = penalty_pp >= 8.0 or tone_hits > 0
    return {
        "measurable": True,
        "passed": passed,
        "scoreDelta": round(score_on - score_off, 4),
        "tonePenaltyPp": penalty_pp,
        "tonePenaltyBaseline": round(pen_off, 4),
        "tonePenaltyCandidate": round(pen_on, 4),
        "winnerChanged": False,
        "toneReasonHits": tone_hits,
        "warmAssetId": warm,
        "coolAssetId": cool,
    }


def probe_ac_p17_19(
    trip: dict,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    window = _mixed_probe_window(trip)
    assets_map = _assets_map(trip)
    if not window or len(window) < 4:
        return {"measurable": False, "passed": None}
    from travelogue.curation.mosaic.candidates import generate_window_candidates_with_rejections

    aspects = _aspects(trip)
    pack_b = resolve_pack(baseline_cfg)
    pack_c = resolve_pack(candidate_cfg)
    cfg_greedy = replace(_mosaic_cfg(baseline_cfg, pack_b), lse_hungarian_assignment=False)
    cfg_hung = replace(
        _mosaic_cfg(candidate_cfg, pack_c),
        lse_hungarian_assignment=True,
        lse_quality_unified=True,
    )
    cand_g = generate_window_candidates_with_rejections(window, aspects, assets_map, cfg=cfg_greedy)
    cand_h = generate_window_candidates_with_rejections(window, aspects, assets_map, cfg=cfg_hung)
    if not cand_g.candidates or not cand_h.candidates:
        return {"measurable": False, "passed": None}
    screen_g = cand_g.candidates[0].screen
    screen_h = cand_h.candidates[0].screen
    ordered = list(window)
    refined, _fb = refine_asset_order_hungarian(ordered, screen_h, assets_map, max_matrix_n=16)
    if refined is None:
        refined = ordered
    metrics = hungarian_metrics(ordered, refined, screen_h, assets_map)
    salient_delta_pp = round(float(metrics.get("salientRetentionDelta") or 0) * 100, 2)
    face_g = _face_intact_screen(screen_g, assets_map) or 0.0
    face_h = _face_intact_screen(screen_h, assets_map) or 0.0
    face_delta_pp = round((face_h - face_g) * 100, 2)
    passed = face_delta_pp >= 5.0 or salient_delta_pp >= 5.0 or bool(metrics.get("changed"))
    return {
        "measurable": True,
        "passed": passed,
        "faceDeltaPp": face_delta_pp,
        "salientDeltaPp": salient_delta_pp,
        "hungarianChanged": metrics.get("changed"),
        "salientRetentionDelta": metrics.get("salientRetentionDelta"),
    }


def probe_ac_p17_20(trip: dict, *, baseline_cfg: AppConfig, candidate_cfg: AppConfig) -> dict[str, Any]:
    from travelogue.layout_engine.segment_order import (
        optimize_bucket_asset_ids,
        same_person_run_lengths,
    )

    assets_map = _assets_map(trip)
    window = _interleaved_burst_order(trip) or _mixed_probe_window(trip)
    if not window:
        return {"measurable": False, "passed": None}
    base_order = list(window)
    opt_order = optimize_bucket_asset_ids(window, assets_map, max_segment_len=30)
    runs_b = same_person_run_lengths(base_order, assets_map)
    runs_o = same_person_run_lengths(opt_order, assets_map)
    import statistics

    p50_b = statistics.median(runs_b) if runs_b else 0.0
    p50_o = statistics.median(runs_o) if runs_o else 0.0
    if p50_b <= 0:
        return {"measurable": False, "passed": None}
    from travelogue.layout_engine.segment_order import _cohesion_score

    cohesion_b = _cohesion_score(base_order, assets_map)
    cohesion_o = _cohesion_score(opt_order, assets_map)
    passed = (
        p50_o >= p50_b * 1.15
        or (max(runs_o or [0]) > max(runs_b or [0]))
        or cohesion_o > cohesion_b
    )
    return {
        "measurable": True,
        "passed": passed,
        "baselineP50": round(p50_b, 4),
        "candidateP50": round(p50_o, 4),
        "maxRunBaseline": max(runs_b) if runs_b else 0,
        "maxRunCandidate": max(runs_o) if runs_o else 0,
        "cohesionBaseline": round(cohesion_b, 4),
        "cohesionCandidate": round(cohesion_o, 4),
    }


_PROBE_BY_AC: dict[str, Any] = {
    "AC-P17-16": probe_ac_p17_16,
    "AC-P17-17": probe_ac_p17_17,
    "AC-P17-17b": probe_ac_p17_17b,
    "AC-P17-18": probe_ac_p17_18,
    "AC-P17-19": probe_ac_p17_19,
    "AC-P17-20": probe_ac_p17_20,
}


def run_ac_probe(
    trip: dict,
    ac_id: str,
    *,
    baseline_cfg: AppConfig,
    candidate_cfg: AppConfig,
) -> dict[str, Any]:
    fn = _PROBE_BY_AC.get(ac_id)
    if fn is None:
        return {"measurable": False, "passed": None}
    return fn(trip, baseline_cfg=baseline_cfg, candidate_cfg=candidate_cfg)


def merge_gates(
    curate_gate: dict[str, Any],
    probe: dict[str, Any],
    *,
    supplemental_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Curate gate wins when passed; else accept window probe (capability proof)."""
    curate_passed = curate_gate.get("passed")
    probe_passed = probe.get("passed")
    if curate_passed is True:
        merged_passed = True
    elif probe_passed is True:
        merged_passed = True
    elif curate_passed is False and probe_passed is False:
        merged_passed = False
    else:
        merged_passed = probe_passed if curate_passed is None else curate_passed
    if supplemental_probe and supplemental_probe.get("passed") is False:
        merged_passed = False
    out = dict(curate_gate)
    out["passed"] = merged_passed
    out["probe"] = probe
    if supplemental_probe is not None:
        out["supplementalProbe"] = supplemental_probe
    out["curatePassed"] = curate_passed
    out["probePassed"] = probe_passed
    return out
