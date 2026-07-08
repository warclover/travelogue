"""Build trip-{id}.zip for offline sharing."""

from __future__ import annotations

import zipfile
from pathlib import Path

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.errors import CodeError
from travelogue.export.exif import write_asset_to_zip
from travelogue.render.context import collect_asset_paths
from travelogue.render.engine import (
    LONGSHOT_INDEX_NAME,
    render_trip,
    should_include_long_shot,
    should_include_longshot_bridge,
    should_include_screenplay,
)
from travelogue.render.preview import render_preview_jpg
from travelogue.services.trip import persist_trip_snapshot
from travelogue.services.validate import validate_trip
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso


class ExportError(CodeError):
    pass


def _mark_rendered(trip: dict) -> None:
    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "rendered"
    trip["updatedAt"] = _utc_now_iso()


def _mark_exported(trip: dict, *, confirm_privacy: bool) -> None:
    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "exported"
    if confirm_privacy:
        privacy = trip.setdefault("privacy", {})
        privacy["confirmedAt"] = _utc_now_iso()
    trip["updatedAt"] = _utc_now_iso()


def export_trip(
    trip_path: Path,
    *,
    output_zip: Path | None = None,
    confirm_privacy: bool = False,
    no_preview: bool = False,
    strip_exif: bool | None = None,
    validate: bool = True,
    auto_render: bool = True,
    no_longshot: bool = False,
    cfg: AppConfig | None = None,
) -> Path:
    """
    Package share-ready zip: index.html, journal.css, assets/, preview.jpg.

    Requires --confirm-privacy (sets privacy.confirmedAt).
    Renders share HTML before packaging when auto_render is True.
    """
    with app_config_scope(cfg):
        return _export_trip_stages(
            trip_path,
            output_zip=output_zip,
            confirm_privacy=confirm_privacy,
            no_preview=no_preview,
            strip_exif=strip_exif,
            validate=validate,
            auto_render=auto_render,
            no_longshot=no_longshot,
        )


def _export_trip_stages(
    trip_path: Path,
    *,
    output_zip: Path | None = None,
    confirm_privacy: bool = False,
    no_preview: bool = False,
    strip_exif: bool | None = None,
    validate: bool = True,
    auto_render: bool = True,
    no_longshot: bool = False,
) -> Path:
    if not confirm_privacy:
        raise ExportError(
            "E_EXPORT_PRIVACY",
            "pass --confirm-privacy to acknowledge export and strip display metadata",
        )

    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    from travelogue.runtime import app_context_for_trip_json

    svc = app_context_for_trip_json(trip_path).trip_service()
    trip = svc.load(trip_path)

    if validate:
        errs = [e for e in validate_trip(trip) if not e.startswith("WARN:")]
        if errs:
            first = errs[0]
            from travelogue.services.validate import validation_error_code

            raise ExportError(validation_error_code(first), first)

    app_cfg = get_config()
    do_strip = strip_exif
    if do_strip is None:
        do_strip = bool(trip.get("privacy", {}).get("stripExifOnExport", True))

    if no_longshot:
        trip.setdefault("export", {})["longShot"] = False
        persist_trip_snapshot(svc, trip_path, trip)

    if auto_render:
        render_trip(trip_path, trip_root, export_mode="share", validate=False)
        trip = svc.load(trip_path)
        _mark_rendered(trip)
        persist_trip_snapshot(svc, trip_path, trip)

    index = trip_root / "index.html"
    css = trip_root / "journal.css"
    if not index.is_file():
        raise ExportError("E_EXPORT_NOT_RENDERED", "index.html missing; run render first")

    if not css.is_file():
        import shutil

        from travelogue.paths import JOURNAL_CSS, JOURNAL_SCREENS_CSS

        shutil.copy2(JOURNAL_CSS, css)
        screens_css = trip_root / "journal-screens.css"
        if not screens_css.is_file() and JOURNAL_SCREENS_CSS.is_file():
            shutil.copy2(JOURNAL_SCREENS_CSS, screens_css)

    preview_path = trip_root / "preview.jpg"
    if not no_preview:
        render_preview_jpg(trip_path, preview_path, trip_root=trip_root)

    trip_id = trip.get("tripId", trip_root.name)
    zip_path = (output_zip or trip_root / f"trip-{trip_id}.zip").resolve()

    asset_paths = collect_asset_paths(trip, trip_root)
    seen: set[str] = set()

    longshot_files = (
        ("longshot.js", trip_root / "longshot.js"),
        ("share.js", trip_root / "share.js"),
        ("longshot.css", trip_root / "longshot.css"),
        ("vendor/html2canvas.min.js", trip_root / "vendor" / "html2canvas.min.js"),
    )
    screenplay_files = (
        ("screenplay.js", trip_root / "screenplay.js"),
        ("screenplay.css", trip_root / "screenplay.css"),
        ("copy-toggle.js", trip_root / "copy-toggle.js"),
        ("copy-display.css", trip_root / "copy-display.css"),
    )

    max_zip_mb = app_cfg.export.max_zip_mb
    photo_n = len(trip.get("assets") or [])

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(index, "index.html")
            zf.write(css, "journal.css")
            screens_css = trip_root / "journal-screens.css"
            if screens_css.is_file():
                zf.write(screens_css, "journal-screens.css")
            if preview_path.is_file():
                zf.write(preview_path, "preview.jpg")

            wrote_longshot_bundle = False
            longshot_sidecar = trip_root / LONGSHOT_INDEX_NAME
            if longshot_sidecar.is_file() and should_include_longshot_bridge(trip):
                zf.write(longshot_sidecar, LONGSHOT_INDEX_NAME)
                wrote_longshot_bundle = True

            if should_include_long_shot(trip, export_mode="share") or wrote_longshot_bundle:
                for arc, path in longshot_files:
                    if path.is_file():
                        zf.write(path, arc)

            if should_include_screenplay(trip, export_mode="share"):
                for arc, path in screenplay_files:
                    if path.is_file():
                        zf.write(path, arc)

            for rel, abs_path in asset_paths:
                if rel in seen or not abs_path.is_file():
                    continue
                seen.add(rel)
                write_asset_to_zip(zf, rel, abs_path, strip_exif=do_strip)
    except Exception:
        try:
            zip_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    # Zip now exists beside index.html — re-render so share toolbar offers download.
    render_trip(trip_path, trip_root, export_mode="share", validate=False)

    zip_bytes = zip_path.stat().st_size
    if zip_bytes > max_zip_mb * 1024 * 1024:
        mb = round(zip_bytes / (1024 * 1024), 1)
        warn = (
            f"分享 zip 约 {mb} MB（>{max_zip_mb} MB），"
            f"含 {photo_n} 张图；建议减图或降低 srcset 档位"
        )
        curation = trip.setdefault("curation", {})
        warnings = list(curation.get("warnings") or [])
        if warn not in warnings:
            warnings.append(warn)
            curation["warnings"] = warnings

    _mark_exported(trip, confirm_privacy=True)
    persist_trip_snapshot(svc, trip_path, trip)
    return zip_path
