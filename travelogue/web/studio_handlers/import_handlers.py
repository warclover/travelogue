"""Studio album import (JSON and multipart).

Loopback album paths (folder picker / JSON ``albumPath``):
  - Always allowed: Studio uploads dir, demo album, paths under ``trips_root``.
  - Other local directories: only when ``TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1``
    (check-layer default **off**; Studio entry points ``setdefault`` to ``1``).
  - LAN (``--allow-lan``): uploads and demo only; requires ``X-Studio-Token``
    (header, cookie, or ``?studio_token=`` for static assets).
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import re
import threading
import time
from pathlib import Path

from travelogue.demo.build import DemoError
from travelogue.desktop.demo_album import is_demo_album_path
from travelogue.domain.title_humanize import humanize_folder_title
from travelogue.services.copy_subject import is_generic_place
from travelogue.web.studio_auth import is_loopback_host
from travelogue.web.studio_constants import (
    STUDIO_IMPORT_JOB_WATCH_SEC,
    STUDIO_MAX_MULTIPART_BODY_BYTES,
    STUDIO_USER_NOTES_MAX_LEN,
)
from travelogue.web.studio_errors import client_error_payload, demo_error_payload, user_message
from travelogue.web.studio_handlers.common import resolve_import_album_path, studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_jobs import get_job_store, run_import_job_subprocess
from travelogue.web.studio_multipart import parse_multipart_form
from travelogue.web.studio_pipeline import (
    assert_album_importable,
    infer_album_preview_date_range,
    list_album_preview_candidates,
    sample_album_preview_thumbs,
)
from travelogue.web.studio_uploads import (
    delete_upload_dir,
    save_upload_files,
    upload_dir_for_job,
    uploads_root,
)

_log = logging.getLogger(__name__)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_photo_cull_enabled(raw: object) -> bool:
    """PRD-P9-F1 · default false when missing or invalid (Import Sheet unchecked)."""
    if raw is None:
        return False
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in ("0", "false", "no", "off"):
        return False
    if text in ("1", "true", "yes", "on"):
        return True
    return False


def _parse_keep_near_duplicates(raw: object) -> bool:
    """PRD-P9-F2 · default false when missing or invalid (Import Sheet unchecked)."""
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    return False


def ensure_studio_trust_local_album() -> None:
    """Desktop Studio entry points: allow local folder-picker albums by default.

    Path checks still default to deny when Studio is not started via these
    entry points. Operators can set ``TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0``
    to lock down. LAN mode never trusts arbitrary local paths.
    """
    os.environ.setdefault("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")


def _studio_trust_local_album_paths() -> bool:
    # Default off: only uploads/demo/trips are allowed unless explicitly opted in.
    raw = os.environ.get("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _album_under_trips_root(album_path: Path, trips_root: Path) -> bool:
    try:
        album_path.resolve().relative_to(trips_root.resolve())
        return True
    except ValueError:
        return False


def _is_valid_iso_date(value: str) -> bool:
    if not value or not _ISO_DATE_RE.match(value):
        return False
    try:
        _dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _truthy_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in ("1", "true", "yes")


def _resolve_import_title(raw: object, *, user_set: bool) -> str:
    """Apply humanize only for default/folder titles; preserve user-edited titles."""
    title = str(raw or "").strip() or "我的旅途"
    if user_set:
        return title[:20]
    return humanize_folder_title(title)


def _normalize_user_date_range(start: str, end: str) -> tuple[dict | None, str | None]:
    start = str(start or "").strip()
    end = str(end or "").strip()
    if not start and not end:
        return None, None
    if start and not _is_valid_iso_date(start):
        return None, "开始日期格式无效，请使用 YYYY-MM-DD"
    if end and not _is_valid_iso_date(end):
        return None, "结束日期格式无效，请使用 YYYY-MM-DD"
    if start and end and start > end:
        return None, "开始日期不能晚于结束日期"
    payload: dict[str, str] = {"source": "user"}
    if start:
        payload["start"] = start
    if end:
        payload["end"] = end
    return payload, None


def read_import_request(handler: StudioHandlerProtocol) -> tuple[dict, Path | None]:
    content_type = handler.headers.get("Content-Type", "")
    if "multipart/form-data" in content_type:
        length = int(handler.headers.get("Content-Length") or 0)
        if length > STUDIO_MAX_MULTIPART_BODY_BYTES:
            raise DemoError("E_STUDIO_BODY_TOO_LARGE", "upload too large")
        body = handler.rfile.read(length) if length else b""
        fields, file_parts = parse_multipart_form(body, content_type)
        plan_bytes: bytes | None = None
        plan_filename = "plan.txt"
        photo_files: list[tuple[str, bytes]] = []
        for field_name, filename, content in file_parts:
            if field_name == "planFile":
                plan_bytes = content
                plan_filename = filename or "plan.txt"
            else:
                photo_files.append((filename, content))
        if not photo_files:
            raise DemoError("E_STUDIO_UPLOAD_EMPTY", "未收到任何照片文件")
        store = get_job_store()
        job = store.create_import_job()
        if job is None:
            raise DemoError("E_STUDIO_JOB_BUSY", "已有导入任务进行中，请稍候")
        ctx = studio_ctx(handler)
        upload_dir = upload_dir_for_job(ctx.trips_root, job.job_id)
        save_upload_files(upload_dir, photo_files)
        upload_place_raw = str(fields.get("place") or "").strip()
        upload_place_user_set = _truthy_flag(fields.get("placeUserSet")) or bool(
            upload_place_raw and not is_generic_place(upload_place_raw)
        )
        upload_title_user_set = _truthy_flag(fields.get("titleUserSet"))
        payload = {
            "albumPath": str(upload_dir),
            "title": _resolve_import_title(
                fields.get("title"), user_set=upload_title_user_set
            ),
            "titleUserSet": upload_title_user_set,
            "place": upload_place_raw or "旅途",
            "placeUserSet": upload_place_user_set,
            "force": fields.get("force", "").lower() in ("1", "true", "yes"),
            "forceStub": fields.get("forceStub", "").lower() in ("1", "true", "yes"),
            "_job": job,
        }
        import_mode = str(fields.get("mode") or fields.get("importMode") or "quick_share").strip().lower()
        payload["mode"] = import_mode
        notes = str(fields.get("userNotes") or "").strip()
        if notes:
            payload["userNotes"] = notes[:STUDIO_USER_NOTES_MAX_LEN]
        travel_notes = str(fields.get("travelNotes") or "").strip()
        if travel_notes:
            payload["travelNotes"] = travel_notes[:500]
        date_start = str(fields.get("dateRangeStart") or fields.get("dateStart") or "").strip()
        date_end = str(fields.get("dateRangeEnd") or fields.get("dateEnd") or "").strip()
        if date_start or date_end:
            payload["dateRange"] = {
                "start": date_start,
                "end": date_end,
                "source": "user",
            }
        featured_dir = str(fields.get("featuredDir") or "").strip()
        if featured_dir:
            payload["featuredDir"] = featured_dir
        material_dir = str(fields.get("materialDir") or "").strip()
        if material_dir:
            payload["materialDir"] = material_dir
        tm = str(fields.get("template_mode") or fields.get("templateMode") or "smart").strip().lower()
        payload["template_mode"] = tm if tm in ("smart", "manual") else "smart"
        tid = str(fields.get("template_id") or fields.get("templateId") or "").strip()
        if tid:
            payload["template_id"] = tid
        if import_mode == "fine_craft":
            from travelogue.curation.layout_density import normalize_layout_density

            # LTN R-A2 · illegal density raises ConfigError (caught in handle_import).
            payload["layoutDensity"] = normalize_layout_density(
                fields.get("layoutDensity")
            )
        payload["photoCullEnabled"] = _parse_photo_cull_enabled(
            fields.get("photoCullEnabled")
        )
        payload["keepNearDuplicates"] = _parse_keep_near_duplicates(
            fields.get("keepNearDuplicates")
        )
        if plan_bytes is not None:
            import base64

            payload["_planBytes"] = base64.b64encode(plan_bytes).decode("ascii")
            payload["_planFilename"] = plan_filename
        return payload, upload_dir

    payload = handler._read_json_body()
    if not payload:
        return {}, None
    return payload, None


def album_path_allowed(handler: StudioHandlerProtocol, album_path: Path, *, trips_root: Path) -> bool:
    album_path = album_path.resolve()
    if not album_path.is_dir():
        return False
    if is_demo_album_path(str(album_path)):
        return True
    try:
        album_path.relative_to(uploads_root(trips_root).resolve())
        return True
    except ValueError:
        pass
    if _album_under_trips_root(album_path, trips_root):
        return True
    if is_loopback_host(handler.studio_host) and not handler.studio_allow_lan:
        if _studio_trust_local_album_paths():
            _log.debug("studio import: trusted local album %s", album_path)
            return True
        return False
    return False


def handle_import(handler: StudioHandlerProtocol) -> None:
    from travelogue.config.errors import ConfigError

    try:
        payload, upload_dir = read_import_request(handler)
    except ConfigError as exc:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_STUDIO_INVALID_LAYOUT_DENSITY",
                "message": str(exc),
            },
        )
        return
    except DemoError as exc:
        status = 409 if exc.code in ("E_DEMO_EXISTS", "E_STUDIO_JOB_BUSY") else 400
        body = demo_error_payload(exc) if exc.code == "E_DEMO_EXISTS" else {
            "ok": False,
            "error": exc.code,
            "message": user_message(exc.code, str(exc)),
        }
        handler._json_response(status, body)
        return

    if not payload:
        return

    # Busy check before album validation so clients/probes see 409, not 403/400.
    if payload.get("_job") is None and get_job_store().is_import_running():
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": user_message("E_STUDIO_JOB_BUSY"),
            },
        )
        return

    precreated_job = payload.pop("_job", None)
    album_raw = str(payload.get("albumPath") or "").strip()
    use_demo_album = bool(payload.get("useDemoAlbum"))
    if not album_raw and not use_demo_album:
        handler._json_response(400, {"ok": False, "error": "albumPath required"})
        return

    try:
        album_path = resolve_import_album_path(album_raw, use_demo=use_demo_album)
    except DemoError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    ctx = studio_ctx(handler)
    trips_root = ctx.trips_root
    if not use_demo_album and not album_path_allowed(handler, album_path, trips_root=trips_root):
        if upload_dir:
            delete_upload_dir(upload_dir, trips_dir=trips_root)
        if precreated_job:
            get_job_store().finish_import()
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_STUDIO_ALBUM_DENIED",
                "message": user_message("E_STUDIO_ALBUM_DENIED"),
            },
        )
        return

    title_user_set = (
        _truthy_flag(payload.get("titleUserSet"))
        if "titleUserSet" in payload
        else False
    )
    title = _resolve_import_title(payload.get("title"), user_set=title_user_set)
    if use_demo_album:
        from travelogue.desktop.demo_album import DEMO_ALBUM_DISPLAY_TITLE
        from travelogue.domain.share_face_copy import is_unsafe_share_copy

        # PMX D1 · 示例导入默认锁定展示名；禁词/未显式改名一律回退
        if not title_user_set or is_unsafe_share_copy(title, kind="title"):
            title = DEMO_ALBUM_DISPLAY_TITLE
    place_raw = str(payload.get("place") or "").strip()
    place = place_raw or "旅途"
    place_user_set = (
        _truthy_flag(payload.get("placeUserSet"))
        if "placeUserSet" in payload
        else bool(place_raw and not is_generic_place(place_raw))
    )
    user_notes = (
        str(payload.get("userNotes") or "").strip()[:STUDIO_USER_NOTES_MAX_LEN] or None
    )
    travel_notes = str(payload.get("travelNotes") or "").strip()[:500] or None
    import_mode = str(payload.get("mode") or payload.get("importMode") or "quick_share").strip().lower()
    if import_mode not in ("quick_share", "fine_craft"):
        import_mode = "quick_share"
    date_range_raw = payload.get("dateRange") if isinstance(payload.get("dateRange"), dict) else {}
    date_start = str(
        date_range_raw.get("start")
        or payload.get("dateRangeStart")
        or payload.get("dateStart")
        or ""
    ).strip()
    date_end = str(
        date_range_raw.get("end")
        or payload.get("dateRangeEnd")
        or payload.get("dateEnd")
        or ""
    ).strip()
    date_range, date_err = _normalize_user_date_range(date_start, date_end)
    if date_err:
        if upload_dir:
            delete_upload_dir(upload_dir, trips_dir=trips_root)
        if precreated_job:
            get_job_store().finish_import()
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_STUDIO_DATE_RANGE_INVALID",
                "message": date_err,
            },
        )
        return
    featured_dir = str(payload.get("featuredDir") or "").strip() or None
    material_dir = str(payload.get("materialDir") or "").strip() or None
    plan_text = str(payload.get("planText") or "").strip() or None
    if plan_text and len(plan_text.encode("utf-8")) > 32 * 1024:
        plan_text = None
    plan_bytes_b64 = payload.pop("_planBytes", None)
    plan_filename = str(payload.pop("_planFilename", None) or "plan.txt")
    trip_id = payload.get("tripId")
    trip_id_str = str(trip_id).strip() if trip_id else None
    force = bool(payload.get("force"))
    force_stub = bool(payload.get("forceStub") or payload.get("force_stub"))
    template_mode = str(payload.get("template_mode") or payload.get("templateMode") or "smart").strip().lower()
    if template_mode not in ("smart", "manual"):
        template_mode = "smart"
    template_id_raw = payload.get("template_id") or payload.get("templateId")
    template_id_str = str(template_id_raw).strip() if template_id_raw else None
    photo_cull_enabled = _parse_photo_cull_enabled(payload.get("photoCullEnabled"))
    keep_near_duplicates = _parse_keep_near_duplicates(payload.get("keepNearDuplicates"))

    try:
        assert_album_importable(
            album_path,
            trips_dir=trips_root,
            title=title,
            place=place,
            trip_id=trip_id_str,
            force=force,
        )
    except DemoError as exc:
        if upload_dir:
            delete_upload_dir(upload_dir, trips_dir=trips_root)
        if precreated_job:
            get_job_store().finish_import()
        status = 409 if exc.code == "E_DEMO_EXISTS" else 400
        body = demo_error_payload(exc)
        body["ok"] = False
        handler._json_response(status, body)
        return

    store = get_job_store()
    job = precreated_job or store.create_import_job()
    if job is None:
        if upload_dir:
            delete_upload_dir(upload_dir, trips_dir=trips_root)
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "已有导入任务进行中，请稍候",
            },
        )
        return

    # Bind tripId early so cancel/fail purge + PATCH/DELETE busy checks work
    # even when force=True (otherwise job.trip_id stays None until success).
    if trip_id_str:
        store.update(job, trip_id=trip_id_str)
    else:
        from travelogue.util.trip_slug import demo_trip_id_from_album

        predicted = demo_trip_id_from_album(
            album_path, title=title, place=place, explicit=None
        )
        store.update(job, trip_id=predicted)

    host = handler.studio_host
    port = handler.studio_port
    job_id = job.job_id

    worker_payload = {
        "albumPath": str(album_path),
        "tripsDir": str(trips_root),
        "tripId": trip_id_str,
        "title": title,
        "place": place,
        "placeUserSet": place_user_set,
        "force": force,
        "forceStub": force_stub,
        "dedupe": not (use_demo_album or is_demo_album_path(str(album_path))),
        "host": host,
        "port": port,
        "mode": import_mode,
        "template_mode": template_mode,
        "photoCullEnabled": photo_cull_enabled,
        "keepNearDuplicates": keep_near_duplicates,
    }
    if template_id_str:
        worker_payload["template_id"] = template_id_str
    if user_notes:
        worker_payload["userNotes"] = user_notes
    if travel_notes:
        worker_payload["travelNotes"] = travel_notes
    if date_range:
        worker_payload["dateRange"] = date_range
    if featured_dir:
        worker_payload["featuredDir"] = featured_dir
    if material_dir:
        worker_payload["materialDir"] = material_dir
    if import_mode == "fine_craft":
        from travelogue.curation.layout_density import normalize_layout_density

        try:
            worker_payload["layoutDensity"] = normalize_layout_density(
                payload.get("layoutDensity")
            )
        except ConfigError as exc:
            if upload_dir:
                delete_upload_dir(upload_dir, trips_dir=trips_root)
            if precreated_job:
                get_job_store().finish_import()
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_STUDIO_INVALID_LAYOUT_DENSITY",
                    "message": str(exc),
                },
            )
            return
    if plan_text:
        worker_payload["planText"] = plan_text
    if plan_bytes_b64:
        worker_payload["planBytes"] = plan_bytes_b64
        worker_payload["planFilename"] = plan_filename
    from travelogue.web.studio_config import resolve_studio_config

    cfg_path = handler.studio_config_path
    if not (cfg_path and cfg_path.is_file()):
        cfg_path = resolve_studio_config()
    if cfg_path and cfg_path.is_file():
        worker_payload["configPath"] = str(cfg_path.resolve())

    def sweep_upload() -> None:
        finished = threading.Event()

        def watch() -> None:
            deadline = time.time() + STUDIO_IMPORT_JOB_WATCH_SEC
            while time.time() < deadline and not finished.is_set():
                current = store.get(job_id)
                if current and current.status in (
                    "succeeded",
                    "failed",
                    "cancelled",
                ):
                    finished.set()
                    # M3 · D-QH-05：任意终态都清 upload staging（成功/失败/取消）
                    if upload_dir:
                        delete_upload_dir(upload_dir, trips_dir=trips_root)
                    break
                time.sleep(0.5)

        threading.Thread(target=watch, daemon=True).start()

    run_import_job_subprocess(job, worker_payload)
    if upload_dir:
        sweep_upload()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})


def handle_album_preview(handler: StudioHandlerProtocol) -> None:
    payload = handler._read_json_body()
    if not payload:
        handler._json_response(400, {"ok": False, "error": "empty body"})
        return

    album_raw = str(payload.get("albumPath") or "").strip()
    use_demo_album = bool(payload.get("useDemoAlbum"))
    if not album_raw and not use_demo_album:
        handler._json_response(400, {"ok": False, "error": "albumPath required"})
        return

    try:
        album_path = resolve_import_album_path(album_raw, use_demo=use_demo_album)
    except DemoError as exc:
        handler._json_response(400, client_error_payload(exc))
        return

    ctx = studio_ctx(handler)
    trips_root = ctx.trips_root
    if not use_demo_album and not album_path_allowed(handler, album_path, trips_root=trips_root):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_STUDIO_ALBUM_DENIED",
                "message": user_message("E_STUDIO_ALBUM_DENIED"),
            },
        )
        return

    raw_count = payload.get("thumbCount")
    try:
        thumb_count = max(1, min(int(raw_count), 6)) if raw_count is not None else 4
    except (TypeError, ValueError):
        thumb_count = 4
    candidates = list_album_preview_candidates(album_path)
    thumbs, photo_count, thumb_names = sample_album_preview_thumbs(
        album_path, count=thumb_count, candidates=candidates
    )
    date_start, date_end = infer_album_preview_date_range(
        album_path, candidates=candidates, budget_s=1.0
    )
    payload: dict = {
        "ok": True,
        "thumbs": thumbs,
        "thumbNames": thumb_names,
        "photoCount": photo_count,
        "folderName": album_path.name,
    }
    if date_start:
        payload["dateStart"] = date_start
    if date_end:
        payload["dateEnd"] = date_end
    handler._json_response(200, payload)
