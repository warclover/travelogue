"""Shared CLI helpers."""

from __future__ import annotations

from pathlib import Path

import typer

from travelogue.config import get_config
from travelogue.demo.build import DemoError, resolve_demo_config, run_demo_from_album
from travelogue.runtime import app_context_for_trip_json, app_context_for_trips_dir
from travelogue.services.trip import TripNotFoundError, TripService


def _load_cfg(config: Path | None) -> None:
    if config:
        get_config(reload=True, path=config)


_EXPORT_LAYOUTS = frozenset({"auto", "mobile", "web"})
_WEB_LAYOUTS = frozenset({"legacy", "screens"})


def _require_export_layout(layout: str) -> None:
    if layout not in _EXPORT_LAYOUTS:
        typer.echo("E_CLI: --layout must be auto, mobile, or web", err=True)
        raise typer.Exit(1)


def _require_web_layout(web_layout: str | None) -> None:
    if web_layout is not None and web_layout not in _WEB_LAYOUTS:
        typer.echo("E_CLI: --web-layout must be legacy or screens", err=True)
        raise typer.Exit(1)


def _trip_svc(trip_json: Path) -> TripService:
    """TripService scoped to the project root for a resolved trip.json."""
    return app_context_for_trip_json(trip_json).trip_service()

def _print_demo_result(
    result,
    *,
    layout: str,
    no_render: bool,
    published: bool = False,
) -> None:
    typer.echo(f"OK demo · trip {result.trip_dir}")
    typer.echo(f"  pipeline: {' → '.join(result.stages)}")
    typer.echo(f"  photos: {result.photo_count}")
    if result.layout_summary:
        typer.echo(f"  layout: {result.layout_summary}")
    s = result.stats
    if s.get("ingest_skipped"):
        typer.echo(f"  ingest skipped: {s['ingest_skipped']}")
    for key, label in (
        ("deduped", "dup(md5)"),
        ("deduped_phash", "dup(phash)"),
        ("deduped_burst", "dup(burst)"),
    ):
        if s.get(key):
            typer.echo(f"    {label}: {s[key]}")
    if s.get("exif_dates") is not None:
        typer.echo(
            f"  dates: exif={s.get('exif_dates', 0)} "
            f"filename={s.get('filename_dates', 0)} "
            f"mtime={s.get('mtime_dates', 0)}"
        )
    for w in s.get("date_warnings") or []:
        typer.echo(f"  WARN: {w}")
    if s.get("mediaClassSummary"):
        parts = [f"{k}={v}" for k, v in sorted(s["mediaClassSummary"].items()) if v]
        typer.echo(f"  media: {', '.join(parts)}")
    typer.echo(f"  trip.json: {result.trip_json}")
    if published and result.zip_path:
        typer.echo(f"  zip: {result.zip_path}")
        typer.echo("")
        typer.echo("Share: send zip to WeChat; unzip → open index.html offline.")
        return
    if not no_render:
        typer.echo(f"  index.html: {result.index_html}")
        typer.echo("")
        typer.echo("Preview:")
        typer.echo(f"  cd {result.trip_dir}")
        typer.echo("  python -m http.server 8766")
        typer.echo("  → http://127.0.0.1:8766/index.html")
    typer.echo("")
    typer.echo("Next (publish share zip):")
    typer.echo('  python -m travelogue demo "<album>" --title "…" --publish --force')
    typer.echo(f"  python -m travelogue run {result.trip_dir.name} --from lock_structure --until exported --confirm-privacy")
    typer.echo("")
    typer.echo("Next (optional gates):")
    typer.echo(f"  python -m travelogue status {result.trip_dir.name} --g1")
    typer.echo(f"  python -m travelogue lock {result.trip_dir.name} structure")
    typer.echo(f"  python -m travelogue narrate {result.trip_dir.name}")
    typer.echo(f"  python -m travelogue export {result.trip_dir.name} --confirm-privacy")


def _run_demo_cmd(
    album_dir: Path,
    *,
    title: str,
    place: str,
    hook: str,
    trip_id: str | None,
    trips_dir: Path,
    max_photos: int,
    layout: str,
    no_render: bool,
    force: bool,
    no_dedupe: bool,
    config: Path | None,
    publish: bool = False,
    confirm_privacy: bool = True,
    no_preview: bool = False,
    featured_dir: Path | None = None,
    material_dir: Path | None = None,
) -> None:
    cfg_path = resolve_demo_config(config)
    if cfg_path:
        _load_cfg(cfg_path)
        typer.echo(f"config: {cfg_path}")
    _require_export_layout(layout)
    try:
        result = run_demo_from_album(
            album_dir,
            trips_dir=trips_dir,
            trip_id=trip_id,
            title=title,
            place=place,
            hook=hook,
            max_photos=max_photos,
            render=not no_render,
            export_layout=layout,
            force=force,
            dedupe=not no_dedupe,
            config=config,
            publish=publish,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            featured_dir=featured_dir,
            material_dir=material_dir,
        )
    except DemoError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _print_demo_result(result, layout=layout, no_render=no_render, published=publish)
def _resolve(path: str, *, trips_dir: Path | None = None) -> Path:
    """Resolve trip id / dir / trip.json.

    When ``trips_dir`` is omitted (``None``), absolute or relative ``trip.json``
    paths resolve by filesystem presence (CLI loose mode). Explicit
    ``--trips-dir`` enables the trips-root sandbox. Studio/HTTP must never use
    this loose path for user input.
    """
    ctx = app_context_for_trips_dir(trips_dir)
    try:
        return ctx.trip_service().resolve_trip_json(path, trips_dir=trips_dir)
    except TripNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def _trips_root(trips_dir: Path) -> Path:
    return trips_dir.resolve()
