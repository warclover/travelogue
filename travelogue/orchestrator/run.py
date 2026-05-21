"""Chain pipeline stages: ingest → curate → narrate → render → export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from travelogue.curation.curate import CurateError, run_curate
from travelogue.export.packager import ExportError, export_trip
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.orchestrator.pipeline import PublishResult, publish_trip
from travelogue.render.engine import RenderError, render_trip, render_trip_surfaces
from travelogue.services.layout import LayoutError, apply_layout_to_trip
from travelogue.services.narrate import run_narrate
from travelogue.services.pipeline_state import PipelineError, Until, assert_stage_allowed
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

    for stage in stages_order[start_idx:]:
        if stages_order.index(stage) > stages_order.index(stop_stage):
            break

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
            apply_layout_to_trip(trip, export_layout=export_layout)
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
            run_narrate(trip)
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
