"""Pipeline stage commands (ingest through validate)."""

from __future__ import annotations

from pathlib import Path

import typer

from travelogue.cli._apps import app, llm_app, media_app
from travelogue.cli._helpers import (
    _load_cfg,
    _require_export_layout,
    _require_web_layout,
    _resolve,
    _trip_svc,
)
from travelogue.config import get_config
from travelogue.curation.curate import CurateError, run_curate
from travelogue.export.packager import ExportError
from travelogue.llm.errors import LlmError
from travelogue.media.ingest import RAW_UNSUPPORTED_MESSAGE, IngestError, ingest_into_trip
from travelogue.media.ingest_report import format_g1_status, format_ingest_report
from travelogue.media.reexport import reexport_trip_assets
from travelogue.orchestrator.run import RunResult, run_trip
from travelogue.render.engine import RenderError, render_trip
from travelogue.services.layout import LayoutError, apply_layout_to_trip
from travelogue.services.narrate import NarrateError, run_narrate
from travelogue.services.pipeline_state import PipelineError, lock_copy, lock_structure
from travelogue.services.trip import persist_trip_snapshot
from travelogue.services.validate import validate_trip


@app.command("ingest")
def cmd_ingest(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    from_dir: Path | None = typer.Option(None, "--from", help="import from folder"),
    batch_id: str | None = typer.Option(None, "--batch-id"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    no_crop: bool = typer.Option(False, "--no-crop", help="skip -m/-w profile crops"),
    incremental: bool = typer.Option(False, "--incremental"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
    featured_dir: Path | None = typer.Option(None, "--featured-dir", help="精选文件夹（双源 ingest）"),
    material_dir: Path | None = typer.Option(None, "--material-dir", help="素材文件夹（双源 ingest）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="show RAW rejection details"),
) -> None:
    """Agent 0: import photos into trip (ingest_ready)."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip_root = trip_path.parent
    trip = _trip_svc(trip_path).load(trip_path)
    try:
        result = ingest_into_trip(
            trip,
            trip_root,
            from_dir=from_dir,
            batch_id=batch_id,
            generate_crops=not no_crop,
            dedupe=not no_dedupe,
            incremental=incremental,
            app_cfg=get_config(),
            featured_dir=featured_dir,
            material_dir=material_dir,
        )
    except IngestError as exc:
        if exc.code == "E_INGEST_RAW_UNSUPPORTED":
            typer.echo(f"{exc.code}: {RAW_UNSUPPORTED_MESSAGE}", err=True)
            if verbose:
                typer.echo(str(exc), err=True)
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    persist_trip_snapshot(_trip_svc(trip_path), trip_path, trip)
    typer.echo("OK ingest")
    typer.echo(format_ingest_report(result, trip))


@media_app.command("reexport")
def cmd_media_reexport(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    asset_id: list[str] | None = typer.Option(None, "--asset", "-a", help="only these asset ids"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Re-export WebP from source/ (after layout or focalPoint change)."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip_root = trip_path.parent
    trip = _trip_svc(trip_path).load(trip_path)
    result = reexport_trip_assets(trip, trip_root, asset_ids=asset_id, app_cfg=get_config())
    persist_trip_snapshot(_trip_svc(trip_path), trip_path, trip)
    typer.echo("OK reexport")
    typer.echo(format_ingest_report(result, trip))
    if result.failed:
        raise typer.Exit(1)


@app.command("curate")
def cmd_curate(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_layout: bool = typer.Option(False, "--no-layout", help="structure only, layoutStatus=pending"),
    refresh_algorithms: bool = typer.Option(
        False,
        "--refresh-algorithms",
        help="force re-cull and refresh algorithm profile before curate",
    ),
    no_refresh_algorithms: bool = typer.Option(
        False,
        "--no-refresh-algorithms",
        help="skip auto re-cull even when cull config is stale",
    ),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
) -> None:
    """Agent 1+1.5: day chapters, cover, row layout (structure_draft)."""
    _require_export_layout(layout)
    if refresh_algorithms and no_refresh_algorithms:
        typer.echo("E_CLI: use only one of --refresh-algorithms / --no-refresh-algorithms", err=True)
        raise typer.Exit(1)
    refresh_flag: bool | None = True if refresh_algorithms else False if no_refresh_algorithms else None
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = _trip_svc(trip_path).load(trip_path)
    try:
        result = run_curate(
            trip,
            export_layout=layout,
            apply_layout=not no_layout,
            trip_dir=trip_path.parent,
            refresh_algorithms=refresh_flag,
        )
    except CurateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    persist_trip_snapshot(_trip_svc(trip_path), trip_path, trip)
    from travelogue.curation.curate_report import format_curate_report

    typer.echo(format_curate_report(result, trip))


@app.command("lock")
def cmd_lock(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    target: str = typer.Argument(..., help="structure | copy"),
    cover: str | None = typer.Option(None, "--cover", help="cover asset id (structure lock)"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
) -> None:
    """Lock structure or copy gate."""
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = _trip_svc(trip_path).load(trip_path)
    assets = {a["id"] for a in trip.get("assets", [])}
    if target == "structure":
        if cover:
            if cover not in assets:
                typer.echo(f"E_LOCK cover not in assets: {cover}", err=True)
                raise typer.Exit(1)
            trip["coverAssetId"] = cover
        lock_structure(trip)
        typer.echo("OK structure_locked")
    elif target == "copy":
        lock_copy(trip)
        typer.echo("OK copy_locked")
    else:
        typer.echo("E_CLI: lock target must be structure or copy", err=True)
        raise typer.Exit(1)
    persist_trip_snapshot(_trip_svc(trip_path), trip_path, trip)


@app.command("narrate")
def cmd_narrate(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    tone: str | None = typer.Option(None, "--tone"),
    provider: str | None = typer.Option(
        None,
        "--provider",
        help="stub | deepseek | dashscope (default: config llm.provider or stub)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    regenerate: bool = typer.Option(
        False,
        "--regenerate",
        help="Rewrite non-edited hook, leads, captions, epilogue",
    ),
    chapter_id: str | None = typer.Option(
        None,
        "--chapter-id",
        help="Only narrate this chapter (skips meta/epilogue); use with --regenerate",
    ),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Agent 2: hook, leads, captions via LLM or rule stub."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = _trip_svc(trip_path).load(trip_path)
    try:
        from travelogue.services.pipeline_state import assert_stage_allowed

        if not dry_run:
            assert_stage_allowed(trip, "narrate")
    except PipelineError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    try:
        cache_dir = trip_path.parent / ".cache" / "narrate"
        result = run_narrate(
            trip,
            tone=tone,
            dry_run=dry_run,
            provider=provider,
            regenerate=regenerate,
            cache_dir=cache_dir,
            chapter_id=chapter_id,
            cfg=get_config(),
        )
    except NarrateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if dry_run:
        typer.echo(f"dry-run would update: {', '.join(result.fields_updated) or '(none)'}")
        return
    persist_trip_snapshot(_trip_svc(trip_path), trip_path, trip)
    prov = provider or get_config().llm.provider or "stub"
    typer.echo(f"OK narrate ({prov}) · updated {', '.join(result.fields_updated) or '(none)'}")
    if result.fields_updated:
        scope = f" (chapter {chapter_id})" if chapter_id else ""
        typer.echo(f"  next: python -m travelogue render {path}{scope}")


@llm_app.command("ping")
def cmd_llm_ping(
    provider: str | None = typer.Option(
        None,
        "--provider",
        help="deepseek | dashscope (default: config llm.provider)",
    ),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Verify LLM API key and connectivity."""
    from travelogue.llm.client import llm_ping

    _load_cfg(config)
    try:
        msg = llm_ping(provider=provider)
    except LlmError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK llm ping · {msg}")


@app.command("status")
def cmd_status(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
    g1: bool = typer.Option(False, "--g1", help="include structure/layout summary"),
) -> None:
    """Print pipeline status, locks, asset/chapter counts."""
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = _trip_svc(trip_path).load(trip_path)
    pipe = trip.get("pipeline", {})
    runs = pipe.get("runs") or []
    last = runs[-1] if runs else {}
    typer.echo(f"tripId: {trip.get('tripId')}")
    typer.echo(f"status: {pipe.get('status')}")
    typer.echo(f"layoutStatus: {pipe.get('layoutStatus', '-')}")
    typer.echo(f"locks: {pipe.get('locks')}")
    typer.echo(f"assets: {len(trip.get('assets', []))}")
    typer.echo(f"chapters: {len(trip.get('chapters', []))}")
    if last:
        typer.echo(f"last run: {last.get('agent')} {last.get('runId')}")
    if g1 and trip.get("chapters"):
        typer.echo("")
        typer.echo(format_g1_status(trip))


@app.command("run")
def cmd_run(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    from_stage: str = typer.Option("ingest", "--from", help="ingest|curate|layout|narrate|render|export"),
    until: str = typer.Option("rendered", "--until", help="ingest|structure|layout|copy|rendered|exported"),
    from_dir: Path | None = typer.Option(None, "--from-dir", help="album for ingest stage"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir"),
    confirm_privacy: bool = typer.Option(False, "--confirm-privacy"),
    no_preview: bool = typer.Option(False, "--no-preview"),
    skip_locked: bool = typer.Option(True, "--skip-locked/--no-skip-locked"),
    narrate_provider: str | None = typer.Option(
        None,
        "--narrate-provider",
        help="stub | deepseek | dashscope for narrate stage",
    ),
    regenerate: bool = typer.Option(False, "--regenerate", help="Force rewrite copy on narrate stage"),
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
) -> None:
    """Run pipeline stages in order up to --until."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    try:
        result: RunResult = run_trip(
            trip_path,
            from_stage=from_stage,
            until=until,  # type: ignore[arg-type]
            album_dir=from_dir,
            export_layout=layout,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            skip_locked=skip_locked,
            narrate_provider=narrate_provider,
            regenerate=regenerate,
            cfg=get_config(),
        )
    except (
        IngestError,
        CurateError,
        LayoutError,
        PipelineError,
        RenderError,
        ExportError,
        NarrateError,
        LlmError,
    ) as exc:
        typer.echo(str(exc), err=True)
        if isinstance(exc, LlmError) and exc.code == "E_LLM_AUTH":
            typer.echo(
                "  hint: add DEEPSEEK_API_KEY to project .env (see .env.example) or set the env var",
                err=True,
            )
        raise typer.Exit(1) from exc
    typer.echo(f"OK run · stages: {', '.join(result.stages)}")
    if result.publish:
        typer.echo(f"  zip {result.publish.zip_path}")


@app.command("layout")
def cmd_layout(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    layout: str = typer.Option(
        "mobile",
        "--layout",
        "-l",
        help="exportLayout: mobile | web | auto",
    ),
    web_layout: str | None = typer.Option(
        None,
        "--web-layout",
        help="layoutEngine: legacy | screens (requires exportLayout web for screens DOM)",
    ),
    render: bool = typer.Option(False, "--render", help="re-render draft index.html after layout"),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation after save"),
) -> None:
    """Re-run Agent 1.5 layout on existing trip.json (chapters/items only)."""
    _require_export_layout(layout)
    _require_web_layout(web_layout)
    trip_path = _resolve(path)
    svc = _trip_svc(trip_path)
    trip = svc.load(trip_path)
    try:
        result = apply_layout_to_trip(
            trip,
            export_layout=layout,
            layout_engine=web_layout,
        )
    except LayoutError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    persist_trip_snapshot(svc, trip_path, trip)
    typer.echo(f"OK layout · {result.summary_text}")
    typer.echo(f"  chapters: {result.chapter_count} · items blocks: {result.item_count}")
    if not no_validate:
        errs = [e for e in validate_trip(trip, level="all") if not e.startswith("WARN:")]
        if errs:
            for e in errs:
                typer.echo(e, err=True)
            raise typer.Exit(1)
    if render:
        try:
            out_dir = render_trip(trip_path, trip_path.parent, export_mode="draft", validate=not no_validate)
        except RenderError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        typer.echo(f"OK render {out_dir / 'index.html'}")


@app.command("validate")
def cmd_validate(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    level: str = typer.Option("all", "--level", "-l", help="schema | manifest | all"),
) -> None:
    """Validate trip.json (L1 schema + L2 manifest)."""
    trip_path = _resolve(path)
    trip = _trip_svc(trip_path).load(trip_path)
    errors = validate_trip(trip, level=level)
    warns = [e for e in errors if e.startswith("WARN:")]
    errs = [e for e in errors if not e.startswith("WARN:")]
    for w in warns:
        typer.echo(w)
    for e in errs:
        typer.echo(e, err=True)
    if errs:
        raise typer.Exit(1)
    typer.echo("OK")
