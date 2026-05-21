"""Build trip-{id}.zip for offline sharing."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path

from travelogue.export.exif import write_asset_to_zip
from travelogue.render.context import collect_asset_paths
from travelogue.render.engine import RenderError, render_trip, should_include_long_shot
from travelogue.render.preview import render_preview_jpg
from travelogue.services.trip import TripService
from travelogue.services.validate import validate_trip


class ExportError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
) -> Path:
    """
    Package share-ready zip: index.html, journal.css, assets/, preview.jpg.

    Requires --confirm-privacy (sets privacy.confirmedAt).
    Renders share HTML before packaging when auto_render is True.
    """
    if not confirm_privacy:
        raise ExportError(
            "E_EXPORT_PRIVACY",
            "pass --confirm-privacy to acknowledge export and strip display metadata",
        )

    trip_path = trip_path.resolve()
    trip_root = trip_path.parent
    svc = TripService()
    trip = svc.load(trip_path)

    if validate:
        errs = [e for e in validate_trip(trip) if not e.startswith("WARN:")]
        if errs:
            raise ExportError("E_VALIDATE", errs[0])

    do_strip = strip_exif
    if do_strip is None:
        do_strip = bool(trip.get("privacy", {}).get("stripExifOnExport", True))

    if no_longshot:
        trip.setdefault("export", {})["longShot"] = False
        svc.save(trip, trip_path)

    if auto_render:
        render_trip(trip_path, trip_root, export_mode="share", validate=False)
        trip = svc.load(trip_path)
        _mark_rendered(trip)
        svc.save(trip, trip_path)

    index = trip_root / "index.html"
    css = trip_root / "journal.css"
    if not index.is_file():
        raise ExportError("E_EXPORT_NOT_RENDERED", "index.html missing; run render first")

    if not css.is_file():
        from travelogue.paths import JOURNAL_CSS, JOURNAL_SCREENS_CSS
        import shutil

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

    max_zip_mb = 80
    photo_n = len(trip.get("assets") or [])

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(index, "index.html")
        zf.write(css, "journal.css")
        screens_css = trip_root / "journal-screens.css"
        if screens_css.is_file():
            zf.write(screens_css, "journal-screens.css")
        if preview_path.is_file():
            zf.write(preview_path, "preview.jpg")

        if should_include_long_shot(trip, export_mode="share"):
            for arc, path in longshot_files:
                if path.is_file():
                    zf.write(path, arc)

        for rel, abs_path in asset_paths:
            if rel in seen or not abs_path.is_file():
                continue
            seen.add(rel)
            write_asset_to_zip(zf, rel, abs_path, strip_exif=do_strip)

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
    svc.save(trip, trip_path)
    return zip_path
