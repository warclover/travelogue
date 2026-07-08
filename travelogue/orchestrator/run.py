"""Chain pipeline stages: ingest → curate → narrate → render → export."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.curation.curate import run_curate
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.orchestrator.pipeline import PublishResult, publish_trip
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.orchestrator.studio_profile import StudioProfile
from travelogue.render.engine import render_trip, render_trip_surfaces
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.layout import apply_layout_to_trip
from travelogue.services.narrate import run_narrate
from travelogue.services.pipeline_state import Until, assert_stage_allowed, lock_copy, lock_structure, set_pipeline_timings, trip_status
from travelogue.services.trip import persist_trip_snapshot


@dataclass
class RunResult:
    stages: list[str] = field(default_factory=list)
    trip_path: Path | None = None
    publish: PublishResult | None = None


def run_trip(
    trip_path: Path,
    *,
    from_stage: str = "ingest",
    until: Until = "rendered",
    album_dir: Path | None = None,
    export_layout: str = "mobile",
    confirm_privacy: bool = False,
    no_preview: bool = False,
    validate: bool = True,
    skip_locked: bool = True,
    dedupe: bool = True,
    narrate_provider: str | None = None,
    regenerate: bool = False,
    cfg: AppConfig | None = None,
    studio_hooks: StudioHooks | None = None,
    studio_profile: StudioProfile | None = None,
) -> RunResult:
    profile = studio_profile or StudioProfile.cli_default()
    with app_config_scope(cfg):
        return _run_trip_stages(
            trip_path,
            from_stage=from_stage,
            until=until,
            album_dir=album_dir,
            export_layout=export_layout,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            validate=validate,
            skip_locked=skip_locked,
            dedupe=dedupe,
            narrate_provider=narrate_provider,
            regenerate=regenerate,
            studio_hooks=studio_hooks,
            studio_profile=profile,
        )


def _run_trip_stages(
    trip_path: Path,
    *,
    from_stage: str = "ingest",
    until: Until = "rendered",
    album_dir: Path | None = None,
    export_layout: str = "mobile",
    confirm_privacy: bool = False,
    no_preview: bool = False,
    validate: bool = True,
    skip_locked: bool = True,
    dedupe: bool = True,
    narrate_provider: str | None = None,
    regenerate: bool = False,
    studio_hooks: StudioHooks | None = None,
    studio_profile: StudioProfile | None = None,
) -> RunResult:
    profile = studio_profile or StudioProfile.cli_default()
    effective_export_layout = profile.export_layout or export_layout
    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    svc = app_context_for_trip_json(trip_path).trip_service()
    trip = svc.load(trip_path)
    result = RunResult(trip_path=trip_path)
    status = (trip.get("pipeline") or {}).get("status", "")
    locks = (trip.get("pipeline") or {}).get("locks") or {}

    def save() -> None:
        persist_trip_snapshot(svc, trip_path, trip)

    stages_order = [
        "ingest",
        "clustering",
        "curate",
        "layout",
        "lock_structure",
        "narrate",
        "lock_copy",
        "render",
        "export",
    ]
    start_idx = stages_order.index(from_stage) if from_stage in stages_order else 0

    until_map = {
        "ingest": "ingest",
        "structure": "curate",
        "layout": "layout",
        "copy": "lock_copy",
        "rendered": "render",
        "exported": "export",
    }
    stop_stage = until_map.get(until, "render")

    stage_index = {
        "ingest": 1,
        "clustering": 2,
        "curate": 2,
        "layout": 2,
        "lock_structure": 2,
        "narrate": 3,
        "lock_copy": 3,
        "render": 4,
        "export": 4,
    }
    pipeline_timings: dict[str, float] = dict((trip.get("pipeline") or {}).get("timings") or {})
    pipeline_t0 = time.monotonic()

    def flush_timings(*, extra: dict[str, float] | None = None) -> None:
        if extra:
            pipeline_timings.update(extra)
        pipeline_timings["totalMs"] = round((time.monotonic() - pipeline_t0) * 1000.0, 2)
        set_pipeline_timings(trip, pipeline_timings)
        if studio_hooks is not None:
            studio_hooks.report_timing(pipeline_timings)

    for stage in stages_order[start_idx:]:
        if stages_order.index(stage) > stages_order.index(stop_stage):
            break
        if studio_hooks is not None:
            studio_hooks.report(stage, stage_index.get(stage, 0))

        if stage == "ingest":
            if album_dir is None:
                raise IngestError("E_RUN_NO_ALBUM", "run --from ingest requires album path via --from-dir")
            assert_stage_allowed(trip, "ingest")
            ingest_t0 = time.monotonic()
            ingest_opts = profile.ingest
            parallel_embed = None
            ingest_asset_added = ingest_opts.on_asset_added
            if ingest_opts.use_parallel_embed and get_config().pipeline.parallel_embed:
                cfg_obj = get_config()
                if cfg_obj.vision.enabled != "false":
                    from travelogue.vision.parallel_embed import ParallelEmbedCoordinator

                    parallel_embed = ParallelEmbedCoordinator(
                        trip_root,
                        cfg=cfg_obj,
                        chunk_size=cfg_obj.pipeline.parallel_embed_chunk,
                    )
                    prior_added = ingest_opts.on_asset_added

                    def ingest_asset_added(entry: dict) -> None:
                        parallel_embed.offer(entry)
                        if prior_added is not None:
                            prior_added(entry)

            ingest_into_trip(
                trip,
                trip_root,
                from_dir=album_dir,
                generate_crops=ingest_opts.generate_crops,
                dedupe=dedupe,
                max_photos=ingest_opts.max_photos,
                app_cfg=get_config(),
                featured_dir=ingest_opts.featured_dir,
                material_dir=ingest_opts.material_dir,
                on_progress=ingest_opts.on_progress,
                on_cull_hint=ingest_opts.on_cull_hint,
                on_persist=ingest_opts.on_persist,
                on_asset_added=ingest_asset_added,
                resume_ingest=ingest_opts.resume_ingest,
            )
            if parallel_embed is not None:
                parallel_embed.finish()
            pipeline_timings["ingestMs"] = round((time.monotonic() - ingest_t0) * 1000.0, 2)
            flush_timings()
            result.stages.append("ingest")
            save()

        elif stage == "clustering":
            if not profile.run_clustering:
                continue
            assert_stage_allowed(trip, "clustering")
            if profile.apply_editorial_hints:
                from travelogue.curation.intent_hints import apply_editorial_intent_hints

                apply_editorial_intent_hints(trip)
            from travelogue.curation.clustering import run_clustering_layer

            cluster_t0 = time.monotonic()
            cluster_result = run_clustering_layer(trip, trip_dir=trip_root, cfg=get_config())
            pipeline_timings["clusterMs"] = round((time.monotonic() - cluster_t0) * 1000.0, 2)
            cluster_meta = (trip.get("curation") or {}).get("clustering") or {}
            embed_stats = cluster_meta.get("embedStats") or {}
            if cluster_meta.get("embedSkipped"):
                pipeline_timings["embedMs"] = 0.0
            else:
                pipeline_timings["embedMs"] = float(embed_stats.get("elapsedMs") or 0.0)
            flush_timings()
            if cluster_result.stage_hint and studio_hooks is not None:
                studio_hooks.report("curate", stage_index.get("curate", 2), cluster_result.stage_hint)
            result.stages.append("clustering")
            save()

        elif stage == "curate":
            assert_stage_allowed(trip, "curate")
            curate_t0 = time.monotonic()
            run_curate(
                trip,
                export_layout=effective_export_layout,
                apply_layout=profile.apply_layout_on_curate,
                trip_dir=trip_root,
            )
            pipeline_timings["curateMs"] = round((time.monotonic() - curate_t0) * 1000.0, 2)
            flush_timings()
            result.stages.append("curate")
            save()

        elif stage == "layout":
            assert_stage_allowed(trip, "layout")
            layout_t0 = time.monotonic()
            apply_layout_to_trip(trip, export_layout=effective_export_layout, cfg=get_config())
            pipeline_timings["layoutMs"] = round((time.monotonic() - layout_t0) * 1000.0, 2)
            flush_timings()
            result.stages.append("layout")
            save()

        elif stage == "lock_structure":
            if status == "structure_locked" and locks.get("structure") and skip_locked:
                continue
            assert_stage_allowed(trip, "lock_structure")
            lock_structure(trip)
            result.stages.append("lock_structure")
            save()
            status = trip_status(trip)

        elif stage == "narrate":
            if status == "copy_locked" and skip_locked:
                continue
            assert_stage_allowed(trip, "narrate")
            cache_dir = trip_root / ".cache" / "narrate"
            narrate_t0 = time.monotonic()
            run_narrate(
                trip,
                provider=narrate_provider,
                regenerate=regenerate,
                cache_dir=cache_dir,
            )
            pipeline_timings["narrateMs"] = round((time.monotonic() - narrate_t0) * 1000.0, 2)
            flush_timings()
            result.stages.append("narrate")
            save()

        elif stage == "lock_copy":
            if status == "copy_locked" and skip_locked:
                continue
            assert_stage_allowed(trip, "lock_copy")
            lock_copy(trip)
            result.stages.append("lock_copy")
            save()

        elif stage == "render":
            if status == "rendered" and skip_locked:
                continue
            trip = svc.load(trip_path)
            render_t0 = time.monotonic()
            if trip.get("exportLayout") == "auto":
                render_trip_surfaces(
                    trip_path,
                    trip_root,
                    export_mode="draft",
                    validate=validate,
                    update_pipeline=True,
                )
            else:
                render_trip(
                    trip_path,
                    trip_root,
                    export_mode="draft",
                    validate=validate,
                    update_pipeline=True,
                )
            pipeline_timings["renderMs"] = round((time.monotonic() - render_t0) * 1000.0, 2)
            trip = svc.load(trip_path)
            flush_timings()
            persist_trip_snapshot(svc, trip_path, trip)

            result.stages.append("render")

        elif stage == "export":
            export_t0 = time.monotonic()
            pub = publish_trip(
                trip_path,
                confirm_privacy=confirm_privacy,
                no_preview=no_preview,
                validate=validate,
            )
            pipeline_timings["exportMs"] = round((time.monotonic() - export_t0) * 1000.0, 2)
            trip = svc.load(trip_path)
            flush_timings()
            persist_trip_snapshot(svc, trip_path, trip)
            result.publish = pub
            result.stages.append("export")

    pipeline_timings["totalMs"] = round((time.monotonic() - pipeline_t0) * 1000.0, 2)
    trip = svc.load(trip_path)
    flush_timings()
    persist_trip_snapshot(svc, trip_path, trip)

    return result
