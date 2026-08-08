"""Render, serve, studio, and export commands."""

from __future__ import annotations

from pathlib import Path

import typer

from travelogue.cli._apps import app
from travelogue.cli._helpers import (
    _load_cfg,
    _require_web_layout,
    _resolve,
    _trip_svc,
)
from travelogue.config import get_config
from travelogue.export.packager import ExportError, export_trip
from travelogue.orchestrator.pipeline import PublishResult, publish_trip
from travelogue.render.engine import RenderError, render_trip, render_trip_surfaces
from travelogue.render.preview import render_preview_jpg
from travelogue.services.trip import TripNotFoundError, persist_trip_snapshot


@app.command("render")
def cmd_render(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    out: Path | None = typer.Option(None, "--out", "-o", help="output directory"),
    mode: str = typer.Option("draft", "--mode", "-m", help="draft | share"),
    web_layout: str | None = typer.Option(
        None,
        "--web-layout",
        help="layout engine override: legacy | screens (also sets index filename for screens)",
    ),
    index_name: str | None = typer.Option(
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
    font_theme: str | None = typer.Option(
        None,
        "--font-theme",
        help="ui (default YaHei stack) | magazine (system KaiTi backup theme)",
    ),
    copy_display: str | None = typer.Option(
        None,
        "--copy-display",
        help="full | photos — hide hook/lead/captions at render (trip.json unchanged unless set in export.copyDisplay)",
    ),
    reading_profile: str | None = typer.Option(
        None,
        "--reading-profile",
        help="legacy | performance | default_hybrid | magazine — override export.reading.profile",
    ),
) -> None:
    """Render index.html + journal.css from trip.json."""
    if mode not in ("draft", "share"):
        typer.echo("E_CLI: --mode must be draft or share", err=True)
        raise typer.Exit(1)
    _require_web_layout(web_layout)
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
    if reading_profile and reading_profile not in (
        "legacy",
        "performance",
        "default_hybrid",
        "magazine",
    ):
        typer.echo(
            "E_CLI: --reading-profile must be legacy, performance, default_hybrid, or magazine",
            err=True,
        )
        raise typer.Exit(1)
    trip_for_layout = _trip_svc(trip_path).load(trip_path)
    use_dual_surfaces = dual or trip_for_layout.get("exportLayout", "auto") == "auto"
    try:
        if use_dual_surfaces:
            web_path, mobile_path, present_path = render_trip_surfaces(
                trip_path,
                out,
                export_mode=mode,
                validate=not no_validate,
                update_pipeline=mark_rendered,
                font_theme=theme_arg,
                copy_display_override=copy_display,
                reading_profile_override=reading_profile,
            )
            typer.echo(f"OK {web_path}")
            typer.echo(f"OK {mobile_path}")
            if present_path is not None:
                typer.echo(f"OK {present_path}")
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
            reading_profile_override=reading_profile,
        )
    except RenderError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {out_dir / out_html}")
    trip = _trip_svc(trip_path).load(trip_path)
    from travelogue.render.engine import should_include_long_shot, should_include_screenplay

    if should_include_screenplay(trip, layout_engine_override=web_layout):
        typer.echo("  放映: 封面或右下角「放映」· 建议用本地 http 打开（全屏需用户手势）")
        typer.echo("  文案切换: 右下角「隐藏文案/显示文案」（偏好保存在浏览器 sessionStorage）")
        if not should_include_long_shot(trip, layout_engine_override=web_layout):
            typer.echo("  保存长图: 右下角「保存长图」→ index-longshot.html 自动生成")
            typer.echo("  预览: python -m travelogue serve <trip>  （长图需 http，不可用 file://）")
    from travelogue.render.copy_display import is_photos_only, resolve_copy_display

    if is_photos_only(resolve_copy_display(trip, override=copy_display)):
        typer.echo("  纯照片模式: 已隐藏 hook/导语/图注（trip.json 文案保留，改 export.copyDisplay=full 可恢复）")
    if mode == "draft":
        typer.echo("  文案编辑: python -m travelogue serve <trip> 打开后点击文案保存到 trip.json")


@app.command("title-art")
def cmd_title_art(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    route_c: bool = typer.Option(
        False,
        "--route-c/--no-route-c",
        help="尝试路线 C（通义万相文生图），失败自动 fallback 路线 B（D-CAL-16）",
    ),
    style: str | None = typer.Option(
        None,
        "--style",
        help="路线 C styleId（cascade-seal | flowing-brush | loose-running-script | "
        "bold-vigorous | casual-handwritten），默认取风格库第一项",
    ),
    force: bool = typer.Option(
        False, "--force", help="忽略已有非 stale 结果，强制重新生成"
    ),
) -> None:
    """生成/刷新 trip.meta.titleArt（PRD-COVER-CALLIGRAPHY-TITLE-V1 §8）。"""
    import hashlib

    from travelogue.cover_engine.title_art import resolve_title_art
    from travelogue.media.source_resolve import resolve_source_path

    trip_path = _resolve(path)
    svc = _trip_svc(trip_path)
    trip = svc.load(trip_path)
    trip_dir = trip_path.parent
    art_dir = trip_dir / "trip-derived" / "title-art"
    cfg = get_config()
    ta = cfg.title_art

    def _resolve_asset_path(asset: dict) -> Path | None:
        return resolve_source_path(asset, trip_dir)

    def _write_png(data: bytes) -> str:
        art_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(data).hexdigest()[:12]
        out_path = art_dir / f"{digest}.png"
        out_path.write_bytes(data)
        return str(art_dir.relative_to(trip_dir) / out_path.name).replace("\\", "/")

    try:
        result = resolve_title_art(
            trip,
            resolve_asset_path=_resolve_asset_path,
            write_png=_write_png,
            route_c_enabled=route_c,
            route_c_style_id=style,
            force=force,
            model_name=ta.model_name,
            prompt_version=ta.prompt_version,
            route_c_max_attempts=ta.route_c_max_attempts,
            ocr_verify_enabled=ta.ocr_verify,
        )
    except Exception as exc:  # noqa: BLE001 — CLI 边界统一报错，不让异常裸奔
        typer.echo(f"E_TITLE_ART: {exc}", err=True)
        raise typer.Exit(1) from exc

    persist_trip_snapshot(svc, trip_path, trip)
    if result is None:
        title_art = (trip.get("meta") or {}).get("titleArt") or {}
        if title_art.get("enabled"):
            typer.echo("OK title-art · 已有有效结果，未重算（加 --force 强制刷新）")
        else:
            typer.echo("OK title-art · 未生成（非白名单 openingStyle / 标题为空 / 字形不覆盖，已 fail-open）")
        return
    engine_label = "路线C" if result.engine == "diffusion-fixed-prompt-v1" else "路线B"
    typer.echo(f"OK title-art · {engine_label} · {result.asset_path}")
    if result.fallback_from:
        typer.echo(f"  fallback: {result.fallback_from} → clean-pipeline-v1（D-CAL-16）")


@app.command("studio")
def cmd_studio(
    pick_folder: Path | None = typer.Option(
        None,
        "--pick-folder",
        help="album folder path; run pipeline before serving",
    ),
    pick_folder_dialog: bool = typer.Option(
        False,
        "--pick-folder-dialog",
        help="open Windows folder picker (IFileDialog) before serving",
    ),
    demo_album: bool = typer.Option(
        False,
        "--demo-album",
        help="import bundled demo album before serving (M11)",
    ),
    port: int = typer.Option(8766, "--port", "-p", help="HTTP port"),
    host: str = typer.Option("127.0.0.1", "--host", help="bind address"),
    allow_lan: bool = typer.Option(
        False,
        "--allow-lan",
        help="allow non-loopback bind with X-Studio-Token auth",
    ),
    no_open: bool = typer.Option(False, "--no-open", help="do not open browser"),
    title: str = typer.Option("我的旅途", "--title", help="trip title"),
    place: str = typer.Option("旅途", "--place", help="default place name"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir", help="trips root directory"),
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
) -> None:
    """Launch Studio workbench (serve --studio on trips directory)."""
    import webbrowser

    from travelogue.demo.build import DemoError
    from travelogue.desktop.single_instance import (
        open_existing_instance_or_stale,
        record_running_instance,
        release_single_instance,
        try_acquire_single_instance,
    )
    from travelogue.web.serve import serve_studio_directory
    from travelogue.web.studio_config import (
        log_studio_trips_dir,
        resolve_studio_config,
        resolve_studio_trips_dir,
    )
    from travelogue.web.studio_pipeline import run_studio_pipeline

    instance = try_acquire_single_instance()
    if not instance.owned:
        existing = open_existing_instance_or_stale()
        target = (existing.url if existing else f"http://{host}:{port}/")
        if not no_open:
            webbrowser.open(target)
        typer.echo(f"Studio 已在运行 · 打开 {target}")
        raise typer.Exit(0)

    resolved_config = config or resolve_studio_config()
    if resolved_config is not None:
        get_config(reload=True, path=resolved_config)
    cfg = get_config()
    root, trips_source = resolve_studio_trips_dir(
        cli_trips_dir=trips_dir,
        cfg_trips_dir=cfg.trips_dir,
    )
    log_studio_trips_dir(root, trips_source)
    root.mkdir(parents=True, exist_ok=True)

    album_path: Path | None = pick_folder
    if demo_album:
        from travelogue.desktop.demo_album import resolve_demo_album_dir

        album_path = resolve_demo_album_dir()
    elif pick_folder_dialog:
        from travelogue.desktop.folder_dialog import pick_folder as open_folder_dialog

        album_path = open_folder_dialog(title="选择照片文件夹")
        if album_path is None:
            release_single_instance(instance)
            typer.echo("未选择文件夹", err=True)
            raise typer.Exit(1)

    preview_url: str | None = None
    if album_path is not None:
        try:
            result = run_studio_pipeline(
                album_path,
                trips_dir=root,
                title=title,
                place=place,
                host=host,
                port=port,
                app_config=cfg,
            )
        except DemoError as exc:
            release_single_instance(instance)
            typer.echo(f"{exc.code}: {exc}", err=True)
            raise typer.Exit(1) from exc
        preview_url = result.preview_url
        typer.echo(f"OK studio pipeline · trip {result.trip_id}")
        typer.echo(f"  photos: {result.photo_count}")
        typer.echo(f"  preview: {preview_url}")

    if not no_open:
        webbrowser.open(preview_url or f"http://{host}:{port}/")

    try:
        # Record preferred port; serve may bump if busy — rewrite after bind via state file
        # updated inside serve is harder; record before and refresh after return is OK for
        # second-launch open (uses last written). We write again once serve starts via hook.
        record_running_instance(host=host, port=port)
        serve_studio_directory(
            root,
            port=port,
            host=host,
            app_config=cfg,
            allow_lan=allow_lan,
            config_path=resolved_config,
        )
    except KeyboardInterrupt:
        raise typer.Exit(0) from None
    finally:
        release_single_instance(instance)


@app.command("serve")
def cmd_serve(
    path: str = typer.Argument(..., help="trip directory, trip.json, tripId, or trips/ root with --studio"),
    port: int = typer.Option(8766, "--port", "-p", help="HTTP port"),
    host: str = typer.Option("127.0.0.1", "--host", help="bind address"),
    index: str = typer.Option("index.html", "--index", help="entry HTML filename"),
    rerender: bool = typer.Option(
        True,
        "--rerender/--no-rerender",
        help="re-render HTML after inline save (F-ED-03)",
    ),
    studio: bool = typer.Option(False, "--studio", help="Studio workbench mode (trips root)"),
    allow_lan: bool = typer.Option(
        False,
        "--allow-lan",
        help="allow non-loopback bind with X-Studio-Token auth",
    ),
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
    trips_dir: Path | None = typer.Option(None, "--trips-dir", help="trips root when path is tripId"),
) -> None:
    """Serve trip output with inline copy save API (draft editing)."""
    from travelogue.web.serve import (
        resolve_trip_serve_dir,
        serve_studio_directory,
        serve_trip_directory,
    )

    _load_cfg(config)
    cfg = get_config()
    if studio:
        root = Path(path).resolve() if path else (trips_dir or cfg.trips_dir).resolve()
        try:
            serve_studio_directory(
                root,
                port=port,
                host=host,
                auto_rerender=rerender,
                app_config=cfg,
                allow_lan=allow_lan,
                config_path=config,
            )
        except KeyboardInterrupt:
            raise typer.Exit(0) from None
        return
    try:
        trip_path = _resolve(path, trips_dir=trips_dir)
        serve_dir = resolve_trip_serve_dir(trip_path)
    except (TripNotFoundError, FileNotFoundError) as exc:
        typer.echo(f"E_SERVE: {exc}", err=True)
        raise typer.Exit(1) from exc
    if not (serve_dir / index).is_file():
        typer.echo(f"E_SERVE: {index} not found in {serve_dir} — run render first", err=True)
        raise typer.Exit(1)
    try:
        serve_trip_directory(
            serve_dir,
            port=port,
            host=host,
            index=index,
            auto_rerender=rerender,
            app_config=get_config(),
        )
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
    svc = _trip_svc(trip_path)
    trip = svc.load(trip_path)
    migrated = migrate_captions_to_assets(trip)
    if not migrated:
        typer.echo("OK migrate-captions · nothing to migrate")
        return
    if dry_run:
        typer.echo(f"OK migrate-captions · would migrate {len(migrated)} assets: {', '.join(migrated[:8])}")
        return
    persist_trip_snapshot(svc, trip_path, trip)
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

@app.command("export-pdf")
def cmd_export_pdf(
    path: str = typer.Argument(..., help="trip directory, trip.json, or tripId"),
    out: Path | None = typer.Option(None, "--out", "-o", help="output PDF path"),
    index: str = typer.Option("index.html", "--index", help="HTML entry (index.html | index-mobile.html)"),
    width: int = typer.Option(1200, "--width", help="PDF viewport width in px"),
    port: int = typer.Option(0, "--port", "-p", help="HTTP port (0 = random)"),
) -> None:
    """Export trip HTML to PDF via Playwright (requires playwright + chromium)."""
    from travelogue.export.pdf import PdfExportError, export_trip_pdf
    from travelogue.web.serve import resolve_trip_serve_dir

    try:
        trip_path = _resolve(path)
        serve_dir = resolve_trip_serve_dir(trip_path)
        out_path = export_trip_pdf(
            serve_dir,
            index=index,
            output=out,
            port=port,
            width_px=width,
        )
    except (TripNotFoundError, FileNotFoundError, PdfExportError) as exc:
        typer.echo(f"E_EXPORT_PDF: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK export-pdf · {out_path}")


@app.command("export-longshot")
def cmd_export_longshot(
    path: str = typer.Argument(..., help="trip directory, trip.json, or tripId"),
    out: Path | None = typer.Option(None, "--out", "-o", help="output PNG path (single file only)"),
    scale: int = typer.Option(1, "--scale", help="capture scale (1–3)"),
    format: str = typer.Option("png", "--format", "-f", help="png | jpeg"),
    chapter: int | None = typer.Option(None, "--chapter", help="export one chapter (1-based)"),
    port: int = typer.Option(0, "--port", "-p", help="HTTP port when no serve running (0 = random)"),
    platform: str | None = typer.Option(
        None,
        "--platform",
        help=(
            "wechat_chat (default) | wechat_moments | moments_grid | xiaohongshu | "
            "wechat_official | album_spread | instagram | weibo | douyin_cover | custom"
        ),
    ),
    intent: str | None = typer.Option(
        None,
        "--intent",
        help="chat_longshot | moments_scroll | moments_grid | xiaohongshu (Output Recipe)",
    ),
    slide_count: int | None = typer.Option(
        None,
        "--slide-count",
        help="aspect-fit slide count (xhs/ins/weibo/custom; moments/douyin ignore)",
    ),
    pad_mode: str | None = typer.Option(
        None,
        "--pad-mode",
        help="letterbox | smart_crop (aspect-fit platforms)",
    ),
    width: int | None = typer.Option(
        None,
        "--width",
        help="custom canvas width (only with --platform custom)",
    ),
    height: int | None = typer.Option(
        None,
        "--height",
        help="custom canvas height (only with --platform custom)",
    ),
) -> None:
    """Export trip longshot PNG via Playwright (requires playwright + chromium)."""
    import json
    import time

    from travelogue.config import get_config
    from travelogue.export.longshot import LongshotExportError, export_trip_longshot
    from travelogue.export.output_recipe import resolve_output_recipe
    from travelogue.export.output_recipe.types import OutputRecipeError
    from travelogue.export.platform_profiles import (
        PlatformProfileError,
        resolve_profile,
        with_custom_output,
    )
    from travelogue.web.serve import resolve_trip_serve_dir
    from travelogue.web.studio_homepage_telemetry import append_studio_homepage_event

    platform_id = platform or "wechat_chat"
    t0 = time.monotonic()
    try:
        append_studio_homepage_event(
            "longshot_export_start",
            {
                "platform": platform_id,
                "scale": scale,
                "slide_count": slide_count,
                "photo_count": None,
                "surface": "cli",
            },
        )
    except Exception:
        pass

    try:
        trip_path = _resolve(path)
        serve_dir = resolve_trip_serve_dir(trip_path)
        cfg = get_config()
        or_cfg = getattr(cfg.studio, "output_recipe", None)
        recipe_enabled = bool(getattr(or_cfg, "enabled", False))
        segment_mode = "auto"
        profile = None

        if recipe_enabled or intent:
            trip_data: dict = {}
            trip_json = serve_dir / "trip.json"
            if trip_json.is_file():
                try:
                    trip_data = json.loads(trip_json.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    trip_data = {}
            recipe = resolve_output_recipe(
                trip=trip_data,
                entrypoint="cli",
                enabled=True if intent else recipe_enabled,
                intent=intent,
                platform=platform,
            )
            if recipe.needs_intent:
                raise OutputRecipeError(
                    "E_OR_INTENT_REQUIRED", "CLI 需指定 --intent 或 --platform"
                )
            platform_id = recipe.platform or platform_id
            if platform_id == "wechat_chat" and recipe.layout in ("chapter", "by_chapter"):
                segment_mode = "chapter"
            elif platform_id == "wechat_chat" and recipe.layout == "single":
                segment_mode = "full"
        else:
            platform_id = platform or "wechat_chat"

        if platform_id and platform_id != "wechat_chat":
            profile = resolve_profile(
                platform_id, slide_count=slide_count, pad_mode=pad_mode
            )
            if profile.id == "custom":
                profile = with_custom_output(
                    profile, width=width, height=height, pad_mode=pad_mode
                )
            elif width is not None or height is not None:
                raise PlatformProfileError(
                    "E_LNG2_INVALID_CUSTOM_SIZE",
                    "--width/--height 仅用于 --platform custom",
                )
        elif width is not None or height is not None:
            raise PlatformProfileError(
                "E_LNG2_INVALID_CUSTOM_SIZE",
                "--width/--height 仅用于 --platform custom",
            )

        result = export_trip_longshot(
            serve_dir,
            scale=scale,
            fmt=format,
            chapter=chapter if platform_id == "wechat_chat" else None,
            output=out,
            port=port,
            platform=platform_id,
            slide_count=slide_count,
            pad_mode=pad_mode,
            profile=profile,
            segment_mode=segment_mode,
        )
    except (
        TripNotFoundError,
        FileNotFoundError,
        LongshotExportError,
        PlatformProfileError,
        OutputRecipeError,
    ) as exc:
        try:
            code = getattr(exc, "code", None) or type(exc).__name__
            append_studio_homepage_event(
                "longshot_export_fail",
                {
                    "platform": platform_id,
                    "error_code": str(code),
                    "surface": "cli",
                },
            )
        except Exception:
            pass
        code = getattr(exc, "code", None)
        if code:
            typer.echo(f"E_EXPORT_LONGSHOT: {code}: {exc}", err=True)
        else:
            typer.echo(f"E_EXPORT_LONGSHOT: {exc}", err=True)
        raise typer.Exit(1) from exc
    try:
        append_studio_homepage_event(
            "longshot_export_success",
            {
                "platform": getattr(result, "platform", None) or platform_id,
                "output_count": len(result.outputs),
                "target_page_count": getattr(result, "page_count", None),
                "duration_ms": int((time.monotonic() - t0) * 1000),
                "surface": "cli",
            },
        )
    except Exception:
        pass
    for item in result.outputs:
        typer.echo(f"OK export-longshot · {item.path} ({item.capture_method})")
    if getattr(result, "user_hint", ""):
        typer.echo(result.user_hint)
    if getattr(result, "publish_guide", ""):
        typer.echo(result.publish_guide)


@app.command("resolve-output-recipe")
def cmd_resolve_output_recipe(
    path: str = typer.Argument(..., help="trip directory, trip.json, or tripId"),
    entrypoint: str = typer.Option("cli", "--entrypoint", help="preview | shelf | cli"),
    intent: str | None = typer.Option(None, "--intent"),
    platform: str | None = typer.Option(None, "--platform"),
) -> None:
    """Print resolved Output Recipe JSON (debug / AC-OR)."""
    import json

    from travelogue.config import get_config
    from travelogue.export.output_recipe import resolve_output_recipe
    from travelogue.export.output_recipe.types import OutputRecipeError
    from travelogue.web.serve import resolve_trip_serve_dir

    try:
        trip_path = _resolve(path)
        serve_dir = resolve_trip_serve_dir(trip_path)
        trip_json = serve_dir / "trip.json"
        trip_data: dict = {}
        if trip_json.is_file():
            trip_data = json.loads(trip_json.read_text(encoding="utf-8"))
        cfg = get_config()
        or_cfg = getattr(cfg.studio, "output_recipe", None)
        recipe = resolve_output_recipe(
            trip=trip_data,
            entrypoint=entrypoint,
            enabled=bool(getattr(or_cfg, "enabled", False)),
            intent=intent,
            platform=platform,
        )
    except (TripNotFoundError, FileNotFoundError, OutputRecipeError, json.JSONDecodeError) as exc:
        typer.echo(f"E_OR_RESOLVE: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(recipe.to_dict(), ensure_ascii=False))


@app.command("preview")
def cmd_preview(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    out: Path | None = typer.Option(None, "--out", "-o", help="preview.jpg path"),
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
    output: Path | None = typer.Option(None, "--output", "-o", help="zip output path"),
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
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
) -> None:
    """Package index.html + assets into trip-{id}.zip (share mode)."""
    _load_cfg(config)
    trip_path = _resolve(path)
    try:
        zip_path = export_trip(
            trip_path,
            output_zip=output,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            validate=not no_validate,
            no_longshot=no_longshot,
            cfg=get_config(),
        )
    except (ExportError, RenderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {zip_path}")


@app.command("publish")
def cmd_publish(
    path: str = typer.Argument(..., help="trip.json path or tripId"),
    output: Path | None = typer.Option(None, "--output", "-o", help="zip output path"),
    confirm_privacy: bool = typer.Option(
        True,
        "--confirm-privacy/--no-confirm-privacy",
        help="confirm privacy before export (default on)",
    ),
    no_preview: bool = typer.Option(False, "--no-preview", help="skip preview.jpg"),
    no_validate: bool = typer.Option(False, "--no-validate", help="skip validation"),
    config: Path | None = typer.Option(None, "--config", help="config.yaml path"),
) -> None:
    """Validate → render (share) → preview → export zip."""
    _load_cfg(config)
    trip_path = _resolve(path)
    try:
        result: PublishResult = publish_trip(
            trip_path,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            output_zip=output,
            validate=not no_validate,
            cfg=get_config(),
        )
    except (ExportError, RenderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK index {result.index_html}")
    if result.preview_jpg:
        typer.echo(f"OK preview {result.preview_jpg}")
    typer.echo(f"OK zip {result.zip_path}")

