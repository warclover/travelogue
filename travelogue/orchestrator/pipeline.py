"""Validate → render (share) → preview → export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope
from travelogue.export.packager import export_trip
from travelogue.render.engine import RenderError, render_trip
from travelogue.render.preview import render_preview_jpg
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.validate import validate_trip


@dataclass
class PublishResult:
    trip_path: Path
    index_html: Path
    preview_jpg: Path | None
    zip_path: Path


def publish_trip(
    trip_path: Path,
    *,
    confirm_privacy: bool = True,
    no_preview: bool = False,
    output_zip: Path | None = None,
    validate: bool = True,
    cfg: AppConfig | None = None,
) -> PublishResult:
    """Full Agent 3 publish path for a trip.json workspace."""
    with app_config_scope(cfg):
        return _publish_trip_stages(
            trip_path,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            output_zip=output_zip,
            validate=validate,
        )


def _publish_trip_stages(
    trip_path: Path,
    *,
    confirm_privacy: bool = True,
    no_preview: bool = False,
    output_zip: Path | None = None,
    validate: bool = True,
) -> PublishResult:
    trip_path = trip_path.resolve()
    trip_root = trip_path.parent

    if validate:
        trip = app_context_for_trip_json(trip_path).trip_service().load(trip_path)
        errs = [e for e in validate_trip(trip) if not e.startswith("WARN:")]
        if errs:
            first = errs[0]
            from travelogue.services.validate import validation_error_code

            raise RenderError(validation_error_code(first), first)

    render_trip(trip_path, trip_root, export_mode="share", validate=False)

    preview: Path | None = None
    if not no_preview:
        preview = render_preview_jpg(trip_path, trip_root=trip_root)

    zip_path = export_trip(
        trip_path,
        output_zip=output_zip,
        confirm_privacy=confirm_privacy,
        no_preview=True,  # already generated
        validate=False,
        auto_render=False,  # already rendered
    )

    return PublishResult(
        trip_path=trip_path,
        index_html=trip_root / "index.html",
        preview_jpg=preview,
        zip_path=zip_path,
    )
