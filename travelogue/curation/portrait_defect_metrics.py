"""AC-PC-D* · portrait defect rates on cover / hero / moment key slots (P3-4)."""

from __future__ import annotations

from typing import Any

from travelogue.config.portrait import PortraitConfig
from travelogue.curation.aesthetic_blind_review import (
    DEFECT_TAG_VALUES,
    PORTRAIT_REVIEW_STRATA,
    review_stratum_for_asset,
)
from travelogue.curation.cover_scoring_params import asset_has_person_tag
from travelogue.curation.portrait_subject_clarity import (
    norm_face_sharpness,
    portrait_has_signal,
    read_portrait_block,
    resolve_portrait_config,
)


def is_portrait_key_slot_candidate(asset: dict | None) -> bool:
    """Whether a key-slot pick is person/group portrait-relevant."""
    if not asset:
        return False
    if review_stratum_for_asset(asset) in PORTRAIT_REVIEW_STRATA:
        return True
    if asset_has_person_tag(asset):
        return True
    faces = asset.get("faces")
    return isinstance(faces, list) and len(faces) > 0


def portrait_defect_tags(
    asset: dict,
    *,
    cfg: PortraitConfig | None = None,
    cull_cfg: dict[str, Any] | None = None,
) -> list[str]:
    """Automated defect tags from portrait block (aligns with blind-review defectTags)."""
    p_cfg = cfg or resolve_portrait_config(cull_cfg)
    if not p_cfg.enabled or not portrait_has_signal(asset, min_confidence=p_cfg.min_confidence):
        return []
    block = read_portrait_block(asset) or {}
    threshold = p_cfg.eyes_threshold()
    tags: list[str] = []
    eyes = block.get("eyesOpenScore")
    if eyes is not None and float(eyes) < threshold:
        tags.append("closed_eyes")
    face_raw = block.get("faceSharpness")
    if face_raw is not None:
        face_norm = norm_face_sharpness(float(face_raw))
        if face_norm < threshold:
            tags.append("blur_face")
    return [t for t in tags if t in DEFECT_TAG_VALUES]


def asset_has_portrait_defect(
    asset: dict,
    *,
    cfg: PortraitConfig | None = None,
    cull_cfg: dict[str, Any] | None = None,
) -> bool:
    return bool(portrait_defect_tags(asset, cfg=cfg, cull_cfg=cull_cfg))


def collect_key_slot_asset_ids(trip: dict) -> dict[str, list[str]]:
    """Unique asset ids per key slot from persisted curate output."""
    out: dict[str, list[str]] = {"cover": [], "hero": [], "moment": []}
    seen_cover: set[str] = set()
    seen_hero: set[str] = set()

    def _add(bucket: str, aid: str | None, seen: set[str]) -> None:
        if not aid:
            return
        key = str(aid)
        if key in seen:
            return
        seen.add(key)
        out[bucket].append(key)

    _add("cover", trip.get("coverAssetId"), seen_cover)
    cover_by = trip.get("coverByLayout")
    if isinstance(cover_by, dict):
        for val in cover_by.values():
            _add("cover", val, seen_cover)

    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    heroes = curation.get("chapterHeroAssetIds")
    if isinstance(heroes, dict):
        for val in heroes.values():
            _add("hero", val, seen_hero)
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        ch_cur = ch.get("curation") if isinstance(ch.get("curation"), dict) else {}
        _add("hero", ch_cur.get("heroAssetId"), seen_hero)

    moment = trip.get("momentAssetId")
    if moment:
        out["moment"] = [str(moment)]
    return out


def analyze_slot_defects(
    trip: dict,
    *,
    cfg: PortraitConfig | None = None,
    cull_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-slot defect summary for one trip."""
    assets_by_id = {
        str(a["id"]): a for a in (trip.get("assets") or []) if isinstance(a, dict) and a.get("id")
    }
    slot_ids = collect_key_slot_asset_ids(trip)
    slots: dict[str, Any] = {}
    for slot_name, aids in slot_ids.items():
        portrait_slots: list[str] = []
        scorable: list[str] = []
        defective: list[str] = []
        details: list[dict[str, Any]] = []
        for aid in aids:
            asset = assets_by_id.get(aid)
            row: dict[str, Any] = {"assetId": aid, "portraitCandidate": is_portrait_key_slot_candidate(asset)}
            if not row["portraitCandidate"]:
                details.append(row)
                continue
            portrait_slots.append(aid)
            tags = portrait_defect_tags(asset or {}, cfg=cfg, cull_cfg=cull_cfg)
            row["defectTags"] = tags
            p_cfg = cfg or resolve_portrait_config(cull_cfg)
            row["hasSignal"] = portrait_has_signal(asset or {}, min_confidence=p_cfg.min_confidence)
            if row["hasSignal"]:
                scorable.append(aid)
                if tags:
                    defective.append(aid)
                    row["defective"] = True
                else:
                    row["defective"] = False
            details.append(row)
        n_scorable = len(scorable)
        slots[slot_name] = {
            "assetIds": aids,
            "portraitCandidateCount": len(portrait_slots),
            "scorableCount": n_scorable,
            "defectCount": len(defective),
            "defectRate": round(len(defective) / n_scorable, 4) if n_scorable else None,
            "defectiveAssetIds": defective,
            "assets": details,
        }
    return {
        "tripId": trip.get("tripId") or trip.get("id"),
        "slots": slots,
    }


def aggregate_defect_rates(trip_reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool scorable portrait key slots across trips."""
    totals: dict[str, dict[str, int]] = {
        slot: {"scorable": 0, "defects": 0} for slot in ("cover", "hero", "moment")
    }
    for rep in trip_reports:
        for slot_name, block in (rep.get("slots") or {}).items():
            if slot_name not in totals:
                continue
            totals[slot_name]["scorable"] += int(block.get("scorableCount") or 0)
            totals[slot_name]["defects"] += int(block.get("defectCount") or 0)
    pooled: dict[str, Any] = {}
    for slot_name, counts in totals.items():
        n = counts["scorable"]
        pooled[slot_name] = {
            "scorableCount": n,
            "defectCount": counts["defects"],
            "defectRate": round(counts["defects"] / n, 4) if n else None,
        }
    all_scorable = sum(c["scorable"] for c in totals.values())
    all_defects = sum(c["defects"] for c in totals.values())
    pooled["all"] = {
        "scorableCount": all_scorable,
        "defectCount": all_defects,
        "defectRate": round(all_defects / all_scorable, 4) if all_scorable else None,
    }
    return pooled


def compare_to_baseline(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    """Return pass/fail when current defect rate <= baseline (AC-PC-D proxy)."""
    base_rates = (baseline.get("aggregate") or baseline.get("pooled") or {}).copy()
    if not base_rates:
        base_rates = aggregate_defect_rates(baseline.get("trips") or [])
    cur_rates = current if current.get("all") else aggregate_defect_rates(current.get("trips") or [])
    comparisons: dict[str, Any] = {}
    passed = True
    for slot in ("cover", "hero", "moment", "all"):
        cur = cur_rates.get(slot) or {}
        base = base_rates.get(slot) or {}
        cur_rate = cur.get("defectRate")
        base_rate = base.get("defectRate")
        if cur_rate is None or base_rate is None:
            comparisons[slot] = {
                "current": cur_rate,
                "baseline": base_rate,
                "passed": None,
                "note": "insufficient scorable portrait slots",
            }
            continue
        ok = float(cur_rate) <= float(base_rate)
        comparisons[slot] = {
            "current": cur_rate,
            "baseline": base_rate,
            "delta": round(float(cur_rate) - float(base_rate), 4),
            "passed": ok,
        }
        if not ok:
            passed = False
    return {"passed": passed, "bySlot": comparisons}
