"""Studio album import (JSON and multipart)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

from travelogue.demo.build import DemoError
from travelogue.services.copy_subject import is_generic_place
from travelogue.desktop.demo_album import is_demo_album_path
from travelogue.web.studio_auth import is_loopback_host
from travelogue.web.studio_errors import demo_error_payload, user_message
from travelogue.web.studio_handlers.common import resolve_import_album_path, studio_ctx
from travelogue.web.studio_jobs import get_job_store, run_import_job_subprocess
from travelogue.web.studio_multipart import parse_multipart_form
from travelogue.web.studio_pipeline import assert_album_importable
from travelogue.web.studio_constants import (
    STUDIO_IMPORT_JOB_WATCH_SEC,
    STUDIO_MAX_MULTIPART_BODY_BYTES,
    STUDIO_USER_NOTES_MAX_LEN,
)
from travelogue.web.studio_uploads import (
    delete_upload_dir,
    save_upload_files,
    upload_dir_for_job,
    uploads_root,
)


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
        upload_place_user_set = str(fields.get("placeUserSet") or "").lower() in (
            "1",
            "true",
            "yes",
        ) or bool(upload_place_raw and not is_generic_place(upload_place_raw))
        payload = {
            "albumPath": str(upload_dir),
            "title": fields.get("title", "我的旅途"),
            "place": upload_place_raw or "旅途",
            "placeUserSet": upload_place_user_set,
            "force": fields.get("force", "").lower() in ("1", "true", "yes"),
            "_job": job,
        }
        notes = str(fields.get("userNotes") or "").strip()
        if notes:
            payload["userNotes"] = notes[:STUDIO_USER_NOTES_MAX_LEN]
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
    if is_demo_album_path(str(album_path)):
        return True
    try:
        album_path.relative_to(uploads_root(trips_root).resolve())
        return True
    except ValueError:
        pass
    if is_loopback_host(handler.studio_host) and not handler.studio_allow_lan:
        return album_path.is_dir()
    return False


def handle_import(handler: StudioHandlerProtocol) -> None:
    try:
        payload, upload_dir = read_import_request(handler)
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

    precreated_job = payload.pop("_job", None)
    album_raw = str(payload.get("albumPath") or "").strip()
    use_demo_album = bool(payload.get("useDemoAlbum"))
    if not album_raw and not use_demo_album:
        handler._json_response(400, {"ok": False, "error": "albumPath required"})
        return

    try:
        album_path = resolve_import_album_path(album_raw, use_demo=use_demo_album)
    except DemoError as exc:
        handler._json_response(400, {"ok": False, "error": exc.code, "message": str(exc)})
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

    title = str(payload.get("title") or "我的旅途").strip() or "我的旅途"
    place_raw = str(payload.get("place") or "").strip()
    place = place_raw or "旅途"
    place_user_set = (
        bool(payload.get("placeUserSet"))
        if "placeUserSet" in payload
        else bool(place_raw and not is_generic_place(place_raw))
    )
    user_notes = (
        str(payload.get("userNotes") or "").strip()[:STUDIO_USER_NOTES_MAX_LEN] or None
    )
    plan_text = str(payload.get("planText") or "").strip() or None
    if plan_text and len(plan_text.encode("utf-8")) > 32 * 1024:
        plan_text = None
    plan_bytes_b64 = payload.pop("_planBytes", None)
    plan_filename = str(payload.pop("_planFilename", None) or "plan.txt")
    trip_id = payload.get("tripId")
    trip_id_str = str(trip_id).strip() if trip_id else None
    force = bool(payload.get("force"))

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
        "dedupe": not (use_demo_album or is_demo_album_path(str(album_path))),
        "host": host,
        "port": port,
    }
    if user_notes:
        worker_payload["userNotes"] = user_notes
    if plan_text:
        worker_payload["planText"] = plan_text
    if plan_bytes_b64:
        worker_payload["planBytes"] = plan_bytes_b64
        worker_payload["planFilename"] = plan_filename
    if handler.studio_config_path and handler.studio_config_path.is_file():
        worker_payload["configPath"] = str(handler.studio_config_path.resolve())

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
                    if upload_dir and current.status == "succeeded":
                        delete_upload_dir(upload_dir, trips_dir=trips_root)
                    break
                time.sleep(0.5)

        threading.Thread(target=watch, daemon=True).start()

    run_import_job_subprocess(job, worker_payload)
    if upload_dir:
        sweep_upload()
    handler._json_response(202, {"ok": True, "jobId": job.job_id})
