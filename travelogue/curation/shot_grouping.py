"""Smart Shot Grouping projection layer (SSG M1/M2) · PRD-SMART-SHOT-GROUPING-V1.

Consumes Phase 3 ``sceneClusterId`` (+ time soft-split) and writes
``asset.shotGroupId`` + ``curation.shotGrouping``. M2 may overwrite with
``kind=look`` via upper-body CLIP appearance. Does not rewrite chapters.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from travelogue.config.app import AppConfig
from travelogue.config.runtime import get_config
from travelogue.config.shot_grouping import (
    ShotGroupingConfig,
    resolve_look_enabled,
    resolve_shot_grouping_enabled,
)
from travelogue.curation.look_split import split_look_segments
from travelogue.curation.shot_group_metrics import shot_group_coverage_ratio

_log = logging.getLogger(__name__)

SHOT_GROUPING_VERSION = "1"


@dataclass
class ShotGroupingResult:
    mode: str  # off | scene | empty
    group_count: int
    soft_split_count: int
    look_group_count: int = 0
    stage_hint: str = ""


def _parse_taken_at(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _assets_list(trip: dict) -> list[dict]:
    assets = trip.get("assets")
    if isinstance(assets, list):
        return [a for a in assets if isinstance(a, dict)]
    return []


def _has_scene_clusters(assets: list[dict]) -> bool:
    for a in assets:
        cid = a.get("sceneClusterId")
        if cid is not None and cid != -1:
            return True
    return False


def _clear_shot_group_fields(assets: list[dict]) -> None:
    for a in assets:
        a.pop("shotGroupId", None)
        a.pop("shotGroupKind", None)
        a.pop("shotGroupConfidence", None)


def _soft_split_runs(
    members: list[dict],
    *,
    split_hours: float,
) -> tuple[list[list[dict]], int]:
    """Split same-cluster members by time gap. Returns (runs, soft_split_count)."""
    if not members:
        return [], 0
    ordered = sorted(members, key=lambda a: (_parse_taken_at(a.get("takenAt")) or datetime.min.replace(tzinfo=UTC), a.get("id") or ""))
    runs: list[list[dict]] = [[ordered[0]]]
    splits = 0
    gap = max(0.0, float(split_hours)) * 3600.0
    for asset in ordered[1:]:
        prev_t = _parse_taken_at(runs[-1][-1].get("takenAt"))
        cur_t = _parse_taken_at(asset.get("takenAt"))
        if prev_t is not None and cur_t is not None and (cur_t - prev_t).total_seconds() > gap:
            runs.append([asset])
            splits += 1
        else:
            runs[-1].append(asset)
    return runs, splits


def _cluster_adjacent_gap_hours(members: list[dict]) -> list[float]:
    """Positive adjacent takenAt gaps (hours) for members with valid timestamps."""
    ordered = sorted(
        members,
        key=lambda a: (
            _parse_taken_at(a.get("takenAt")) or datetime.min.replace(tzinfo=UTC),
            a.get("id") or "",
        ),
    )
    gaps: list[float] = []
    prev_t = _parse_taken_at(ordered[0].get("takenAt")) if ordered else None
    for asset in ordered[1:]:
        cur_t = _parse_taken_at(asset.get("takenAt"))
        if prev_t is not None and cur_t is not None:
            delta_h = (cur_t - prev_t).total_seconds() / 3600.0
            if delta_h > 0:
                gaps.append(delta_h)
        prev_t = cur_t if cur_t is not None else prev_t
    return gaps


def adaptive_soft_split_hours(
    members: list[dict],
    *,
    k: float,
    lo: float,
    hi: float,
    fallback: float,
) -> float:
    """ALG-V3 A3 · clamp(median(gaps_h) * k, [lo, hi]); fallback when sparse.

    Independent of LTN ``coarse_segments`` (seconds / chapter scope).
    """
    if k <= 0:
        return float(fallback)
    lo_v, hi_v = (float(lo), float(hi)) if lo <= hi else (float(hi), float(lo))
    gaps = _cluster_adjacent_gap_hours(members)
    if len(gaps) < 1:
        return float(fallback)
    # Pure-Python median — avoid importing numpy on the SSG hot path.
    ordered = sorted(gaps)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        med = ordered[mid]
    else:
        med = 0.5 * (ordered[mid - 1] + ordered[mid])
    return min(hi_v, max(lo_v, float(med) * float(k)))


def resolve_soft_split_hours(members: list[dict], scene_cfg: Any) -> float:
    """Fixed hours unless ``adaptive_soft_split`` is on."""
    fallback = float(getattr(scene_cfg, "time_soft_split_hours", 6.0) or 6.0)
    if not bool(getattr(scene_cfg, "adaptive_soft_split", False)):
        return fallback
    return adaptive_soft_split_hours(
        members,
        k=float(getattr(scene_cfg, "adaptive_soft_split_k", 3.0) or 3.0),
        lo=float(getattr(scene_cfg, "adaptive_soft_split_hours_lo", 1.0) or 1.0),
        hi=float(getattr(scene_cfg, "adaptive_soft_split_hours_hi", 12.0) or 12.0),
        fallback=fallback,
    )

def _kind_meta(kind: str) -> tuple[float, list[str]]:
    if kind == "scene":
        return 1.0, ["clip_scene", "time_split"]
    if kind == "look":
        return 0.9, ["face_crop", "delta", "clip_torso"]
    return 0.5, ["weak"]


def _assign_group(
    members: list[dict],
    *,
    group_id: str,
    kind: str,
    source_cluster: int | None,
) -> dict[str, Any]:
    conf, signals = _kind_meta(kind)
    medoid = members[0].get("id")
    best_sharp = -1.0
    for a in members:
        sharp = a.get("quality", {})
        if isinstance(sharp, dict):
            s = float(sharp.get("sharpness") or 0.0)
        else:
            s = float(a.get("sharpness") or 0.0)
        if s > best_sharp:
            best_sharp = s
            medoid = a.get("id")
        a["shotGroupId"] = group_id
        a["shotGroupKind"] = kind
        a["shotGroupConfidence"] = conf
    event_id = next((a.get("eventId") for a in members if a.get("eventId")), None)
    out: dict[str, Any] = {
        "id": group_id,
        "kind": kind,
        "assetIds": [str(a.get("id")) for a in members if a.get("id")],
        "medoidAssetId": medoid,
        "sourceSceneClusterId": source_cluster,
        "sourceEventId": event_id,
        "signals": signals,
        "confidence": conf,
    }
    if kind == "look":
        out["lookTrackId"] = "face-main"
    return out


def _apply_look_overrides(
    groups: list[dict[str, Any]],
    assets_by_id: dict[str, dict],
    vectors: Mapping[str, np.ndarray],
    *,
    delta_threshold: float,
    sustain_frames: int,
) -> tuple[list[dict[str, Any]], int]:
    """Split face-eligible members inside each scene/weak group into look groups.

    Look never merges across scene groups (outfit continuity ≠ place continuity).
    Assets without appearance vectors keep the residual scene/weak group.
    """
    if not vectors:
        return groups, 0
    out: list[dict[str, Any]] = []
    look_seq = 0
    for g in groups:
        if g.get("kind") == "look":
            out.append(g)
            continue
        member_ids = [str(aid) for aid in (g.get("assetIds") or [])]
        members = [assets_by_id[aid] for aid in member_ids if aid in assets_by_id]
        with_vec = [a for a in members if str(a.get("id") or "") in vectors]
        without_vec = [a for a in members if str(a.get("id") or "") not in vectors]
        if not with_vec:
            out.append(g)
            continue
        src = g.get("sourceSceneClusterId")
        src_i = int(src) if isinstance(src, int) else None
        segments = split_look_segments(
            with_vec,
            vectors,
            delta_threshold=delta_threshold,
            sustain_frames=sustain_frames,
        )
        for seg in segments:
            if not seg:
                continue
            gid = f"sg-look-{look_seq:02d}"
            look_seq += 1
            out.append(
                _assign_group(
                    seg, group_id=gid, kind="look", source_cluster=src_i
                )
            )
        if without_vec:
            residual = dict(g)
            residual["assetIds"] = [str(a.get("id")) for a in without_vec if a.get("id")]
            for a in without_vec:
                a["shotGroupId"] = residual["id"]
                a["shotGroupKind"] = residual.get("kind") or "scene"
                a["shotGroupConfidence"] = float(residual.get("confidence") or 0.5)
            out.append(residual)
    return out, look_seq


def _merge_small_groups(
    groups: list[dict[str, Any]],
    assets_by_id: dict[str, dict],
    *,
    min_size: int,
) -> list[dict[str, Any]]:
    """Merge tiny scene/weak groups into time-neighbor groups (look never here in M1)."""
    if min_size <= 1 or len(groups) <= 1:
        return groups
    # Sort by earliest takenAt
    def earliest(g: dict) -> str:
        ids = g.get("assetIds") or []
        times = [
            str((assets_by_id.get(aid) or {}).get("takenAt") or "")
            for aid in ids
        ]
        return min(times) if times else ""

    ordered = sorted(groups, key=earliest)
    out: list[dict[str, Any]] = []
    for g in ordered:
        if g.get("kind") == "look":
            out.append(g)
            continue
        n = len(g.get("assetIds") or [])
        if n >= min_size or not out:
            out.append(g)
            continue
        # Merge into previous non-look
        prev = out[-1]
        if prev.get("kind") == "look":
            out.append(g)
            continue
        prev_ids = list(prev.get("assetIds") or [])
        prev_ids.extend(g.get("assetIds") or [])
        prev["assetIds"] = prev_ids
        for aid in g.get("assetIds") or []:
            asset = assets_by_id.get(aid)
            if asset is not None:
                asset["shotGroupId"] = prev["id"]
                asset["shotGroupKind"] = prev.get("kind") or "scene"
        # Drop merged group id
    return out


def run_shot_grouping_layer(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
    look_vectors: Mapping[str, np.ndarray] | None = None,
) -> ShotGroupingResult:
    """Project scene clusters into shot groups (+ optional look). Fail-open on errors.

    ``look_vectors`` is a test/injection hook; production loads CLIP torso cache
    when look is enabled and ``trip_dir`` is set.
    """
    app_cfg = cfg or get_config()
    ssg: ShotGroupingConfig = getattr(app_cfg, "shot_grouping", None) or ShotGroupingConfig()
    assets = _assets_list(trip)
    curation = trip.setdefault("curation", {})

    try:
        has_clusters = _has_scene_clusters(assets)
        vision_ok: bool | None = None
        try:
            from travelogue.vision.clip_encoder import clip_torch_available

            vision_ok = bool(clip_torch_available())
        except Exception:
            vision_ok = False
        if not resolve_shot_grouping_enabled(
            ssg, has_scene_clusters=has_clusters, vision_available=vision_ok
        ):
            _clear_shot_group_fields(assets)
            curation.pop("shotGrouping", None)
            return ShotGroupingResult(mode="off", group_count=0, soft_split_count=0)

        if not has_clusters:
            _clear_shot_group_fields(assets)
            curation.pop("shotGrouping", None)
            return ShotGroupingResult(
                mode="empty",
                group_count=0,
                soft_split_count=0,
                stage_hint="整理分镜…（无场景簇，已跳过）",
            )

        # CQA D-06 / AC-12 · clear orphans before reassign (video / no-cluster / noise)
        _clear_shot_group_fields(assets)

        by_cluster: dict[int, list[dict]] = {}
        noise: list[dict] = []
        for a in assets:
            if a.get("type") == "video":
                continue
            cid = a.get("sceneClusterId")
            if cid is None:
                continue  # D-SSG-24: absent → no strong group
            if cid == -1:
                noise.append(a)
                continue
            by_cluster.setdefault(int(cid), []).append(a)

        groups: list[dict[str, Any]] = []
        soft_splits = 0
        seq = 0
        adaptive_hours: list[float] = []

        for cid, members in sorted(by_cluster.items(), key=lambda x: x[0]):
            split_h = resolve_soft_split_hours(members, ssg.scene)
            if bool(getattr(ssg.scene, "adaptive_soft_split", False)):
                adaptive_hours.append(float(split_h))
            runs, splits = _soft_split_runs(members, split_hours=split_h)
            soft_splits += splits
            for run_i, run in enumerate(runs):
                seq += 1
                suffix = chr(ord("a") + run_i) if len(runs) > 1 and run_i < 26 else str(run_i)
                gid = f"sg-scene-{cid}{suffix}" if len(runs) > 1 else f"sg-scene-{cid}"
                groups.append(
                    _assign_group(
                        run, group_id=gid, kind="scene", source_cluster=cid
                    )
                )

        if ssg.scene.merge_noise and noise:
            # Each noise asset as weak singleton; merge pass may coalesce
            for i, a in enumerate(noise):
                seq += 1
                groups.append(
                    _assign_group(
                        [a],
                        group_id=f"sg-weak-{i}",
                        kind="weak",
                        source_cluster=-1,
                    )
                )
        else:
            for a in noise:
                a.pop("shotGroupId", None)
                a.pop("shotGroupKind", None)
                a.pop("shotGroupConfidence", None)

        assets_by_id = {str(a.get("id")): a for a in assets if a.get("id")}
        groups = _merge_small_groups(
            groups, assets_by_id, min_size=ssg.min_shot_group_size
        )

        look_stats: dict[str, int | float] = {
            "lookSkippedNoFace": 0,
            "lookSkippedMulti": 0,
            "lookEncoded": 0,
            "lookCacheHits": 0,
        }
        look_n = 0
        want_look = resolve_look_enabled(ssg.look, clip_available=vision_ok)
        if want_look:
            vectors: Mapping[str, np.ndarray] = look_vectors or {}
            if look_vectors is None and trip_dir is not None:
                try:
                    from travelogue.vision.look_appearance import (
                        compute_look_vectors_for_assets,
                    )

                    vectors, look_stats = compute_look_vectors_for_assets(
                        assets,
                        trip_dir=trip_dir,
                        cfg=ssg,
                        app_cfg=app_cfg,
                    )
                except Exception:
                    _log.exception("look appearance encode failed; keep scene groups")
                    vectors = {}
            elif look_vectors is None and trip_dir is None:
                _log.debug("look enabled but no trip_dir; skip look")
            if vectors:
                groups, look_n = _apply_look_overrides(
                    groups,
                    assets_by_id,
                    vectors,
                    delta_threshold=ssg.look.delta_threshold,
                    sustain_frames=ssg.look.sustain_frames,
                )

        scene_n = sum(1 for g in groups if g.get("kind") == "scene")
        weak_n = sum(1 for g in groups if g.get("kind") == "weak")
        look_n = sum(1 for g in groups if g.get("kind") == "look")
        coverage = shot_group_coverage_ratio(assets)
        soft_split_meta: dict[str, Any] = {
            "softSplitAdaptive": bool(getattr(ssg.scene, "adaptive_soft_split", False)),
        }
        if adaptive_hours:
            soft_split_meta["softSplitHoursEffective"] = round(
                float(sorted(adaptive_hours)[len(adaptive_hours) // 2]), 4
            )
        telemetry = {
            "mode": "scene",
            "groupCount": len(groups),
            "sceneGroupCount": scene_n,
            "lookGroupCount": look_n,
            "weakGroupCount": weak_n,
            "softSplitCount": soft_splits,
            "coverageRatio": round(coverage, 4),
            "lookEnabled": want_look,
            **soft_split_meta,
            **look_stats,
        }
        curation["shotGrouping"] = {
            "version": SHOT_GROUPING_VERSION,
            "groups": groups,
            "stats": {
                "sceneGroupCount": scene_n,
                "lookGroupCount": look_n,
                "weakGroupCount": weak_n,
                "softSplitCount": soft_splits,
                "coverageRatio": round(coverage, 4),
                **soft_split_meta,
                **look_stats,
            },
            "telemetry": telemetry,
        }
        if trip_dir is not None:
            try:
                from travelogue.curation.shot_group_decision_log import (
                    write_shot_grouping_decision_log,
                )

                write_shot_grouping_decision_log(trip_dir, telemetry)
            except Exception:
                _log.debug("shot_grouping decision log write skipped", exc_info=True)
        hint = f"整理分镜…（{len(groups)} 组"
        if look_n:
            hint += f" · {look_n} 造型"
        hint += "）"
        return ShotGroupingResult(
            mode="scene",
            group_count=len(groups),
            soft_split_count=soft_splits,
            look_group_count=look_n,
            stage_hint=hint,
        )
    except Exception:
        _log.exception("shot_grouping failed; fail-open")
        _clear_shot_group_fields(assets)
        curation.pop("shotGrouping", None)
        return ShotGroupingResult(mode="off", group_count=0, soft_split_count=0)
