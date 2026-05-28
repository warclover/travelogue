"""Serve auto re-render after inline copy save."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.services.trip import TripService
from travelogue.web.copy_patch import CopyPatchError, apply_copy_patches
from travelogue.web.studio_chrome import inject_studio_chrome, should_inject_studio_chrome
from travelogue.web.studio_routes import StudioMixin
from travelogue.web.studio_uploads import sweep_stale_uploads
from travelogue.web.tier_patch import TierPatchError, apply_tier_promotions

SAVE_PATH = "/__travelogue/save-copy"
PROMOTE_TIER_PATH = "/__travelogue/promote-tier"
FAVICON_SILENT_PATHS = frozenset({"/favicon.ico", "/favicon.svg"})
MAX_JSON_BODY = 1_048_576
_trip_write_lock = threading.Lock()


class TripPreviewHandler(StudioMixin, SimpleHTTPRequestHandler):
    trip_json_path: Path
    auto_rerender: bool = True

    def __init__(
        self,
        *args,
        directory: str | None = None,
        trip_json: Path | None = None,
        auto_rerender: bool = True,
        studio_mode: bool = False,
        trips_dir: Path | None = None,
        studio_host: str = "127.0.0.1",
        studio_port: int = 8766,
        app_config: AppConfig | None = None,
        studio_token: str | None = None,
        studio_allow_lan: bool = False,
        studio_config_path: Path | None = None,
        **kwargs,
    ):
        self.trip_json_path = trip_json or Path("trip.json")
        self.auto_rerender = auto_rerender
        self.studio_mode = studio_mode
        self.trips_dir = trips_dir
        self.studio_host = studio_host
        self.studio_port = studio_port
        self.app_config = app_config
        self.studio_token = studio_token
        self.studio_allow_lan = studio_allow_lan
        self.studio_config_path = studio_config_path
        super().__init__(*args, directory=directory, **kwargs)

    @contextmanager
    def _app_config_scope(self) -> Iterator[AppConfig]:
        cfg = self.app_config
        if cfg is None:
            yield get_config()
        else:
            with app_config_scope(cfg) as active:
                yield active

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in FAVICON_SILENT_PATHS:
            self.send_response(204)
            self.end_headers()
            return
        if self.studio_mode:
            if self.studio_dispatch_GET(path):
                return
            parts = self.studio_trip_parts(path)
            if parts is not None:
                trip_id, rel_path = parts
                if self._serve_trip_static(trip_id, rel_path):
                    return
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if self.studio_mode:
            if self.studio_dispatch_POST(path):
                return
            api = self._studio_trip_api(path)
            if api is not None:
                trip_id, action = api
                if self.studio_bind_trip(trip_id) is None:
                    self.send_error(404)
                    return
                if action == "save-copy":
                    self._handle_save_copy()
                    return
                if action == "promote-tier":
                    self._handle_promote_tier()
                    return
            self.send_error(404)
            return
        if path == SAVE_PATH:
            self._handle_save_copy()
            return
        if path == PROMOTE_TIER_PATH:
            self._handle_promote_tier()
            return
        self.send_error(404)

    def _serve_trip_static(self, trip_id: str, rel_path: str) -> bool:
        trip_dir = self.studio_bind_trip(trip_id)
        if trip_dir is None:
            return False
        target = (trip_dir / rel_path).resolve()
        try:
            target.relative_to(trip_dir.resolve())
        except ValueError:
            return False
        if not target.is_file():
            self.send_error(404)
            return True

        if (
            should_inject_studio_chrome(rel_path)
            and target.suffix.lower() in {".html", ".htm"}
        ):
            html = target.read_text(encoding="utf-8", errors="replace")
            html = inject_studio_chrome(html, studio_token=self.studio_token)
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True

        old_directory = self.directory
        old_path = self.path
        self.directory = str(trip_dir)
        self.path = "/" + rel_path.replace("\\", "/")
        try:
            super().do_GET()
        finally:
            self.directory = old_directory
            self.path = old_path
        return True

    def _read_json_body(self, *, max_bytes: int = MAX_JSON_BODY) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > max_bytes:
            self._json_response(
                413,
                {
                    "ok": False,
                    "error": "E_STUDIO_BODY_TOO_LARGE",
                    "message": "request body too large",
                },
            )
            return {}
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json_response(400, {"ok": False, "error": "invalid JSON"})
            return {}
        return payload if isinstance(payload, dict) else {}

    def _handle_save_copy(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return
        patches = payload.get("patches")
        if not isinstance(patches, list) or not patches:
            self._json_response(400, {"ok": False, "error": "patches required"})
            return
        svc = TripService()
        rendered: list[str] = []
        try:
            with self._app_config_scope():
                with _trip_write_lock:
                    trip = svc.load(self.trip_json_path)
                    updated = apply_copy_patches(trip, patches)
                    svc.save(trip, self.trip_json_path)
                    if self.auto_rerender:
                        from travelogue.web.rerender import rerender_draft_trip

                        rendered = rerender_draft_trip(self.trip_json_path)
        except CopyPatchError as exc:
            self._json_response(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:
            self._json_response(500, {"ok": False, "error": str(exc)})
            return
        self._json_response(200, {"ok": True, "updated": updated, "rendered": rendered})

    def _handle_promote_tier(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return
        asset_ids = payload.get("assetIds")
        if not isinstance(asset_ids, list) or not asset_ids:
            self._json_response(400, {"ok": False, "error": "assetIds required"})
            return
        ids = [str(aid).strip() for aid in asset_ids if str(aid).strip()]
        svc = TripService()
        rendered: list[str] = []
        try:
            with self._app_config_scope():
                with _trip_write_lock:
                    trip = svc.load(self.trip_json_path)
                    promoted = apply_tier_promotions(trip, ids)
                    svc.save(trip, self.trip_json_path)
                    if self.auto_rerender and promoted:
                        from travelogue.web.rerender import rerender_draft_trip

                        rendered = rerender_draft_trip(self.trip_json_path)
        except TierPatchError as exc:
            self._json_response(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:
            self._json_response(500, {"ok": False, "error": str(exc)})
            return
        self._json_response(200, {"ok": True, "promoted": promoted, "rendered": rendered})

    def _json_response(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def serve_trip_directory(
    trip_dir: Path,
    *,
    port: int = 8766,
    host: str = "127.0.0.1",
    index: str = "index.html",
    auto_rerender: bool = True,
    app_config: AppConfig | None = None,
) -> None:
    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip.json not found in {trip_dir}")

    pinned_cfg = app_config or get_config()
    handler = partial(
        TripPreviewHandler,
        directory=str(trip_dir),
        trip_json=trip_json,
        auto_rerender=auto_rerender,
        studio_mode=False,
        app_config=pinned_cfg,
    )
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/{index}"
    print(f"Serving {trip_dir}")
    print(f"  preview: {url}")
    print(f"  inline edit saves to: {trip_json}")
    if auto_rerender:
        print("  auto re-render: index.html + index-longshot.html after save")
    else:
        print("  auto re-render: off (run render manually)")
    print("  Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def serve_studio_directory(
    trips_dir: Path,
    *,
    port: int = 8766,
    host: str = "127.0.0.1",
    auto_rerender: bool = True,
    app_config: AppConfig | None = None,
    allow_lan: bool = False,
    config_path: Path | None = None,
) -> None:
    from travelogue.web.studio_auth import ensure_studio_bind_allowed, is_loopback_host, new_studio_token

    ensure_studio_bind_allowed(host, allow_lan=allow_lan)
    trips_dir = trips_dir.resolve()
    trips_dir.mkdir(parents=True, exist_ok=True)
    sweep_stale_uploads(trips_dir)

    pinned_cfg = app_config or get_config()
    studio_token = new_studio_token() if allow_lan and not is_loopback_host(host) else None
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".studio-placeholder" / "trip.json",
        auto_rerender=auto_rerender,
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host=host,
        studio_port=port,
        app_config=pinned_cfg,
        studio_token=studio_token,
        studio_allow_lan=allow_lan,
        studio_config_path=config_path,
    )
    from travelogue.desktop.folder_picker_service import start_folder_picker_service

    start_folder_picker_service()
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"Studio mode · trips: {trips_dir}")
    print(f"  workbench: {url}")
    print(f"  import API: POST {url.rstrip('/')}/__travelogue/import")
    if studio_token:
        print(f"  studio token (POST header X-Studio-Token): {studio_token}")
    print("  Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def resolve_trip_serve_dir(path: Path) -> Path:
    path = path.resolve()
    if path.is_file() and path.name == "trip.json":
        return path.parent
    if path.is_dir():
        if (path / "trip.json").is_file():
            return path
        if (path / "index.html").is_file():
            return path
    raise FileNotFoundError(f"cannot serve {path}")
