"""ClusteringLayer integration · Phase 3 M12/M13."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from travelogue.config import AppConfig
from travelogue.curation.cluster_decision_log import ClusterDecisionLog
from travelogue.curation.curate import layout_eligible_assets
from travelogue.curation.geo_events import GeoSegment, detect_geo_events, gps_coverage_ratio
from travelogue.curation.scene_clusters import assign_scene_cluster_fields, compute_scene_clusters
from travelogue.vision.cache import prepare_scene_embeddings, embedding_cache_is_corrupt
from travelogue.vision.clip_encoder import ClipEncoder, clip_torch_available, clip_weights_likely_cached, vision_stack_available

_log = logging.getLogger(__name__)

ClusteringMode = Literal["off", "lite", "full"]

# Lower bound on the scene-clustering timeout. Exposed as a module attribute
# so regression tests can shrink it for fast verification of the timeout path.
_MIN_SCENE_TIMEOUT_SEC = 30


def _vision_downgrade_notice(log: ClusterDecisionLog, want_vision: bool, scene_count: int) -> str:
    """Non-blocking toast copy when P3-Full vision was requested but skipped (UX-P3-08)."""
    if not want_vision or scene_count > 0:
        return ""
    for entry in log.entries:
        detail = str(entry.get("detail") or "")
        if "E_CLUSTER_VISION_TIMEOUT" in detail:
            return "场景分析耗时较长，已按行程与日期排版完成"
        if "E_CLUSTER_VISION_MISSING" in detail:
            return ""
        if entry.get("kind") == "fallback" and "scene" in detail.lower():
            return "场景分析未完成，已按行程与日期排版完成"
    return ""


def resolve_clustering_mode(assets: list[dict], cfg: AppConfig) -> ClusteringMode:
    enabled = cfg.clustering.enabled
    if enabled == "false":
        return "off"
    if enabled == "true":
        return "lite"
    ratio = gps_coverage_ratio(assets)
    if ratio >= cfg.clustering.auto_gps_min_ratio:
        return "lite"
    return "off"


def resolve_vision_mode(assets: list[dict], cfg: AppConfig) -> bool:
    enabled = cfg.vision.enabled
    if enabled == "false":
        return False
    if enabled == "true":
        return True
    eligible = layout_eligible_assets({"assets": assets})
    if not eligible:
        return False
    if len(eligible) < cfg.vision.auto_min_photos:
        return False
    ratio = len(eligible) / max(1, len(assets))
    return ratio >= cfg.vision.auto_min_eligible_ratio


@dataclass
class ClusteringResult:
    mode: ClusteringMode
    segment_mode: str
    geo_event_count: int = 0
    scene_cluster_count: int = 0
    stage_hint: str = ""
    user_notice: str = ""


@dataclass
class _GeoStage:
    """Outcome of geo-event detection step."""

    segment_mode: str
    segments: list[GeoSegment] = field(default_factory=list)


class ClusteringLayer:
    def run(
        self,
        trip: dict,
        assets: list[dict] | None = None,
        *,
        trip_dir: Path,
        cfg: AppConfig,
        pipeline_run_id: str | None = None,
    ) -> ClusteringResult:
        body = assets if assets is not None else layout_eligible_assets(trip)
        log = ClusterDecisionLog(pipeline_run_id=pipeline_run_id)

        skip = self._resolve_skip(body, cfg, log)
        if skip is not None:
            log.write(trip_dir)
            return skip

        geo = self._run_geo(trip, body, cfg=cfg, log=log)

        want_vision = resolve_vision_mode(body, cfg)
        scene_count = 0
        vision_hint = ""
        if want_vision:
            scene_count, vision_hint = self._run_scene_clustering(
                trip, body, trip_dir=trip_dir, cfg=cfg, log=log
            )

        effective_mode = self._resolve_effective_mode(geo, scene_count)
        hint = self._build_stage_hint(geo, scene_count, vision_hint)
        user_notice = _vision_downgrade_notice(log, want_vision, scene_count)
        log.write(trip_dir)
        return ClusteringResult(
            mode=effective_mode,
            segment_mode=geo.segment_mode,
            geo_event_count=len(geo.segments),
            scene_cluster_count=scene_count,
            stage_hint=hint,
            user_notice=user_notice,
        )

    @staticmethod
    def _resolve_skip(
        assets: list[dict],
        cfg: AppConfig,
        log: ClusterDecisionLog,
    ) -> ClusteringResult | None:
        mode = resolve_clustering_mode(assets, cfg)
        if mode == "off":
            log.add("cluster_skip", "clustering.enabled=off or auto GPS below threshold")
            return ClusteringResult(mode="off", segment_mode="date_fallback")
        if cfg.clustering.segment_curate_mode == "date_fallback":
            log.add("fallback", "segmentCurateMode=date_fallback")
            return ClusteringResult(mode="off", segment_mode="date_fallback")
        return None

    @staticmethod
    def _run_geo(
        trip: dict,
        assets: list[dict],
        *,
        cfg: AppConfig,
        log: ClusterDecisionLog,
    ) -> _GeoStage:
        try:
            segments = detect_geo_events(
                assets,
                cfg=cfg.clustering.geo,
                meta=trip.get("meta") or {},
                intent=trip.get("intent"),
            )
        except Exception as exc:
            _log.warning("geo_events failed: %s", exc, exc_info=True)
            log.add("fallback", f"geo_events error: {exc}")
            return _GeoStage(segment_mode="date_fallback")

        if not segments:
            log.add("fallback", "no GPS segments; curate uses time_segments")
            return _GeoStage(segment_mode="date_fallback")

        trip.setdefault("curation", {})["clustering"] = {
            "version": "1",
            "segmentMode": "geo_event",
            "segments": [s.to_dict() for s in segments],
        }
        by_id = {a["id"]: a for a in trip.get("assets") or []}
        for seg in segments:
            for aid in seg.asset_ids:
                asset = by_id.get(aid)
                if asset is not None:
                    asset["eventId"] = seg.id
        log.add(
            "segment_source",
            "segmentMode=geo_event",
            input_summary=f"eventCount={len(segments)}",
        )
        return _GeoStage(segment_mode="geo_event", segments=segments)

    @staticmethod
    def _resolve_effective_mode(geo: _GeoStage, scene_count: int) -> ClusteringMode:
        if scene_count > 0:
            return "full"
        if geo.segments:
            return "lite"
        return "off"

    @staticmethod
    def _build_stage_hint(geo: _GeoStage, scene_count: int, vision_hint: str) -> str:
        if scene_count > 0:
            return vision_hint or "正在分析场景与行程…"
        if vision_hint:
            return vision_hint
        if geo.segments:
            return "正在识别行程…"
        return ""

    def _run_scene_clustering(
        self,
        trip: dict,
        assets: list[dict],
        *,
        trip_dir: Path,
        cfg: AppConfig,
        log: ClusterDecisionLog,
    ) -> tuple[int, str]:
        if not vision_stack_available():
            log.add("fallback", "E_CLUSTER_VISION_MISSING: numpy/sklearn not installed")
            return 0, ""

        if cfg.clustering.scene_cluster_mode == "off":
            log.add("cluster_skip", "sceneClusterMode=off")
            return 0, ""

        hints: list[str] = []
        if clip_torch_available() and not clip_weights_likely_cached(
            model_name=cfg.vision.model.replace("/", "-")
        ):
            hints.append("正在准备场景分析组件（仅首次）…")
        if embedding_cache_is_corrupt(trip_dir):
            log.add("fallback", "E_CLUSTER_CACHE_CORRUPT: rebuilding cluster cache")
            hints.append("正在重新分析场景…")

        scene_cfg = cfg.clustering.scene
        timeout = max(_MIN_SCENE_TIMEOUT_SEC, int(scene_cfg.timeout_sec))

        def _work() -> tuple[int, str]:
            encoder = ClipEncoder(
                model_name=cfg.vision.model.replace("/", "-"),
                subject_prompts=cfg.vision.subject_prompts or None,
            )
            embed, cache_plan = prepare_scene_embeddings(
                trip_dir,
                assets,
                encoder,
                force_recluster=cfg.clustering.force_recluster,
                deterministic=cfg.clustering.deterministic,
            )
            log.add(
                "cache_plan",
                f"mode={cache_plan.mode}",
                input_summary=(
                    f"change={cache_plan.change_ratio:.2f} "
                    f"new={len(cache_plan.new_ids)} removed={len(cache_plan.removed_ids)}"
                ),
            )
            if not embed.asset_ids:
                return 0, ""
            clusters = compute_scene_clusters(
                embed.asset_ids,
                embed.vectors,
                eps=scene_cfg.cluster_eps,
                min_samples=scene_cfg.cluster_min_samples,
                deterministic=cfg.clustering.deterministic,
            )
            assign_scene_cluster_fields(
                trip,
                embed.asset_ids,
                embed.vectors,
                clusters,
                cluster_source=embed.source,
                model=embed.model,
            )
            log.add(
                "cluster_assign",
                f"scene clusters via {embed.source}",
                input_summary=f"clusterCount={len(clusters)}",
            )
            return len(clusters), hints[-1] if hints else "正在分析场景与行程…"

        # NOTE: Python threads cannot be killed. We deliberately drop the pool
        # with wait=False on timeout/failure so the surrounding pipeline can
        # honor cfg.clustering.scene.timeout_sec instead of blocking on shutdown.
        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="clip-cluster")
        try:
            future = pool.submit(_work)
            count, work_hint = future.result(timeout=timeout)
            return count, hints[0] if hints else work_hint
        except FuturesTimeoutError:
            log.add("fallback", "E_CLUSTER_VISION_TIMEOUT: scene analysis skipped")
            return 0, ""
        except Exception as exc:
            _log.warning("scene clustering failed: %s", exc, exc_info=True)
            log.add("fallback", f"scene cluster error: {exc}")
            return 0, ""
        finally:
            pool.shutdown(wait=False)


def run_clustering_layer(
    trip: dict,
    *,
    trip_dir: Path,
    cfg: AppConfig,
    pipeline_run_id: str | None = None,
) -> ClusteringResult:
    return ClusteringLayer().run(
        trip,
        trip_dir=trip_dir,
        cfg=cfg,
        pipeline_run_id=pipeline_run_id,
    )
