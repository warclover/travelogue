"""Studio HTTP routes (serve --studio)."""

from __future__ import annotations

import json
import mimetypes
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from travelogue.config import AppConfig, get_config
from travelogue.demo.build import DemoError
from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_chrome import should_inject_studio_chrome
from travelogue.web.studio_errors import demo_error_payload, user_message
from travelogue.web.studio_jobs import (
    get_job_store,
    run_import_job_subprocess,
    run_longshot_job,
    run_narrate_job,
)
from travelogue.web.studio_multipart import parse_multipart_form
from travelogue.web.studio_pipeline import assert_album_importable
from travelogue.web.studio_trips import list_studio_trips, studio_trips_total
from travelogue.web.studio_uploads import (
    delete_upload_dir,
    save_upload_files,
    sweep_stale_uploads,
    upload_dir_for_job,
    uploads_root,
)
from travelogue.desktop.demo_album import is_demo_album_path, resolve_demo_album_dir
from travelogue.web.studio_auth import is_loopback_host, studio_post_authorized
from travelogue.web.studio_trip_id import is_valid_studio_trip_id

MAX_JSON_BODY = 1_048_576
MAX_MULTIPART_BODY = 200 * 1024 * 1024


def _rel_to_trip(trip_dir: Path, target: Path) -> str:
    return target.resolve().relative_to(trip_dir.resolve()).as_posix()


def _resolve_import_album_path(album_raw: str, *, use_demo: bool = False) -> Path:
    if use_demo or is_demo_album_path(album_raw):
        return resolve_demo_album_dir()
    return Path(album_raw)

IMPORT_PATH = "/__travelogue/import"
STATUS_PATH = "/__travelogue/status"
CONFIG_PATH = "/__travelogue/config"
TRIPS_PATH = "/__travelogue/trips"
LONGSHOT_PATH = "/__travelogue/longshot"
NARRATE_PATH = "/__travelogue/narrate"
REVEAL_PATH = "/__travelogue/reveal"
CANCEL_PATH = "/__travelogue/cancel"
EXPORT_PATH = "/__travelogue/export"
PICK_FOLDER_PATH = "/__travelogue/pick-folder"
STUDIO_ASSET_PREFIX = "/__studio/"
SAVE_COPY_SUFFIX = "/__travelogue/save-copy"
PROMOTE_TIER_SUFFIX = "/__travelogue/promote-tier"


class StudioMixin:
    studio_mode: bool = False
    trips_dir: Path | None = None
    studio_host: str = "127.0.0.1"
    studio_port: int = 8766
    studio_token: str | None = None
    studio_allow_lan: bool = False
    studio_config_path: Path | None = None

    def _studio_require_post_auth(self) -> bool:
        if studio_post_authorized(
            host=self.studio_host,
            token=self.studio_token,
            headers=self.headers,
            allow_lan=self.studio_allow_lan,
        ):
            return True
        self._json_response(
            401,
            {
                "ok": False,
                "error": "E_STUDIO_AUTH",
                "message": user_message("E_STUDIO_AUTH"),
            },
        )
        return False

    def _album_path_allowed(self, album_path: Path, *, trips_root: Path) -> bool:
        album_path = album_path.resolve()
        if is_demo_album_path(str(album_path)):
            return True
        try:
            album_path.relative_to(uploads_root(trips_root).resolve())
            return True
        except ValueError:
            pass
        if is_loopback_host(self.studio_host) and not self.studio_allow_lan:
            return album_path.is_dir()
        return False

    def studio_dispatch_GET(self, path: str) -> bool:
        if path == "/":
            html_path = STUDIO_TEMPLATE_DIR / "studio.html"
            html = html_path.read_text(encoding="utf-8")
            token = self.studio_token or ""
            html = html.replace("__STUDIO_TOKEN__", token)
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True
        if path == STATUS_PATH:
            self._studio_handle_status()
            return True
        if path == CONFIG_PATH:
            self._studio_handle_config()
            return True
        if path == TRIPS_PATH:
            self._studio_handle_trips()
            return True
        if path.startswith(STUDIO_ASSET_PREFIX):
            rel = unquote(path[len(STUDIO_ASSET_PREFIX) :].lstrip("/"))
            asset = (STUDIO_TEMPLATE_DIR / rel).resolve()
            try:
                asset.relative_to(STUDIO_TEMPLATE_DIR.resolve())
            except ValueError:
                self.send_error(404)
                return True
            if not asset.is_file():
                self.send_error(404)
                return True
            ctype = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
            self._studio_send_file(asset, ctype)
            return True
        return False

    def studio_dispatch_POST(self, path: str) -> bool:
        if not self._studio_require_post_auth():
            return True
        if path == IMPORT_PATH:
            self._studio_handle_import()
            return True
        if path == LONGSHOT_PATH:
            self._studio_handle_longshot()
            return True
        if path == NARRATE_PATH:
            self._studio_handle_narrate()
            return True
        if path == REVEAL_PATH:
            self._studio_handle_reveal()
            return True
        if path == CANCEL_PATH:
            self._studio_handle_cancel()
            return True
        if path == EXPORT_PATH:
            self._studio_handle_export()
            return True
        if path == PICK_FOLDER_PATH:
            self._studio_handle_pick_folder()
            return True
        return False

    def studio_trip_parts(self, path: str) -> tuple[str, str] | None:
        if not path.startswith("/"):
            return None
        parts = path.strip("/").split("/", 1)
        if len(parts) != 2:
            return None
        trip_id, rel = parts[0], parts[1]
        if not trip_id or trip_id.startswith("_") or trip_id.startswith("__"):
            return None
        if not rel:
            return None
        return trip_id, rel

    def studio_bind_trip(self, trip_id: str) -> Path | None:
        if not self.trips_dir or not is_valid_studio_trip_id(trip_id):
            return None
        trips_root = self.trips_dir.resolve()
        trip_dir = (trips_root / trip_id).resolve()
        try:
            trip_dir.relative_to(trips_root)
        except ValueError:
            return None
        trip_json = trip_dir / "trip.json"
        if not trip_json.is_file():
            return None
        self.trip_json_path = trip_json
        return trip_dir

    def should_inject_studio_chrome(self, rel_path: str) -> bool:
        return should_inject_studio_chrome(rel_path)

    def _studio_cfg(self) -> AppConfig:
        return self.app_config or get_config()

    def _studio_send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _studio_handle_trips(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        try:
            limit = int((query.get("limit") or ["20"])[0])
        except ValueError:
            limit = 20
        limit = max(1, min(limit, 100))
        trips_root = self.trips_dir or self._studio_cfg().trips_dir
        trips = list_studio_trips(trips_root, limit=limit)
        total = studio_trips_total(trips_root)
        self._json_response(200, {"ok": True, "trips": trips, "total": total})

    def _studio_handle_status(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        job_ids = query.get("jobId") or query.get("jobid") or []
        if not job_ids:
            self._json_response(400, {"ok": False, "error": "jobId required"})
            return
        job = get_job_store().get(job_ids[0])
        if job is None:
            self._json_response(404, {"ok": False, "error": "job not found"})
            return
        self._json_response(200, job.to_dict())

    def _studio_handle_config(self) -> None:
        from travelogue.web.studio_narrate import studio_llm_status

        status = studio_llm_status(cfg=self._studio_cfg())
        self._json_response(200, {"ok": True, **status})

    def _studio_handle_pick_folder(self) -> None:
        import sys

        client_host = self.client_address[0] if self.client_address else ""
        if not is_loopback_host(client_host):
            self._json_response(
                403,
                {
                    "ok": False,
                    "error": "E_PICK_FOLDER_DENIED",
                    "message": user_message("E_PICK_FOLDER_DENIED"),
                },
            )
            return
        if sys.platform != "win32":
            self._json_response(
                501,
                {
                    "ok": False,
                    "error": "E_PICK_FOLDER_UNSUPPORTED",
                    "message": user_message("E_PICK_FOLDER_UNSUPPORTED"),
                },
            )
            return
        from travelogue.desktop.folder_picker_service import request_folder

        chosen = request_folder(title="选择照片文件夹")
        if chosen is None:
            self._json_response(200, {"ok": True, "cancelled": True})
            return
        self._json_response(200, {"ok": True, "albumPath": str(chosen.resolve())})

    def _studio_read_import_request(self) -> tuple[dict, Path | None]:
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" in content_type:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_MULTIPART_BODY:
                raise DemoError("E_STUDIO_BODY_TOO_LARGE", "upload too large")
            body = self.rfile.read(length) if length else b""
            fields, files = parse_multipart_form(body, content_type)
            if not files:
                raise DemoError("E_STUDIO_UPLOAD_EMPTY", "未收到任何照片文件")
            store = get_job_store()
            job = store.create_import_job()
            if job is None:
                raise DemoError("E_STUDIO_JOB_BUSY", "已有导入任务进行中，请稍候")
            trips_root = self.trips_dir or self._studio_cfg().trips_dir
            upload_dir = upload_dir_for_job(trips_root, job.job_id)
            save_upload_files(upload_dir, files)
            payload = {
                "albumPath": str(upload_dir),
                "title": fields.get("title", "我的旅途"),
                "place": fields.get("place", "旅途"),
                "force": fields.get("force", "").lower() in ("1", "true", "yes"),
                "_job": job,
            }
            return payload, upload_dir

        payload = self._read_json_body()
        if not payload:
            return {}, None
        return payload, None

    def _studio_handle_import(self) -> None:
        try:
            payload, upload_dir = self._studio_read_import_request()
        except DemoError as exc:
            status = 409 if exc.code in ("E_DEMO_EXISTS", "E_STUDIO_JOB_BUSY") else 400
            body = demo_error_payload(exc) if exc.code == "E_DEMO_EXISTS" else {
                "ok": False,
                "error": exc.code,
                "message": user_message(exc.code, str(exc)),
            }
            self._json_response(status, body)
            return

        if not payload:
            return

        precreated_job = payload.pop("_job", None)
        album_raw = str(payload.get("albumPath") or "").strip()
        use_demo_album = bool(payload.get("useDemoAlbum"))
        if not album_raw and not use_demo_album:
            self._json_response(400, {"ok": False, "error": "albumPath required"})
            return

        try:
            album_path = _resolve_import_album_path(album_raw, use_demo=use_demo_album)
        except DemoError as exc:
            self._json_response(400, {"ok": False, "error": exc.code, "message": str(exc)})
            return

        cfg = self._studio_cfg()
        trips_root = self.trips_dir or cfg.trips_dir
        if not use_demo_album and not self._album_path_allowed(album_path, trips_root=trips_root):
            if upload_dir:
                delete_upload_dir(upload_dir, trips_dir=trips_root)
            if precreated_job:
                get_job_store().finish_import()
            self._json_response(
                403,
                {
                    "ok": False,
                    "error": "E_STUDIO_ALBUM_DENIED",
                    "message": user_message("E_STUDIO_ALBUM_DENIED"),
                },
            )
            return

        title = str(payload.get("title") or "我的旅途").strip() or "我的旅途"
        place = str(payload.get("place") or "旅途").strip() or "旅途"
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
            self._json_response(status, body)
            return

        store = get_job_store()
        job = precreated_job or store.create_import_job()
        if job is None:
            if upload_dir:
                delete_upload_dir(upload_dir, trips_dir=trips_root)
            self._json_response(
                409,
                {
                    "ok": False,
                    "error": "E_STUDIO_JOB_BUSY",
                    "message": "已有导入任务进行中，请稍候",
                },
            )
            return

        host = self.studio_host
        port = self.studio_port
        job_id = job.job_id

        worker_payload = {
            "albumPath": str(album_path),
            "tripsDir": str(trips_root),
            "tripId": trip_id_str,
            "title": title,
            "place": place,
            "force": force,
            "dedupe": not (use_demo_album or is_demo_album_path(str(album_path))),
            "host": host,
            "port": port,
        }
        if self.studio_config_path and self.studio_config_path.is_file():
            worker_payload["configPath"] = str(self.studio_config_path.resolve())

        def sweep_upload() -> None:
            finished = {"done": False}

            def watch() -> None:
                deadline = time.time() + 600
                while time.time() < deadline and not finished["done"]:
                    current = store.get(job_id)
                    if current and current.status in (
                        "succeeded",
                        "failed",
                        "cancelled",
                    ):
                        finished["done"] = True
                        if upload_dir and current.status == "succeeded":
                            delete_upload_dir(upload_dir, trips_dir=trips_root)
                        break
                    time.sleep(0.5)

            threading.Thread(target=watch, daemon=True).start()

        run_import_job_subprocess(job, worker_payload)
        if upload_dir:
            sweep_upload()
        self._json_response(202, {"ok": True, "jobId": job.job_id})

    def _studio_handle_narrate(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return

        trip_id = str(payload.get("tripId") or "").strip()
        if not trip_id:
            self._json_response(400, {"ok": False, "error": "tripId required"})
            return

        trip_dir = self._studio_resolve_trip_dir(trip_id)
        if trip_dir is None:
            self._json_response(404, {"ok": False, "error": "trip not found"})
            return

        from travelogue.web.studio_narrate import run_studio_llm_narrate, studio_llm_status

        cfg = self._studio_cfg()
        llm_status = studio_llm_status(cfg=cfg)
        if not llm_status.get("llmAvailable"):
            self._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LLM_AUTH",
                    "message": "未配置 LLM API Key，无法生成杂志感文案",
                },
            )
            return

        store = get_job_store()
        job = store.create_narrate_job()
        if job is None:
            self._json_response(
                409,
                {
                    "ok": False,
                    "error": "E_STUDIO_JOB_BUSY",
                    "message": "已有文案生成任务进行中，请稍候",
                },
            )
            return

        def runner() -> dict:
            return run_studio_llm_narrate(trip_dir, cfg=cfg, trips_dir=trips_root)

        threading.Thread(
            target=lambda: run_narrate_job(job, runner=runner),
            daemon=True,
        ).start()
        self._json_response(202, {"ok": True, "jobId": job.job_id})

    def _studio_resolve_trip_dir(self, trip_id: str) -> Path | None:
        if not is_valid_studio_trip_id(trip_id):
            return None
        trips_root = (self.trips_dir or self._studio_cfg().trips_dir).resolve()
        trip_dir = (trips_root / trip_id).resolve()
        try:
            trip_dir.relative_to(trips_root)
        except ValueError:
            return None
        if not (trip_dir / "trip.json").is_file():
            return None
        return trip_dir

    def _studio_handle_longshot(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return

        trip_id = str(payload.get("tripId") or "").strip()
        if not trip_id:
            self._json_response(400, {"ok": False, "error": "tripId required"})
            return

        trip_dir = self._studio_resolve_trip_dir(trip_id)
        if trip_dir is None:
            self._json_response(404, {"ok": False, "error": "trip not found"})
            return

        store = get_job_store()
        job = store.create_longshot_job()
        if job is None:
            self._json_response(
                409,
                {
                    "ok": False,
                    "error": "E_STUDIO_JOB_BUSY",
                    "message": "已有长图任务进行中，请稍候",
                },
            )
            return

        scale = int(payload.get("scale") or 2)
        fmt = str(payload.get("format") or "png")

        def runner() -> dict:
            from travelogue.export.longshot import export_trip_longshot

            result = export_trip_longshot(
                trip_dir,
                scale=scale,
                fmt=fmt,
            )
            rel_outputs = [_rel_to_trip(trip_dir, item.path) for item in result.outputs]
            return {
                "tripId": trip_id,
                "outputs": rel_outputs,
                "captureMethod": result.capture_method,
                "segmented": len(result.outputs) > 1,
                "pageCount": len(result.outputs),
            }

        threading.Thread(
            target=lambda: run_longshot_job(job, runner=runner),
            daemon=True,
        ).start()
        self._json_response(202, {"ok": True, "jobId": job.job_id})

    def _studio_handle_reveal(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return

        trips_root = (self.trips_dir or self._studio_cfg().trips_dir).resolve()
        trip_id = str(payload.get("tripId") or "").strip()
        rel_path = str(payload.get("relPath") or "").strip()
        path_raw = str(payload.get("path") or "").strip()

        from travelogue.export.longshot import LongshotExportError, reveal_path_in_folder

        if trip_id and rel_path:
            trip_dir = self._studio_resolve_trip_dir(trip_id)
            if trip_dir is None:
                self._json_response(404, {"ok": False, "error": "trip not found"})
                return
            target = (trip_dir / rel_path).resolve()
            try:
                target.relative_to(trip_dir.resolve())
            except ValueError:
                self._json_response(
                    403,
                    {
                        "ok": False,
                        "error": "E_STUDIO_REVEAL_DENIED",
                        "message": user_message("E_STUDIO_REVEAL_DENIED"),
                    },
                )
                return
            path_raw = str(target)

        if not path_raw:
            self._json_response(400, {"ok": False, "error": "path or tripId+relPath required"})
            return

        try:
            reveal_path_in_folder(Path(path_raw), allowed_root=trips_root)
        except LongshotExportError as exc:
            self._json_response(
                403,
                {
                    "ok": False,
                    "error": exc.code,
                    "message": str(exc).split(": ", 1)[-1],
                },
            )
            return

        self._json_response(200, {"ok": True})

    def _studio_handle_cancel(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return

        job_id = str(payload.get("jobId") or "").strip()
        if not job_id:
            self._json_response(400, {"ok": False, "error": "jobId required"})
            return

        job = get_job_store().cancel_job(job_id)
        if job is None:
            self._json_response(404, {"ok": False, "error": "job not found"})
            return
        self._json_response(200, {"ok": True, "status": job.status})

    def _studio_handle_export(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return

        trip_id = str(payload.get("tripId") or "").strip()
        if not trip_id:
            self._json_response(400, {"ok": False, "error": "tripId required"})
            return

        trip_dir = self._studio_resolve_trip_dir(trip_id)
        if trip_dir is None:
            self._json_response(404, {"ok": False, "error": "trip not found"})
            return

        if not payload.get("confirmPrivacy"):
            self._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_EXPORT_PRIVACY",
                    "message": "导出 zip 需要确认隐私设置",
                },
            )
            return

        from travelogue.export.packager import ExportError, export_trip

        try:
            zip_path = export_trip(
                trip_dir / "trip.json",
                confirm_privacy=True,
            )
        except ExportError as exc:
            self._json_response(
                400,
                {"ok": False, "error": exc.code, "message": str(exc).split(": ", 1)[-1]},
            )
            return

        rel_zip = _rel_to_trip(trip_dir, zip_path)
        self._json_response(200, {"ok": True, "zipRelPath": rel_zip, "tripId": trip_id})

    def _studio_trip_api(self, path: str) -> tuple[str, str] | None:
        if path.endswith(SAVE_COPY_SUFFIX):
            trip_id = path[: -len(SAVE_COPY_SUFFIX)].strip("/")
            if trip_id and "/" not in trip_id:
                return trip_id, "save-copy"
        if path.endswith(PROMOTE_TIER_SUFFIX):
            trip_id = path[: -len(PROMOTE_TIER_SUFFIX)].strip("/")
            if trip_id and "/" not in trip_id:
                return trip_id, "promote-tier"
        return None
