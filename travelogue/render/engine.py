"""Handlebars render engine for visual-journal."""

from __future__ import annotations

import shutil
from pathlib import Path

from pybars import Compiler

from travelogue.paths import (
    BREATH_CSS,
    BREATH_JS,
    BREATH_LENIS_JS,
    BREATH_GSAP_JS,
    COPY_DISPLAY_CSS,
    COPY_TOGGLE_JS,
    HTML2CANVAS_VENDOR,
    INLINE_EDIT_CSS,
    INLINE_EDIT_JS,
    JOURNAL_CSS,
    JOURNAL_SCREENS_CSS,
    LONGSHOT_CSS,
    LONGSHOT_JS,
    LONGSHOT_BRIDGE_JS,
    SCREENPLAY_BOOKMARKS_JS,
    SCREENPLAY_CSS,
    SCREENPLAY_HASH_JS,
    SCREENPLAY_JS,
    SHARE_JS,
    TEMPLATE_VISUAL_JOURNAL,
)
from travelogue.render.context import build_render_context, collect_asset_paths
from travelogue.services.validate import validate_trip


class RenderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


EXPORT_LAYOUT_LONGSHOT = "longshot"
LONGSHOT_INDEX_NAME = "index-longshot.html"


def should_include_long_shot(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
) -> bool:
    """P0: long-shot export on by default (draft + share). Set export.longShot=false to disable."""
    from travelogue.curation.screen_planner import screens_layout_active

    export_layout = export_layout_override or trip.get("exportLayout", "auto")
    if export_layout == EXPORT_LAYOUT_LONGSHOT:
        export_opts = trip.get("export") or {}
        flag = export_opts.get("longShot")
        if flag is None:
            return True
        return bool(flag)

    if screens_layout_active(trip, override=layout_engine_override):
        return False

    export_opts = trip.get("export") or {}
    flag = export_opts.get("longShot")
    if flag is None:
        return True
    return bool(flag)


def web_screens_surface_active(
    trip: dict,
    *,
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
) -> bool:
    """Web index with chapter screens[] (present / longshot-bridge eligibility)."""
    from travelogue.curation.screen_planner import screens_layout_active

    if not screens_layout_active(trip, override=layout_engine_override):
        return False

    export_layout = export_layout_override or trip.get("exportLayout", "auto")
    if export_layout in ("mobile", EXPORT_LAYOUT_LONGSHOT):
        return False

    chapters = trip.get("chapters") or []
    return any(ch.get("screens") for ch in chapters)


def should_include_screenplay(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
) -> bool:
    """Web screens slideshow: auto-play layout-screen blocks in fullscreen."""
    # AC-EXP-09 / experience-matrix inline_edit: draft preview disables present.
    if export_mode == "draft":
        return False

    return web_screens_surface_active(
        trip,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    )


def copy_longshot_bundle(out_dir: Path) -> None:
    """Copy longshot.js, share.js, longshot.css, copy-toggle, and vendored html2canvas."""
    out_dir = out_dir.resolve()
    for src, name in (
        (LONGSHOT_JS, "longshot.js"),
        (SHARE_JS, "share.js"),
        (LONGSHOT_CSS, "longshot.css"),
        (COPY_TOGGLE_JS, "copy-toggle.js"),
        (COPY_DISPLAY_CSS, "copy-display.css"),
    ):
        if not src.is_file():
            raise RenderError("E_RENDER_LONGSHOT", f"missing {src.name}")
        dest = out_dir / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)
    vendor_dir = out_dir / "vendor"
    vendor_dir.mkdir(parents=True, exist_ok=True)
    if not HTML2CANVAS_VENDOR.is_file():
        raise RenderError("E_RENDER_LONGSHOT", "missing vendor/html2canvas.min.js")
    dest_vendor = vendor_dir / "html2canvas.min.js"
    if dest_vendor.resolve() != HTML2CANVAS_VENDOR.resolve():
        shutil.copy2(HTML2CANVAS_VENDOR, dest_vendor)


def should_include_longshot_bridge(
    trip: dict,
    *,
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
) -> bool:
    """Web screens page: jump to index-longshot.html for save-longshot (P0 path A)."""
    return web_screens_surface_active(
        trip,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    ) and not should_include_long_shot(
        trip,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
    )


def _reading_payload_for_breath(
    trip: dict,
    *,
    export_mode: str = "draft",
    export_layout_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
) -> dict:
    from travelogue.config import get_config
    from travelogue.render.reading_profile import resolve_reading_payload

    cfg = get_config()
    return resolve_reading_payload(
        trip,
        export_mode=export_mode,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
        config_defaults={
            "draft_web_profile": cfg.render.reading.default_profile,
            "share_zip_profile": cfg.render.reading.share_profile,
            "mobile_profile": cfg.render.reading.mobile_profile,
            "longshot_surface_profile": cfg.render.reading.longshot_surface_profile,
        },
    )


def should_include_breath(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
) -> bool:
    payload = _reading_payload_for_breath(
        trip,
        export_mode=export_mode,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    )
    breath = (payload.get("scroll") or {}).get("breath", "off")
    return breath not in ("off", "", None)


def should_include_breath_flow(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
) -> bool:
    payload = _reading_payload_for_breath(
        trip,
        export_mode=export_mode,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    )
    return (payload.get("scroll") or {}).get("breath") == "flow"


def should_include_breath_scrub(
    trip: dict,
    *,
    export_mode: str = "draft",
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
) -> bool:
    payload = _reading_payload_for_breath(
        trip,
        export_mode=export_mode,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    )
    return (payload.get("scroll") or {}).get("breath") in ("cinematic", "gallery")


def copy_breath_bundle(out_dir: Path, *, include_flow: bool = False, include_scrub: bool = False) -> None:
    out_dir = out_dir.resolve()
    for src, name in ((BREATH_JS, "breath.js"), (BREATH_CSS, "breath.css")):
        if not src.is_file():
            raise RenderError("E_RENDER_BREATH", f"missing {src.name}")
        dest = out_dir / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)
    if include_flow:
        if not BREATH_LENIS_JS.is_file():
            raise RenderError("E_RENDER_BREATH", "missing breath-lenis.js")
        dest = out_dir / "breath-lenis.js"
        if dest.resolve() != BREATH_LENIS_JS.resolve():
            shutil.copy2(BREATH_LENIS_JS, dest)
    if include_scrub:
        if not BREATH_GSAP_JS.is_file():
            raise RenderError("E_RENDER_BREATH", "missing breath-gsap.js")
        dest = out_dir / "breath-gsap.js"
        if dest.resolve() != BREATH_GSAP_JS.resolve():
            shutil.copy2(BREATH_GSAP_JS, dest)


def write_longshot_sidecar(
    trip: dict,
    out_dir: Path,
    *,
    export_mode: str = "draft",
    trip_root: Path | None = None,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
) -> Path:
    """Write index-longshot.html (screens flattened to vertical stack) for capture from screens web."""
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

    out_dir = out_dir.resolve()
    html = render_html(
        trip,
        export_mode=export_mode,
        trip_root=trip_root,
        layout_engine_override=LAYOUT_ENGINE_SCREENS,
        export_layout_override=EXPORT_LAYOUT_LONGSHOT,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        index_name=LONGSHOT_INDEX_NAME,
    )
    dest = out_dir / LONGSHOT_INDEX_NAME
    dest.write_text(html, encoding="utf-8", newline="\n")
    copy_longshot_bundle(out_dir)
    return dest


def copy_screenplay_bundle(out_dir: Path) -> None:
    """Copy screenplay, copy-toggle, copy-display, and longshot-bridge assets."""
    out_dir = out_dir.resolve()
    for src, name in (
        (SCREENPLAY_HASH_JS, "screenplay-hash.js"),
        (SCREENPLAY_BOOKMARKS_JS, "screenplay-bookmarks.js"),
        (SCREENPLAY_JS, "screenplay.js"),
        (SCREENPLAY_CSS, "screenplay.css"),
        (COPY_TOGGLE_JS, "copy-toggle.js"),
        (COPY_DISPLAY_CSS, "copy-display.css"),
        (LONGSHOT_BRIDGE_JS, "longshot-bridge.js"),
    ):
        if not src.is_file():
            raise RenderError("E_RENDER_SCREENPLAY", f"missing {src.name}")
        dest = out_dir / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)


def copy_longshot_bridge_bundle(out_dir: Path) -> None:
    """Draft web toolbar: longshot bridge + copy toggles without present bundle."""
    out_dir = out_dir.resolve()
    for src, name in (
        (SCREENPLAY_CSS, "screenplay.css"),
        (COPY_TOGGLE_JS, "copy-toggle.js"),
        (COPY_DISPLAY_CSS, "copy-display.css"),
        (LONGSHOT_BRIDGE_JS, "longshot-bridge.js"),
    ):
        if not src.is_file():
            raise RenderError("E_RENDER_SCREENPLAY", f"missing {src.name}")
        dest = out_dir / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)


def copy_inline_edit_bundle(out_dir: Path) -> None:
    """Copy inline-edit assets for draft preview."""
    out_dir = out_dir.resolve()
    for src, name in (
        (INLINE_EDIT_JS, "inline-edit.js"),
        (INLINE_EDIT_CSS, "inline-edit.css"),
    ):
        if not src.is_file():
            raise RenderError("E_RENDER_INLINE_EDIT", f"missing {src.name}")
        dest = out_dir / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)


def _load_partials(compiler: Compiler, partials_dir: Path) -> dict:
    partials: dict = {}
    for path in sorted(partials_dir.glob("*.hbs")):
        name = path.stem
        partials[name] = compiler.compile(path.read_text(encoding="utf-8"))
    return partials


def _compile_template(compiler: Compiler, template_dir: Path) -> object:
    main = template_dir / "journal.hbs"
    if not main.is_file():
        raise RenderError("E_RENDER_TEMPLATE", f"missing {main}")
    return compiler.compile(main.read_text(encoding="utf-8"))


def render_html(
    trip: dict,
    *,
    template_id: str = "visual-journal",
    export_mode: str = "draft",
    trip_root: Path | None = None,
    template_dir: Path | None = None,
    layout_engine_override: str | None = None,
    export_layout_override: str | None = None,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
    index_name: str = "index.html",
    reading_profile_override: str | None = None,
) -> str:
    if template_id != "visual-journal":
        raise RenderError("E_RENDER_TEMPLATE", f"unsupported templateId: {template_id}")

    tdir = template_dir or TEMPLATE_VISUAL_JOURNAL
    partials_dir = tdir / "partials"
    compiler = Compiler()
    partials = _load_partials(compiler, partials_dir)
    template = _compile_template(compiler, tdir)
    ctx = build_render_context(
        trip,
        export_mode=export_mode,
        trip_root=trip_root,
        layout_engine_override=layout_engine_override,
        export_layout_override=export_layout_override,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    )
    return template(ctx, partials=partials)


def render_trip(
    trip_path: Path,
    out_dir: Path | None = None,
    *,
    export_mode: str = "draft",
    validate: bool = True,
    copy_css: bool = True,
    write_index: bool = True,
    index_name: str = "index.html",
    layout_engine: str | None = None,
    export_layout_override: str | None = None,
    update_pipeline: bool = False,
    include_longshot: bool | None = None,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
    reading_profile_override: str | None = None,
) -> Path:
    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    out_dir = (out_dir or trip_root).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from travelogue.services.trip import TripService

    trip = TripService().load(trip_path)

    if validate:
        errs = [e for e in validate_trip(trip) if not e.startswith("WARN:")]
        if errs:
            raise RenderError("E_VALIDATE", errs[0])

    for rel, abs_path in collect_asset_paths(trip, trip_root):
        if not abs_path.is_file():
            raise RenderError("E_RENDER_ASSET_MISSING", rel)

    html = render_html(
        trip,
        export_mode=export_mode,
        trip_root=trip_root,
        layout_engine_override=layout_engine,
        export_layout_override=export_layout_override,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    )

    if write_index:
        (out_dir / index_name).write_text(html, encoding="utf-8", newline="\n")

    if copy_css:
        for src, name in ((JOURNAL_CSS, "journal.css"), (JOURNAL_SCREENS_CSS, "journal-screens.css")):
            if not src.is_file():
                raise RenderError("E_RENDER_TEMPLATE", f"missing {src.name}")
            dest = out_dir / name
            if dest.resolve() != src.resolve():
                shutil.copy2(src, dest)

    if include_longshot is None:
        include_longshot = should_include_long_shot(
            trip,
            export_mode=export_mode,
            layout_engine_override=layout_engine,
            export_layout_override=export_layout_override,
        )
    if include_longshot:
        copy_longshot_bundle(out_dir)

    if should_include_screenplay(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine,
        export_layout_override=export_layout_override,
    ):
        copy_screenplay_bundle(out_dir)
    elif should_include_longshot_bridge(
        trip,
        layout_engine_override=layout_engine,
        export_layout_override=export_layout_override,
    ):
        copy_longshot_bridge_bundle(out_dir)

    if should_include_breath(
        trip,
        export_mode=export_mode,
        layout_engine_override=layout_engine,
        export_layout_override=export_layout_override,
        index_name=index_name,
        reading_profile_override=reading_profile_override,
    ):
        copy_breath_bundle(
            out_dir,
            include_flow=should_include_breath_flow(
                trip,
                export_mode=export_mode,
                layout_engine_override=layout_engine,
                export_layout_override=export_layout_override,
                index_name=index_name,
                reading_profile_override=reading_profile_override,
            ),
            include_scrub=should_include_breath_scrub(
                trip,
                export_mode=export_mode,
                layout_engine_override=layout_engine,
                export_layout_override=export_layout_override,
                index_name=index_name,
                reading_profile_override=reading_profile_override,
            ),
        )

    if (
        write_index
        and index_name == "index.html"
        and should_include_longshot_bridge(
            trip,
            layout_engine_override=layout_engine,
            export_layout_override=export_layout_override,
        )
    ):
        write_longshot_sidecar(
            trip,
            out_dir,
            export_mode=export_mode,
            trip_root=trip_root,
            font_theme=font_theme,
            copy_display_override=copy_display_override,
        )

    if export_mode == "draft":
        copy_inline_edit_bundle(out_dir)

    if update_pipeline:
        from datetime import datetime, timezone

        pipe = trip.setdefault("pipeline", {})
        pipe["status"] = "rendered"
        trip["updatedAt"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
        TripService().save(trip, trip_path)

    return out_dir


def render_trip_surfaces(
    trip_path: Path,
    out_dir: Path | None = None,
    *,
    export_mode: str = "draft",
    validate: bool = True,
    update_pipeline: bool = False,
    font_theme: str | None = None,
    copy_display_override: str | None = None,
    reading_profile_override: str | None = None,
) -> tuple[Path, Path]:
    """Write index.html (web + screens) and index-mobile.html (mobile + legacy) from one trip.json."""
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS

    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    out_dir = (out_dir or trip_root).resolve()

    web_index = render_trip(
        trip_path,
        out_dir,
        export_mode=export_mode,
        validate=validate,
        copy_css=True,
        index_name="index.html",
        layout_engine=LAYOUT_ENGINE_SCREENS,
        export_layout_override="web",
        update_pipeline=False,
        include_longshot=False,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        reading_profile_override=reading_profile_override,
    ) / "index.html"
    mobile_index = render_trip(
        trip_path,
        out_dir,
        export_mode=export_mode,
        validate=validate,
        copy_css=False,
        index_name="index-mobile.html",
        layout_engine=LAYOUT_ENGINE_LEGACY,
        export_layout_override="mobile",
        update_pipeline=update_pipeline,
        font_theme=font_theme,
        copy_display_override=copy_display_override,
        reading_profile_override=reading_profile_override,
    ) / "index-mobile.html"
    return web_index, mobile_index
