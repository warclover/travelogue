"""Featured-subject cohort tagging (duo presence) for layout/mosaic coherence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageOps

from travelogue.config import AppConfig, CohortConfig
from travelogue.media.face_embed import cosine_similarity, face_crop_embedding, mean_embedding
from travelogue.media.subject_detect import detect_faces_in_image


@dataclass(frozen=True)
class SubjectTemplate:
    subject_id: str
    label: str
    embedding: np.ndarray


def featured_subjects_from_trip(trip: dict) -> list[dict]:
    intent = trip.get("intent") or {}
    raw = intent.get("featuredSubjects") or intent.get("featured_subjects") or []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id") or "").strip()
        if not sid:
            continue
        seeds = item.get("seedAssetIds") or item.get("seed_asset_ids") or []
        seed_ids = [str(s).strip() for s in seeds if str(s).strip()]
        out.append(
            {
                "id": sid,
                "label": str(item.get("label") or sid)[:16],
                "seedAssetIds": seed_ids,
            }
        )
    return out


def _resolve_asset_image_path(asset: dict, trip_dir: Path) -> Path | None:
    for key in ("sourceFile", "displayFile"):
        rel = asset.get(key)
        if not rel:
            continue
        path = trip_dir / str(rel).replace("\\", "/")
        if path.is_file():
            return path
    return None


def _face_area_ratio(box: tuple[int, int, int, int], img_w: int, img_h: int) -> float:
    _x, _y, w, h = box
    if img_w <= 0 or img_h <= 0:
        return 0.0
    return float(w * h) / float(img_w * img_h)


def _embed_faces_from_image(
    img: Image.Image,
    *,
    min_face_size: int,
    min_face_area_ratio: float,
) -> list[np.ndarray]:
    faces = detect_faces_in_image(img, min_size=min_face_size)
    if not faces:
        return []
    vectors: list[np.ndarray] = []
    for box in faces:
        if _face_area_ratio(box, img.width, img.height) < min_face_area_ratio:
            continue
        emb = face_crop_embedding(img, box)
        if emb is not None:
            vectors.append(emb)
    return vectors


def build_subject_templates(
    subjects: list[dict],
    *,
    trip_dir: Path,
    assets_by_id: Mapping[str, dict],
    cfg: CohortConfig,
    ingest_face_min_size: int,
) -> list[SubjectTemplate]:
    templates: list[SubjectTemplate] = []
    for subj in subjects:
        sid = subj["id"]
        seed_vecs: list[np.ndarray] = []
        for aid in subj.get("seedAssetIds") or []:
            asset = assets_by_id.get(aid)
            if not asset or asset.get("type") != "image":
                continue
            path = _resolve_asset_image_path(asset, trip_dir)
            if path is None:
                continue
            with Image.open(path) as raw:
                img = ImageOps.exif_transpose(raw.convert("RGB"))
            seed_vecs.extend(
                _embed_faces_from_image(
                    img,
                    min_face_size=ingest_face_min_size,
                    min_face_area_ratio=cfg.min_face_area_ratio,
                )
            )
        merged = mean_embedding(seed_vecs)
        if merged is not None:
            templates.append(
                SubjectTemplate(subject_id=sid, label=subj.get("label", sid), embedding=merged)
            )
    return templates


def _match_present_subjects(
    face_embeddings: list[np.ndarray],
    templates: list[SubjectTemplate],
    *,
    threshold: float,
) -> tuple[set[str], float, list[dict[str, Any]]]:
    present: set[str] = set()
    per_face: list[dict[str, Any]] = []
    sims_for_present: list[float] = []

    for emb in face_embeddings:
        best_id: str | None = None
        best_sim = -1.0
        for tpl in templates:
            sim = cosine_similarity(emb, tpl.embedding)
            if sim > best_sim:
                best_sim = sim
                best_id = tpl.subject_id
        row: dict[str, Any] = {"bestSubjectId": best_id, "similarity": round(best_sim, 4)}
        per_face.append(row)
        if best_id and best_sim >= threshold:
            present.add(best_id)
            sims_for_present.append(best_sim)

    confidence = min(sims_for_present) if sims_for_present else 0.0
    return present, confidence, per_face


def _write_asset_cohort(
    asset: dict,
    *,
    present: set[str],
    subject_ids: list[str],
    duo: bool,
    confidence: float,
    method: str,
    face_count: int,
) -> None:
    cur = dict(asset.get("curation") or {})
    cur["cohort"] = {
        "version": "1",
        "subjectsPresent": sorted(present),
        "duo": bool(duo),
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "method": method,
        "faceCount": int(face_count),
        "subjectIds": list(subject_ids),
    }
    asset["curation"] = cur


def asset_cohort_duo(asset: dict | None) -> bool:
    if not asset:
        return False
    cohort = (asset.get("curation") or {}).get("cohort") or {}
    return bool(cohort.get("duo"))


def score_cohort_coherence(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
) -> float:
    """Reward adjacent duo-tagged shots (soft narrative run)."""
    if len(asset_ids) < 2:
        return 1.0
    flags = [asset_cohort_duo(assets_by_id.get(aid)) for aid in asset_ids]
    scores: list[float] = []
    for i in range(len(flags) - 1):
        if flags[i] and flags[i + 1]:
            scores.append(1.0)
        elif flags[i] or flags[i + 1]:
            scores.append(0.55)
        else:
            scores.append(0.35)
    return sum(scores) / len(scores) if scores else 0.5


def apply_cohort_tags(
    trip: dict,
    *,
    trip_dir: Path | None,
    cfg: AppConfig | None,
) -> dict[str, Any] | None:
    """Tag assets when cohort.enabled and trip.intent.featuredSubjects configured."""
    app_cfg = cfg or AppConfig()
    cohort_cfg = app_cfg.cohort
    if not cohort_cfg.enabled:
        return None

    subjects = featured_subjects_from_trip(trip)
    subject_ids = [s["id"] for s in subjects]
    if len(subject_ids) < 2:
        return None
    if trip_dir is None or not trip_dir.is_dir():
        return None

    assets = trip.get("assets") or []
    assets_by_id = {a["id"]: a for a in assets if a.get("id")}
    templates = build_subject_templates(
        subjects,
        trip_dir=trip_dir,
        assets_by_id=assets_by_id,
        cfg=cohort_cfg,
        ingest_face_min_size=app_cfg.ingest.face_min_size_px,
    )
    use_embed = len(templates) >= 2
    tagged = 0
    duo_count = 0

    for asset in assets:
        if asset.get("type") != "image":
            continue
        q = asset.get("quality") or {}
        face_count = int(q.get("faceCount") or 0)
        path = _resolve_asset_image_path(asset, trip_dir)
        present: set[str] = set()
        confidence = 0.0
        method = "none"
        per_face: list[dict[str, Any]] = []

        if use_embed and path is not None:
            with Image.open(path) as raw:
                img = ImageOps.exif_transpose(raw.convert("RGB"))
            face_vecs = _embed_faces_from_image(
                img,
                min_face_size=app_cfg.ingest.face_min_size_px,
                min_face_area_ratio=cohort_cfg.min_face_area_ratio,
            )
            face_count = max(face_count, len(face_vecs))
            present, confidence, per_face = _match_present_subjects(
                face_vecs, templates, threshold=cohort_cfg.match_threshold
            )
            method = "face_embed_v1"
        elif cohort_cfg.l0_face_count_fallback and face_count >= 2:
            present = set(subject_ids)
            confidence = 0.35
            method = "face_count_proxy"

        duo = subject_ids[0] in present and subject_ids[1] in present
        if len(subject_ids) > 2:
            duo = all(sid in present for sid in subject_ids)

        if method != "none":
            tagged += 1
            _write_asset_cohort(
                asset,
                present=present,
                subject_ids=subject_ids,
                duo=duo,
                confidence=confidence,
                method=method,
                face_count=face_count,
            )
            if duo:
                duo_count += 1
            if per_face and method == "face_embed_v1":
                cur = asset.get("curation") or {}
                cohort = cur.get("cohort") or {}
                cohort["faceMatches"] = per_face
                cur["cohort"] = cohort
                asset["curation"] = cur

    return {
        "version": "1",
        "subjectIds": subject_ids,
        "templatesBuilt": len(templates),
        "tagged": tagged,
        "duoCount": duo_count,
        "method": "face_embed_v1" if use_embed else "face_count_proxy",
    }


def cohort_layout_weight_boost(cfg: CohortConfig) -> float:
    return max(0.0, float(cfg.layout_weight))


def merge_cohort_weight(weights: Any, cohort_cfg: CohortConfig) -> Any:
    """Inject cohort_coherence into layout weights when cohort tagging is active."""
    from travelogue.curation.layout_scoring import ScoringWeights

    boost = cohort_layout_weight_boost(cohort_cfg)
    if boost <= 1e-9:
        return weights
    if not isinstance(weights, ScoringWeights):
        weights = ScoringWeights.from_dict(dict(weights) if isinstance(weights, dict) else {})
    if weights.cohort_coherence > 1e-9:
        return weights.normalized()
    patched = ScoringWeights(**{**weights.__dict__, "cohort_coherence": boost})
    return patched.normalized()
