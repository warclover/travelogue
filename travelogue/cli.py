"""Travelogue CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import typer.main

import json

from travelogue.curation.curate import CurateError, run_curate
from travelogue.demo.build import DemoError, resolve_demo_config, run_demo_from_album
from travelogue.demo.verify import run_demo_verify
from travelogue.paths import GOLDEN_HTML, TEMPLATE_VISUAL_JOURNAL
from travelogue.export.packager import ExportError, export_trip
from travelogue.config import get_config
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.media.ingest_report import format_g1_status, format_ingest_report
from travelogue.media.reexport import reexport_trip_assets
from travelogue.orchestrator.pipeline import PublishResult, publish_trip
from travelogue.orchestrator.run import RunResult, run_trip
from travelogue.render.engine import RenderError, render_trip, render_trip_surfaces
from travelogue.render.preview import render_preview_jpg
from travelogue.services.layout import LayoutError, apply_layout_to_trip
from travelogue.llm.errors import LlmError
from travelogue.services.narrate import NarrateError, run_narrate
from travelogue.services.pipeline_state import PipelineError
from travelogue.services.trip import TripNotFoundError, TripService
from travelogue.services.trip_factory import create_trip
from travelogue.services.validate import validate_trip

app = typer.Typer(help="Travelogue — photos to HTML travelogue", no_args_is_help=True)
trip_app = typer.Typer(help="Create and list trip workspaces")
demo_app = typer.Typer(help="Quick demos (real photos → HTML preview)")
app.add_typer(trip_app, name="trip")
app.add_typer(demo_app, name="demo")
llm_app = typer.Typer(help="LLM provider utilities")
media_app = typer.Typer(help="Re-export pixels from source/")
app.add_typer(llm_app, name="llm")
app.add_typer(media_app, name="media")


def _load_cfg(config: Path | None) -> None:
    if config:
        get_config(reload=True, path=config)


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
    trip_id: Optional[str],
    trips_dir: Path,
    max_photos: int,
    layout: str,
    no_render: bool,
    force: bool,
    no_dedupe: bool,
    config: Optional[Path],
    publish: bool = False,
    confirm_privacy: bool = True,
    no_preview: bool = False,
) -> None:
    cfg_path = resolve_demo_config(config)
    if cfg_path:
        _load_cfg(cfg_path)
        typer.echo(f"config: {cfg_path}")
    if layout not in ("auto", "mobile", "web"):
        typer.echo("E_CLI: --layout must be auto, mobile, or web", err=True)
        raise typer.Exit(1)
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
        )
    except DemoError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _print_demo_result(result, layout=layout, no_render=no_render, published=publish)


@demo_app.callback(invoke_without_command=True)
def demo_main(
    ctx: typer.Context,
    album_dir: Optional[Path] = typer.Argument(
        None,
        help="folder with JPG/PNG/WebP/HEIC (omit when using demo verify / demo golden)",
    ),
    title: str = typer.Option("我的旅途", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    hook: str = typer.Option("", "--hook"),
    trip_id: Optional[str] = typer.Option(None, "--trip-id"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    max_photos: int = typer.Option(250, "--max-photos"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_render: bool = typer.Option(False, "--no-render"),
    force: bool = typer.Option(False, "--force", help="replace existing trip folder"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    config: Optional[Path] = typer.Option(None, "--config"),
    publish: bool = typer.Option(
        False,
        "--publish",
        help="after preview pipeline, auto lock → narrate → export share zip",
    ),
    confirm_privacy: bool = typer.Option(
        True,
        "--confirm-privacy/--no-confirm-privacy",
        help="required for --publish (sets privacy.confirmedAt, strips EXIF)",
    ),
    no_preview: bool = typer.Option(False, "--no-preview", help="skip preview.jpg in zip"),
) -> None:
    """Album → ingest → curate → render; with --publish also exports share zip."""
    if ctx.invoked_subcommand is not None:
        return
    if album_dir is not None:
        sub_name = str(album_dir)
        demo_group = typer.main.get_group(demo_app)
        sub_cmd = demo_group.get_command(ctx, sub_name)
        if sub_cmd is not None:
            return ctx.invoke(sub_cmd)
    if album_dir is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(1)
    if publish and not confirm_privacy:
        typer.echo("E_CLI: --publish requires --confirm-privacy", err=True)
        raise typer.Exit(1)
    _run_demo_cmd(
        album_dir,
        title=title,
        place=place,
        hook=hook,
        trip_id=trip_id,
        trips_dir=trips_dir,
        max_photos=max_photos,
        layout=layout,
        no_render=no_render,
        force=force,
        no_dedupe=no_dedupe,
        config=config,
        publish=publish,
        confirm_privacy=confirm_privacy,
        no_preview=no_preview,
    )


@app.command("from-album")
def cmd_from_album(
    album_dir: Path = typer.Argument(..., help="folder with JPG/PNG/WebP/HEIC"),
    title: str = typer.Option("我的旅途", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    hook: str = typer.Option("", "--hook"),
    trip_id: Optional[str] = typer.Option(None, "--trip-id"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    max_photos: int = typer.Option(250, "--max-photos"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_render: bool = typer.Option(False, "--no-render"),
    force: bool = typer.Option(False, "--force", help="replace existing trip folder"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    config: Optional[Path] = typer.Option(None, "--config"),
    publish: bool = typer.Option(
        False,
        "--publish",
        help="after preview pipeline, auto lock → narrate → export share zip",
    ),
    confirm_privacy: bool = typer.Option(
        True,
        "--confirm-privacy/--no-confirm-privacy",
        help="required for --publish (sets privacy.confirmedAt, strips EXIF)",
    ),
    no_preview: bool = typer.Option(False, "--no-preview", help="skip preview.jpg in zip"),
) -> None:
    """Same as ``demo <album>`` — explicit top-level entry (album → HTML or zip)."""
    if publish and not confirm_privacy:
        typer.echo("E_CLI: --publish requires --confirm-privacy", err=True)
        raise typer.Exit(1)
    _run_demo_cmd(
        album_dir,
        title=title,
        place=place,
        hook=hook,
        trip_id=trip_id,
        trips_dir=trips_dir,
        max_photos=max_photos,
        layout=layout,
        no_render=no_render,
        force=force,
        no_dedupe=no_dedupe,
        config=config,
        publish=publish,
        confirm_privacy=confirm_privacy,
        no_preview=no_preview,
    )


def _resolve(path: str, *, trips_dir: Path | None = None) -> Path:
    try:
        svc = TripService()
        if trips_dir:
            svc.root = trips_dir.parent if trips_dir.name == "trips" else trips_dir
        return svc.resolve_trip_json(path, trips_dir=trips_dir)
    except TripNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def _trips_root(trips_dir: Path) -> Path:
    return trips_dir.resolve()


@trip_app.command("new")
def cmd_trip_new(
    trip_id: str = typer.Argument(..., help="trip folder name under trips/"),
    title: str = typer.Option("待命名旅程", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    from_dir: Optional[Path] = typer.Option(None, "--from", help="photo folder; chains ingest"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    layout: str = typer.Option("mobile", "--layout", "-l", help="exportLayout for ingest/curate"),
    force: bool = typer.Option(False, "--force", help="allow non-empty trip dir"),
) -> None:
    """Create trip workspace (draft_ingest) and optionally ingest photos."""
    root = _trips_root(trips_dir)
    trip_dir = root / trip_id
    if trip_dir.exists() and any(trip_dir.iterdir()) and not force:
        typer.echo(f"E_TRIP_EXISTS {trip_dir} (use --force)", err=True)
        raise typer.Exit(1)
    trip_json = create_trip(trip_id, root, title=title, place=place, export_layout=layout)
    typer.echo(f"OK trip {trip_dir}")
    if from_dir:
        trip = TripService(root=root.parent).load(trip_json)
        try:
            result = ingest_into_trip(trip, trip_dir, from_dir=from_dir, generate_crops=False)
        except IngestError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        TripService(root=root.parent).save(trip, trip_json)
        typer.echo(f"OK ingest +{result.added} assets · batch {result.batch_id}")
        if layout != "auto":
            try:
                cur = run_curate(trip, export_layout=layout, trip_dir=trip_json.parent)
            except CurateError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(1) from exc
            TripService(root=root.parent).save(trip, trip_json)
            typer.echo(f"OK curate {cur.chapter_count} chapters · {cur.layout_summary}")


@trip_app.command("list")
def cmd_trip_list(
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
) -> None:
    """List trips under trips_dir."""
    root = _trips_root(trips_dir)
    if not root.is_dir():
        typer.echo("(no trips directory)")
        return
    rows: list[tuple[str, str, str, str]] = []
    for d in sorted(root.iterdir()):
        tj = d / "trip.json"
        if not tj.is_file():
            continue
        try:
            trip = json.loads(tj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        meta = trip.get("meta", {})
        pipe = trip.get("pipeline", {})
        rows.append(
            (
                trip.get("tripId", d.name),
                pipe.get("status", "?"),
                pipe.get("layoutStatus", "-") or "-",
                meta.get("title", "")[:20],
            )
        )
    if not rows:
        typer.echo("(no trips)")
        return
    for tid, status, layout_st, title in rows:
        typer.echo(f"{tid}\t{status}\t{layout_st}\t{title}")


@app.command("ingest")
def cmd_ingest(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    from_dir: Optional[Path] = typer.Option(None, "--from", help="import from folder"),
    batch_id: Optional[str] = typer.Option(None, "--batch-id"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    no_crop: bool = typer.Option(False, "--no-crop", help="skip -m/-w profile crops"),
    incremental: bool = typer.Option(False, "--incremental"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    config: Optional[Path] = typer.Option(None, "--config", help="config.yaml path"),
) -> None:
    """Agent 0: import photos into trip (ingest_ready)."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip_root = trip_path.parent
    trip = TripService().load(trip_path)
    try:
        result = ingest_into_trip(
            trip,
            trip_root,
            from_dir=from_dir,
            batch_id=batch_id,
            generate_crops=not no_crop,
            dedupe=not no_dedupe,
            incremental=incremental,
        )
    except IngestError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    TripService().save(trip, trip_path)
    typer.echo("OK ingest")
    typer.echo(format_ingest_report(result, trip))


@media_app.command("reexport")
def cmd_media_reexport(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    asset_id: Optional[list[str]] = typer.Option(None, "--asset", "-a", help="only these asset ids"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    """Re-export WebP from source/ (after layout or focalPoint change)."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip_root = trip_path.parent
    trip = TripService().load(trip_path)
    result = reexport_trip_assets(trip, trip_root, asset_ids=asset_id)
    TripService().save(trip, trip_path)
    typer.echo("OK reexport")
    typer.echo(format_ingest_report(result, trip))
    if result.failed:
        raise typer.Exit(1)


@app.command("curate")
def cmd_curate(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_layout: bool = typer.Option(False, "--no-layout", help="structure only, layoutStatus=pending"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
) -> None:
    """Agent 1+1.5: day chapters, cover, row layout (structure_draft)."""
    if layout not in ("auto", "mobile", "web"):
        typer.echo("E_CLI: --layout must be auto, mobile, or web", err=True)
        raise typer.Exit(1)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = TripService().load(trip_path)
    try:
        result = run_curate(
            trip,
            export_layout=layout,
            apply_layout=not no_layout,
            trip_dir=trip_path.parent,
        )
    except CurateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    TripService().save(trip, trip_path)
    typer.echo(f"OK curate · cover {result.cover_asset_id}")
    typer.echo(f"  {result.chapter_count} chapters · {result.day_groups} day groups")
    typer.echo(f"  {result.layout_summary}")
    for w in result.warnings:
        typer.echo(f"  WARN {w}")


@app.command("lock")
def cmd_lock(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    target: str = typer.Argument(..., help="structure | copy"),
    cover: Optional[str] = typer.Option(None, "--cover", help="cover asset id (structure lock)"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
) -> None:
    """Lock structure or copy gate."""
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = TripService().load(trip_path)
    pipe = trip.setdefault("pipeline", {})
    locks = pipe.setdefault("locks", {"structure": False, "copy": False})
    assets = {a["id"] for a in trip.get("assets", [])}
    if target == "structure":
        if cover:
            if cover not in assets:
                typer.echo(f"E_LOCK cover not in assets: {cover}", err=True)
                raise typer.Exit(1)
            trip["coverAssetId"] = cover
        locks["structure"] = True
        pipe["status"] = "structure_locked"
        typer.echo("OK structure_locked")
    elif target == "copy":
        locks["copy"] = True
        pipe["status"] = "copy_locked"
        typer.echo("OK copy_locked")
    else:
        typer.echo("E_CLI: lock target must be structure or copy", err=True)
        raise typer.Exit(1)
    TripService().save(trip, trip_path)


@app.command("narrate")
def cmd_narrate(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    tone: Optional[str] = typer.Option(None, "--tone"),
    provider: Optional[str] = typer.Option(
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
    chapter_id: Optional[str] = typer.Option(
        None,
        "--chapter-id",
        help="Only narrate this chapter (skips meta/epilogue); use with --regenerate",
    ),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    """Agent 2: hook, leads, captions via LLM or rule stub."""
    _load_cfg(config)
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = TripService().load(trip_path)
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
        )
    except NarrateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if dry_run:
        typer.echo(f"dry-run would update: {', '.join(result.fields_updated) or '(none)'}")
        return
    TripService().save(trip, trip_path)
    prov = provider or get_config().llm.provider or "stub"
    typer.echo(f"OK narrate ({prov}) · updated {', '.join(result.fields_updated) or '(none)'}")
    if result.fields_updated:
        scope = f" (chapter {chapter_id})" if chapter_id else ""
        typer.echo(f"  next: python -m travelogue render {path}{scope}")


@llm_app.command("ping")
def cmd_llm_ping(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="deepseek | dashscope (default: config llm.provider)",
    ),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    """Verify LLM API key and connectivity."""
    from travelogue.llm.client import llm_ping
    from travelogue.llm.errors import LlmError

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
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    g1: bool = typer.Option(False, "--g1", help="include structure/layout summary"),
) -> None:
    """Print pipeline status, locks, asset/chapter counts."""
    trip_path = _resolve(path, trips_dir=trips_dir)
    trip = TripService().load(trip_path)
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
    from_dir: Optional[Path] = typer.Option(None, "--from-dir", help="album for ingest stage"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    confirm_privacy: bool = typer.Option(False, "--confirm-privacy"),
    no_preview: bool = typer.Option(False, "--no-preview"),
    skip_locked: bool = typer.Option(True, "--skip-locked/--no-skip-locked"),
    narrate_provider: Optional[str] = typer.Option(
        None,
        "--narrate-provider",
        help="stub | deepseek | dashscope for narrate stage",
    ),
    regenerate: bool = typer.Option(False, "--regenerate", help="Force rewrite copy on narrate stage"),
) -> None:
    """Run pipeline stages in order up to --until."""
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
    web_layout: Optional[str] = typer.Option(
        None,
        "--web-layout",
        help="layoutEngine: legacy | screens (requires exportLayout web for screens DOM)",
    ),
    render: bool = typer.Option(False, "--render", help="re-render draft index.html after layout"),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation after save"),
) -> None:
    """Re-run Agent 1.5 layout on existing trip.json (chapters/items only)."""
    if layout not in ("auto", "mobile", "web"):
        typer.echo("E_CLI: --layout must be auto, mobile, or web", err=True)
        raise typer.Exit(1)
    if web_layout is not None and web_layout not in ("legacy", "screens"):
        typer.echo("E_CLI: --web-layout must be legacy or screens", err=True)
        raise typer.Exit(1)
    trip_path = _resolve(path)
    svc = TripService()
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
    svc.save(trip, trip_path)
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
    trip = TripService().load(trip_path)
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


@app.command("render")
def cmd_render(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="output directory"),
    mode: str = typer.Option("draft", "--mode", "-m", help="draft | share"),
    web_layout: Optional[str] = typer.Option(
        None,
        "--web-layout",
        help="layout engine override: legacy | screens (also sets index filename for screens)",
    ),
    index_name: Optional[str] = typer.Option(
        None,
        "--index-name",
        help="output HTML filename (default index.html)",
    ),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation"),
    mark_rendered: bool = typer.Option(False, "--mark-rendered", help="set pipeline.status=rendered"),
    dual: bool = typer.Option(
        False,
        "--dual",
        help="write index.html (web+screens) and index-mobile.html (mobile+legacy)",
    ),
    font_theme: Optional[str] = typer.Option(
        None,
        "--font-theme",
        help="ui (default YaHei stack) | magazine (system KaiTi backup theme)",
    ),
    copy_display: Optional[str] = typer.Option(
        None,
        "--copy-display",
        help="full | photos — hide hook/lead/captions at render (trip.json unchanged unless set in export.copyDisplay)",
    ),
) -> None:
    """Render index.html + journal.css from trip.json."""
    if mode not in ("draft", "share"):
        typer.echo("E_CLI: --mode must be draft or share", err=True)
        raise typer.Exit(1)
    if web_layout is not None and web_layout not in ("legacy", "screens"):
        typer.echo("E_CLI: --web-layout must be legacy or screens", err=True)
        raise typer.Exit(1)
    if font_theme is not None and font_theme not in ("ui", "magazine"):
        typer.echo("E_CLI: --font-theme must be ui or magazine", err=True)
        raise typer.Exit(1)
    if copy_display is not None and copy_display not in ("full", "photos"):
        typer.echo("E_CLI: --copy-display must be full or photos", err=True)
        raise typer.Exit(1)
    theme_arg = None if font_theme in (None, "ui") else font_theme
    out_html = index_name
    if out_html is None:
        out_html = "index.html"
    trip_path = _resolve(path)
    try:
        if dual:
            web_path, mobile_path = render_trip_surfaces(
                trip_path,
                out,
                export_mode=mode,
                validate=not no_validate,
                update_pipeline=mark_rendered,
                font_theme=theme_arg,
                copy_display_override=copy_display,
            )
            typer.echo(f"OK {web_path}")
            typer.echo(f"OK {mobile_path}")
            return
        out_dir = render_trip(
            trip_path,
            out,
            export_mode=mode,
            validate=not no_validate,
            update_pipeline=mark_rendered,
            layout_engine=web_layout,
            index_name=out_html,
            font_theme=theme_arg,
            copy_display_override=copy_display,
        )
    except RenderError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {out_dir / out_html}")
    trip = TripService().load(trip_path)
    from travelogue.render.engine import should_include_long_shot, should_include_screenplay

    if should_include_screenplay(trip, layout_engine_override=web_layout):
        typer.echo("  自动播放: 封面或右下角「自动播放」· 建议用本地 http 打开（全屏需用户手势）")
        typer.echo("  文案切换: 右下角「隐藏文案/显示文案」（偏好保存在浏览器 sessionStorage）")
        if not should_include_long_shot(trip, layout_engine_override=web_layout):
            typer.echo("  保存长图: 右下角「保存长图」→ index-longshot.html 自动生成")
            typer.echo("  预览: python -m travelogue serve <trip>  （长图需 http，不可用 file://）")
    from travelogue.render.copy_display import is_photos_only, resolve_copy_display

    if is_photos_only(resolve_copy_display(trip, override=copy_display)):
        typer.echo("  纯照片模式: 已隐藏 hook/导语/图注（trip.json 文案保留，改 export.copyDisplay=full 可恢复）")
    if mode == "draft":
        typer.echo("  文案编辑: python -m travelogue serve <trip> 打开后点击文案保存到 trip.json")


@app.command("serve")
def cmd_serve(
    path: str = typer.Argument(..., help="trip directory, trip.json, or tripId"),
    port: int = typer.Option(8766, "--port", "-p", help="HTTP port"),
    host: str = typer.Option("127.0.0.1", "--host", help="bind address"),
    index: str = typer.Option("index.html", "--index", help="entry HTML filename"),
    rerender: bool = typer.Option(
        True,
        "--rerender/--no-rerender",
        help="re-render HTML after inline save (F-ED-03)",
    ),
) -> None:
    """Serve trip output with inline copy save API (draft editing)."""
    from travelogue.web.serve import resolve_trip_serve_dir, serve_trip_directory

    try:
        trip_path = _resolve(path)
        serve_dir = resolve_trip_serve_dir(trip_path)
    except (TripNotFoundError, FileNotFoundError) as exc:
        typer.echo(f"E_SERVE: {exc}", err=True)
        raise typer.Exit(1) from exc
    if not (serve_dir / index).is_file():
        typer.echo(f"E_SERVE: {index} not found in {serve_dir} — run render first", err=True)
        raise typer.Exit(1)
    try:
        serve_trip_directory(serve_dir, port=port, host=host, index=index, auto_rerender=rerender)
    except KeyboardInterrupt:
        raise typer.Exit(0) from None


@app.command("migrate-captions")
def cmd_migrate_captions(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    dry_run: bool = typer.Option(False, "--dry-run", help="report only, do not save"),
) -> None:
    """Copy media-card item captions onto assets[].caption when missing."""
    from travelogue.curation.asset_caption import migrate_captions_to_assets

    trip_path = _resolve(path)
    svc = TripService()
    trip = svc.load(trip_path)
    migrated = migrate_captions_to_assets(trip)
    if not migrated:
        typer.echo("OK migrate-captions · nothing to migrate")
        return
    if dry_run:
        typer.echo(f"OK migrate-captions · would migrate {len(migrated)} assets: {', '.join(migrated[:8])}")
        return
    svc.save(trip, trip_path)
    typer.echo(f"OK migrate-captions · migrated {len(migrated)} assets")


@app.command("longshot-smoke")
def cmd_longshot_smoke(
    path: str = typer.Argument(..., help="trip directory, trip.json, or tripId"),
    port: int = typer.Option(0, "--port", "-p", help="HTTP port (0 = random)"),
    no_capture: bool = typer.Option(False, "--no-capture", help="DOM/API checks only"),
) -> None:
    """Playwright smoke test for index-longshot.html (requires playwright + chromium)."""
    from travelogue.render.engine import LONGSHOT_INDEX_NAME
    from travelogue.web.longshot_smoke import LongshotSmokeError, run_longshot_smoke
    from travelogue.web.serve import resolve_trip_serve_dir

    try:
        trip_path = _resolve(path)
        serve_dir = resolve_trip_serve_dir(trip_path)
    except (TripNotFoundError, FileNotFoundError) as exc:
        typer.echo(f"E_LONGSHOT_SMOKE: {exc}", err=True)
        raise typer.Exit(1) from exc
    sidecar = serve_dir / LONGSHOT_INDEX_NAME
    if not sidecar.is_file():
        typer.echo(f"E_LONGSHOT_SMOKE: {LONGSHOT_INDEX_NAME} not found — run render first", err=True)
        raise typer.Exit(1)
    try:
        result = run_longshot_smoke(
            serve_dir,
            port=port,
            capture_first_chapter=not no_capture,
        )
    except LongshotSmokeError as exc:
        typer.echo(f"E_LONGSHOT_SMOKE: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"OK longshot-smoke · chapters={result['chapter_count']} cards={result['media_card_count']} "
        f"url={result['url']}"
    )
    if result.get("first_chapter_blob_bytes"):
        typer.echo(f"  capture: {result['first_chapter_blob_bytes']} bytes (chapter 1 @ 1×)")
    elif result.get("capture_skipped"):
        typer.echo(f"  capture skipped: {result['capture_skipped']}")


@app.command("preview")
def cmd_preview(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="preview.jpg path"),
) -> None:
    """Generate preview.jpg (1080×1920) with Pillow."""
    trip_path = _resolve(path)
    try:
        out_path = render_preview_jpg(trip_path, out)
    except Exception as exc:
        typer.echo(f"E_PREVIEW: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {out_path}")


@app.command("export")
def cmd_export(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="zip output path"),
    confirm_privacy: bool = typer.Option(
        False,
        "--confirm-privacy",
        help="required: confirm privacy and package for sharing",
    ),
    no_preview: bool = typer.Option(False, "--no-preview", help="skip preview.jpg generation"),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation"),
    no_longshot: bool = typer.Option(
        False,
        "--no-longshot",
        help="omit 保存长图 bundle from export (trip.export.longShot=false)",
    ),
) -> None:
    """Package index.html + assets into trip-{id}.zip (share mode)."""
    trip_path = _resolve(path)
    try:
        zip_path = export_trip(
            trip_path,
            output_zip=output,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            validate=not no_validate,
            no_longshot=no_longshot,
        )
    except (ExportError, RenderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {zip_path}")


@app.command("publish")
def cmd_publish(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="zip output path"),
    confirm_privacy: bool = typer.Option(
        True,
        "--confirm-privacy/--no-confirm-privacy",
        help="confirm privacy before export (default on)",
    ),
    no_preview: bool = typer.Option(False, "--no-preview", help="skip preview.jpg"),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation"),
) -> None:
    """Validate → render (share) → preview → export zip."""
    trip_path = _resolve(path)
    try:
        result: PublishResult = publish_trip(
            trip_path,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            output_zip=output,
            validate=not no_validate,
        )
    except (ExportError, RenderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK index {result.index_html}")
    if result.preview_jpg:
        typer.echo(f"OK preview {result.preview_jpg}")
    typer.echo(f"OK zip {result.zip_path}")


@demo_app.command("verify")
def cmd_demo_verify(
    album_dir: Optional[Path] = typer.Option(
        None,
        "--album",
        help="optional: run ingest→render smoke on a photo folder",
    ),
    full: bool = typer.Option(False, "--full", help="run entire tests/ suite"),
    skip_pytest: bool = typer.Option(False, "--skip-pytest", help="only fixtures + dom gates"),
    skip_dom: bool = typer.Option(False, "--skip-dom", help="skip fixture vs golden.html DOM check"),
    sync_reference: bool = typer.Option(
        False,
        "--sync-reference",
        help="write trips/_golden-reference/render-golden-demo/",
    ),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir", help="trips root for reference sync"),
) -> None:
    """Validate fixtures, golden DOM, pytest (quick or full), optional album smoke."""
    result = run_demo_verify(
        album_dir=album_dir,
        full_tests=full,
        skip_pytest=skip_pytest,
        skip_dom=skip_dom,
        sync_reference=sync_reference,
        trips_dir=trips_dir,
    )
    for line in result.messages:
        typer.echo(line)
    if result.ok:
        typer.echo("OK demo verify")
    else:
        raise typer.Exit(1)


@demo_app.command("golden")
def cmd_demo_golden(
    port: int = typer.Option(8765, "--port", "-p", help="http.server port for template golden.html"),
    sync_reference: bool = typer.Option(
        False,
        "--sync-reference",
        help="materialize trips/_golden-reference/render-golden-demo/",
    ),
    reference_port: int = typer.Option(
        8767,
        "--reference-port",
        help="http.server port for reference trip index.html",
    ),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir", help="trips root"),
    force: bool = typer.Option(False, "--force", help="replace existing reference trip dir"),
) -> None:
    """Preview golden.html and/or the render_golden reference trip."""
    from travelogue.demo.golden_reference import golden_reference_dir, materialize_golden_reference

    if not GOLDEN_HTML.is_file():
        typer.echo(f"E_GOLDEN: missing {GOLDEN_HTML}", err=True)
        raise typer.Exit(1)

    root = TEMPLATE_VISUAL_JOURNAL.resolve()
    typer.echo("OK golden template")
    typer.echo(f"  golden.html: {GOLDEN_HTML}")
    typer.echo("")
    typer.echo("Template preview (generate assets once if missing):")
    typer.echo("  python scripts/gen_demo_assets.py")
    typer.echo("  python scripts/gen_golden_variants.py")
    typer.echo(f"  cd {root}")
    typer.echo(f"  python -m http.server {port}")
    typer.echo(f"  → http://127.0.0.1:{port}/golden.html")

    ref_dir = golden_reference_dir(trips_dir)
    if sync_reference or force or not (ref_dir / "index.html").is_file():
        try:
            ref = materialize_golden_reference(trips_dir, force=force or sync_reference)
        except FileNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        typer.echo("")
        typer.echo(ref.message)
        ref_dir = ref.trip_dir

    if ref_dir.is_dir() and (ref_dir / "index.html").is_file():
        typer.echo("")
        typer.echo("Reference trip (fixture → render, same pipeline as demo):")
        typer.echo(f"  dir: {ref_dir.resolve()}")
        typer.echo(f"  cd {ref_dir.resolve()}")
        typer.echo(f"  python -m http.server {reference_port}")
        typer.echo(f"  → http://127.0.0.1:{reference_port}/index.html")
    else:
        typer.echo("")
        typer.echo("Reference trip not built. Run:")
        typer.echo("  travelogue demo golden --sync-reference")


@demo_app.command("from-album", hidden=True)
def cmd_demo_from_album_hidden(
    album_dir: Path = typer.Argument(..., help="folder with JPG/PNG/WebP/HEIC"),
    title: str = typer.Option("我的旅途", "--title", "-t", help="trip title / cover"),
    place: str = typer.Option("旅途", "--place", "-p", help="place label in meta"),
    hook: str = typer.Option("", "--hook", help="optional hook line"),
    trip_id: Optional[str] = typer.Option(None, "--trip-id", help="output folder name under trips/"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir", help="trips root directory"),
    max_photos: int = typer.Option(250, "--max-photos", help="max images to import"),
    layout: str = typer.Option(
        "mobile",
        "--layout",
        "-l",
        help="exportLayout: mobile | web | auto",
    ),
    no_render: bool = typer.Option(False, "--no-render", help="only build trip.json + assets"),
    force: bool = typer.Option(False, "--force"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    config: Optional[Path] = typer.Option(None, "--config"),
    publish: bool = typer.Option(False, "--publish"),
    confirm_privacy: bool = typer.Option(True, "--confirm-privacy/--no-confirm-privacy"),
    no_preview: bool = typer.Option(False, "--no-preview"),
) -> None:
    """Alias for ``travelogue demo`` (same pipeline)."""
    _run_demo_cmd(
        album_dir,
        title=title,
        place=place,
        hook=hook,
        trip_id=trip_id,
        trips_dir=trips_dir,
        max_photos=max_photos,
        layout=layout,
        no_render=no_render,
        force=force,
        no_dedupe=no_dedupe,
        config=config,
        publish=publish,
        confirm_privacy=confirm_privacy,
        no_preview=no_preview,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
