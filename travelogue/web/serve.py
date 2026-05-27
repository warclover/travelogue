"""Serve auto re-render after inline copy save."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from travelogue.services.trip import TripService
from travelogue.web.copy_patch import CopyPatchError, apply_copy_patches
from travelogue.web.tier_patch import TierPatchError, apply_tier_promotions

SAVE_PATH = "/__travelogue/save-copy"
PROMOTE_TIER_PATH = "/__travelogue/promote-tier"
FAVICON_SILENT_PATHS = frozenset({"/favicon.ico", "/favicon.svg"})
_trip_write_lock = threading.Lock()


class TripPreviewHandler(SimpleHTTPRequestHandler):
    trip_json_path: Path
    auto_rerender: bool = True

    def __init__(
        self,
        *args,
        directory: str | None = None,
        trip_json: Path | None = None,
        auto_rerender: bool = True,
        **kwargs,
    ):
        self.trip_json_path = trip_json or Path("trip.json")
        self.auto_rerender = auto_rerender
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] in FAVICON_SILENT_PATHS:
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == SAVE_PATH:
            self._handle_save_copy()
            return
        if path == PROMOTE_TIER_PATH:
            self._handle_promote_tier()
            return
        self.send_error(404)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
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
) -> None:
    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        raise FileNotFoundError(f"trip.json not found in {trip_dir}")

    handler = partial(
        TripPreviewHandler,
        directory=str(trip_dir),
        trip_json=trip_json,
        auto_rerender=auto_rerender,
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
