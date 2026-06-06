"""Demo subcommands and top-level album shortcuts."""

from __future__ import annotations

from pathlib import Path

import typer
import typer.main

from travelogue.cli._apps import app, demo_app
from travelogue.cli._helpers import _run_demo_cmd
from travelogue.demo.verify import run_demo_verify
from travelogue.paths import GOLDEN_HTML, TEMPLATE_VISUAL_JOURNAL


@demo_app.callback(invoke_without_command=True)
def demo_main(
    ctx: typer.Context,
    album_dir: Path | None = typer.Argument(
        None,
        help="folder with JPG/PNG/WebP/HEIC (omit when using demo verify / demo golden)",
    ),
    title: str = typer.Option("我的旅途", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    hook: str = typer.Option("", "--hook"),
    trip_id: str | None = typer.Option(None, "--trip-id"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    max_photos: int = typer.Option(250, "--max-photos"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_render: bool = typer.Option(False, "--no-render"),
    force: bool = typer.Option(False, "--force", help="replace existing trip folder"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    config: Path | None = typer.Option(None, "--config"),
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
    featured_dir: Path | None = typer.Option(
        None, "--featured-dir", help="精选文件夹（双源 ingest；默认识别 album 下 精选/featured 等）"
    ),
    material_dir: Path | None = typer.Option(
        None, "--material-dir", help="素材文件夹（双源 ingest；默认识别 album 下 素材/material 等）"
    ),
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
        featured_dir=featured_dir,
        material_dir=material_dir,
    )


@app.command("quick")
def cmd_quick(
    album_dir: Path = typer.Argument(..., help="folder with JPG/PNG/WebP/HEIC"),
    title: str = typer.Option("我的旅途", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    max_photos: int = typer.Option(250, "--max-photos"),
    layout: str = typer.Option("auto", "--layout", "-l", help="default auto (web screens)"),
    force: bool = typer.Option(False, "--force", help="replace existing trip folder"),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """One-shot album → ingest → curate → render (shortcut for ``from-album --layout auto``)."""
    _run_demo_cmd(
        album_dir,
        title=title,
        place=place,
        hook="",
        trip_id=None,
        trips_dir=trips_dir,
        max_photos=max_photos,
        layout=layout,
        no_render=False,
        force=force,
        no_dedupe=False,
        config=config,
    )


@app.command("from-album")
def cmd_from_album(
    album_dir: Path = typer.Argument(..., help="folder with JPG/PNG/WebP/HEIC"),
    title: str = typer.Option("我的旅途", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    hook: str = typer.Option("", "--hook"),
    trip_id: str | None = typer.Option(None, "--trip-id"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    max_photos: int = typer.Option(250, "--max-photos"),
    layout: str = typer.Option("mobile", "--layout", "-l"),
    no_render: bool = typer.Option(False, "--no-render"),
    force: bool = typer.Option(False, "--force", help="replace existing trip folder"),
    no_dedupe: bool = typer.Option(False, "--no-dedupe"),
    config: Path | None = typer.Option(None, "--config"),
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
    featured_dir: Path | None = typer.Option(
        None, "--featured-dir", help="精选文件夹（双源 ingest）"
    ),
    material_dir: Path | None = typer.Option(
        None, "--material-dir", help="素材文件夹（双源 ingest）"
    ),
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
        featured_dir=featured_dir,
        material_dir=material_dir,
    )
@demo_app.command("verify")
def cmd_demo_verify(
    album_dir: Path | None = typer.Option(
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
    trip_id: str | None = typer.Option(None, "--trip-id", help="output folder name under trips/"),
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
    config: Path | None = typer.Option(None, "--config"),
    publish: bool = typer.Option(False, "--publish"),
    confirm_privacy: bool = typer.Option(True, "--confirm-privacy/--no-confirm-privacy"),
    no_preview: bool = typer.Option(False, "--no-preview"),
    featured_dir: Path | None = typer.Option(None, "--featured-dir"),
    material_dir: Path | None = typer.Option(None, "--material-dir"),
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
        featured_dir=featured_dir,
        material_dir=material_dir,
    )
