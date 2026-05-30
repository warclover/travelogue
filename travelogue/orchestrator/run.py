"""Chain pipeline stages: ingest → curate → narrate → render → export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope
from travelogue.curation.curate import CurateError, run_curate
from travelogue.export.packager import ExportError, export_trip
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.orchestrator.pipeline import PublishResult, publish_trip
from travelogue.render.engine import RenderError, render_trip, render_trip_surfaces
from travelogue.services.layout import LayoutError, apply_layout_to_trip
from travelogue.services.narrate import run_narrate
from travelogue.services.pipeline_state import PipelineError, Until, assert_stage_allowed
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.services.trip import TripService


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
) -> RunResult:
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
) -> RunResult:
    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    svc = TripService()
    trip = svc.load(trip_path)
    result = RunResult(trip_path=trip_path)
    status = (trip.get("pipeline") or {}).get("status", "")
    locks = (trip.get("pipeline") or {}).get("locks") or {}

    def save() -> None:
        svc.save(trip, trip_path)

    stages_order = ["ingest", "curate", "layout", "lock_structure", "narrate", "lock_copy", "render", "export"]
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
        "curate": 2,
        "layout": 2,
        "lock_structure": 2,
        "narrate": 3,
        "lock_copy": 3,
        "render": 4,
        "export": 4,
    }

    for stage in stages_order[start_idx:]:
        if stages_order.index(stage) > stages_order.index(stop_stage):
            break
        if studio_hooks is not None:
            studio_hooks.report(stage, stage_index.get(stage, 0))

        if stage == "ingest":
            if album_dir is None:
                raise IngestError("E_RUN_NO_ALBUM", "run --from ingest requires album path via --from-dir")
            assert_stage_allowed(trip, "ingest")
            ingest_into_trip(
                trip,
                trip_root,
                from_dir=album_dir,
                generate_crops=False,
                dedupe=dedupe,
            )
            result.stages.append("ingest")
            save()

        elif stage == "curate":
            assert_stage_allowed(trip, "curate")
            run_curate(
                trip,
                export_layout=export_layout,
                apply_layout=True,
                trip_dir=trip_root,
            )
            result.stages.append("curate")
            save()

        elif stage == "layout":
            assert_stage_allowed(trip, "layout")
            apply_layout_to_trip(trip, export_layout=export_layout, cfg=get_config())
            result.stages.append("layout")
            save()

        elif stage == "lock_structure":
            if status == "structure_locked" and locks.get("structure") and skip_locked:
                continue
            assert_stage_allowed(trip, "lock_structure")
            pipe = trip.setdefault("pipeline", {})
            pipe["locks"]["structure"] = True
            pipe["status"] = "structure_locked"
            result.stages.append("lock_structure")
            save()
            status = pipe["status"]

        elif stage == "narrate":
            if status == "copy_locked" and skip_locked:
                continue
            assert_stage_allowed(trip, "narrate")
            cache_dir = trip_root / ".cache" / "narrate"
            run_narrate(
                trip,
                provider=narrate_provider,
                regenerate=regenerate,
                cache_dir=cache_dir,
            )
            result.stages.append("narrate")
            save()

        elif stage == "lock_copy":
            if status == "copy_locked" and skip_locked:
                continue
            assert_stage_allowed(trip, "lock_copy")
            pipe = trip.setdefault("pipeline", {})
            pipe["locks"]["copy"] = True
            pipe["status"] = "copy_locked"
            result.stages.append("lock_copy")
            save()

        elif stage == "render":
            if status == "rendered" and skip_locked:
                continue
            trip = svc.load(trip_path)
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
            trip = svc.load(trip_path)
            result.stages.append("render")
            save()

        elif stage == "export":
            pub = publish_trip(
                trip_path,
                confirm_privacy=confirm_privacy,
                no_preview=no_preview,
                validate=validate,
            )
            result.publish = pub
            result.stages.append("export")

    return result
