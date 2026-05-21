"""Unified demo: album → ingest → curate → render (single pipeline)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config import get_config
from travelogue.util.trip_slug import demo_trip_id_from_album
from travelogue.paths import DEMO_CONFIG_PATH
from travelogue.curation.curate import CurateError, run_curate
from travelogue.media.ingest import IngestError, ingest_into_trip, scan_image_paths
from travelogue.orchestrator.pipeline import PublishResult
from travelogue.orchestrator.run import RunResult, run_trip
from travelogue.render.engine import render_trip, render_trip_surfaces
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip


class DemoError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class DemoResult:
    trip_dir: Path
    trip_json: Path
    index_html: Path
    photo_count: int
    stats: dict = field(default_factory=dict)
    stages: list[str] = field(default_factory=list)
    layout_summary: str = ""
    zip_path: Path | None = None
    publish: PublishResult | None = None


def _wrap_ingest_error(exc: IngestError) -> DemoError:
    code = exc.code
    if code in ("E_INGEST_TOO_FEW", "E_INGEST_EMPTY"):
        return DemoError("E_DEMO_TOO_FEW", str(exc))
    return DemoError(code, str(exc))


def publish_demo_trip(
    trip_json: Path,
    *,
    confirm_privacy: bool = True,
    validate: bool = False,
    no_preview: bool = False,
) -> RunResult:
    """Auto lock → narrate → export share zip from a demo workspace."""
    return run_trip(
        trip_json,
        from_stage="lock_structure",
        until="exported",
        confirm_privacy=confirm_privacy,
        no_preview=no_preview,
        validate=validate,
        skip_locked=True,
    )


def resolve_demo_config(explicit: Path | None = None) -> Path | None:
    """Prefer explicit --config, else config.demo.yaml in repo root."""
    if explicit is not None:
        return explicit
    return DEMO_CONFIG_PATH if DEMO_CONFIG_PATH.is_file() else None


def run_demo_from_album(
    album_dir: Path,
    *,
    trips_dir: Path | None = None,
    trip_id: str | None = None,
    title: str = "我的旅途",
    place: str = "旅途",
    hook: str = "",
    max_photos: int = 50,
    recursive: bool = True,
    render: bool = True,
    export_layout: str = "mobile",
    force: bool = False,
    dedupe: bool = True,
    validate: bool = False,
    config: Path | None = None,
    publish: bool = False,
    confirm_privacy: bool = True,
    no_preview: bool = False,
) -> DemoResult:
    """
    One-shot demo using the same services as ``travelogue ingest`` / ``curate`` / ``render``.

    Leaves trip at ``structure_draft`` (+ ``rendered`` if render=True) unless ``publish=True``,
    which runs lock → narrate → share render → zip.
    """
    album_dir = album_dir.resolve()
    if not album_dir.is_dir():
        raise DemoError("E_DEMO_NOT_DIR", f"not a directory: {album_dir}")

    cfg_path = resolve_demo_config(config)
    if cfg_path:
        get_config(reload=True, path=cfg_path)
    cfg = get_config()
    trips_root = trips_dir or cfg.trips_dir
    slug = demo_trip_id_from_album(
        album_dir, title=title, place=place, explicit=trip_id
    )
    trip_dir = trips_root / slug

    if trip_dir.exists() and any(trip_dir.iterdir()):
        if not force:
            raise DemoError(
                "E_DEMO_EXISTS",
                f"trip already exists: {trip_dir} (use --force to replace)",
            )
        shutil.rmtree(trip_dir)

    trip_json = create_trip(
        slug,
        trips_root,
        title=title,
        place=place,
        export_layout=export_layout,
    )
    trip_root = trip_json.parent
    svc = TripService(root=trips_root.parent)
    trip = svc.load(trip_json)

    stages: list[str] = []
    stats: dict = {}

    try:
        ingest_result = ingest_into_trip(
            trip,
            trip_root,
            from_dir=album_dir,
            max_photos=max_photos,
            recursive=recursive,
            dedupe=dedupe,
        )
    except IngestError as exc:
        raise _wrap_ingest_error(exc) from exc

    stages.append("ingest")
    stats.update(ingest_result.stats)
    stats["ingest_added"] = ingest_result.added
    stats["ingest_skipped"] = ingest_result.skipped

    meta = trip.setdefault("meta", {})
    meta["title"] = title[:20]
    if place and place not in (meta.get("places") or []):
        meta["places"] = [place]
    if hook:
        meta["hook"] = hook[:56]

    try:
        curate_result = run_curate(
            trip,
            export_layout=export_layout,
            apply_layout=True,
            trip_dir=trip_root,
        )
    except CurateError as exc:
        raise DemoError(exc.code, str(exc)) from exc

    stages.append("curate")
    stats["layout_summary"] = curate_result.layout_summary
    stats["chapter_count"] = curate_result.chapter_count
    stats["cover_asset_id"] = curate_result.cover_asset_id

    orient = (trip.get("curation") or {}).get("orientationSummary") or {}
    stats.update(orient)

    svc.save(trip, trip_json)

    index_html = trip_root / "index.html"
    if render:
        trip = svc.load(trip_json)
        surface = trip.get("exportLayout", export_layout)
        if surface == "auto":
            web_path, mobile_path = render_trip_surfaces(
                trip_json, trip_root, export_mode="draft", validate=validate, update_pipeline=True
            )
            index_html = web_path
            stats["index_mobile_html"] = str(mobile_path)
        else:
            render_trip(
                trip_json, trip_root, export_mode="draft", validate=validate, update_pipeline=True
            )
        stages.append("render")
        trip = svc.load(trip_json)

    photo_count = len(trip.get("assets") or [])
    zip_path: Path | None = None
    publish_result: PublishResult | None = None

    if publish:
        if not render:
            render_trip(trip_json, trip_root, export_mode="draft", validate=validate, update_pipeline=True)
            stages.append("render")
        try:
            run_result = publish_demo_trip(
                trip_json,
                confirm_privacy=confirm_privacy,
                validate=validate,
                no_preview=no_preview,
            )
        except Exception as exc:
            raise DemoError(getattr(exc, "code", "E_DEMO_PUBLISH"), str(exc)) from exc
        stages.extend(run_result.stages)
        publish_result = run_result.publish
        if publish_result:
            zip_path = publish_result.zip_path

    return DemoResult(
        trip_dir=trip_root,
        trip_json=trip_json,
        index_html=index_html,
        photo_count=photo_count,
        stats=stats,
        stages=stages,
        layout_summary=curate_result.layout_summary,
        zip_path=zip_path,
        publish=publish_result,
    )
