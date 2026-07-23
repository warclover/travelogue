"""Serve auto re-render after inline copy save."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from travelogue.config import AppConfig, app_config_scope, get_config
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.trip import TripConflictError
from travelogue.web.copy_patch import CopyPatchError, apply_copy_patches
from travelogue.web.studio_auth import is_loopback_host, studio_request_authorized
from travelogue.web.studio_chrome import inject_studio_chrome, should_inject_studio_chrome
from travelogue.web.studio_errors import client_error_payload, internal_error_payload, user_message
from travelogue.web.studio_routes import StudioMixin
from travelogue.web.studio_uploads import sweep_stale_uploads
from travelogue.web.tier_patch import TierPatchError, apply_tier_promotions

SAVE_PATH = "/__travelogue/save-copy"
PROMOTE_TIER_PATH = "/__travelogue/promote-tier"
FAVICON_SILENT_PATHS = frozenset({"/favicon.ico", "/favicon.svg"})
MAX_JSON_BODY = 1_048_576
_log = logging.getLogger(__name__)


def _studio_static_authorized(handler: Any) -> bool:
    path = getattr(handler, "path", "") or ""
    query = path.split("?", 1)[1] if "?" in path else ""
    headers = getattr(handler, "headers", {}) or {}
    return studio_request_authorized(
        host=handler.studio_host,
        token=handler.studio_token,
        headers=headers,
        allow_lan=handler.studio_allow_lan,
        query=query,
    )


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

    def _request_path(self) -> str:
        """Percent-decode path so trip assets with non-ASCII names resolve on disk."""
        return unquote(self.path.split("?", 1)[0])

    def do_GET(self) -> None:  # noqa: N802
        path = self._request_path()
        if path in FAVICON_SILENT_PATHS:
            self.send_response(204)
            self.end_headers()
            return
        if self.studio_mode:
            if self.studio_dispatch_GET(path):
                return
            parts = self.studio_trip_parts(path)
            if parts is not None:
                if not _studio_static_authorized(self):
                    self._json_response(
                        401,
                        {
                            "ok": False,
                            "error": "E_STUDIO_AUTH",
                            "message": user_message("E_STUDIO_AUTH"),
                        },
                    )
                    return
                trip_id, rel_path = parts
                rel_path = unquote(rel_path)
                if self._serve_trip_static(trip_id, rel_path):
                    return
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        """PMX · Studio 路由对 HEAD 与 GET 对齐（至少 /v2 → 302）。"""
        if not self.studio_mode:
            super().do_HEAD()
            return
        path = self._request_path()
        if path in FAVICON_SILENT_PATHS:
            self.send_response(204)
            self.end_headers()
            return
        # 仅走无 body 的声明式路由（如 /v2 重定向）；首页 HTML 回 200 头即可
        from travelogue.web.studio_handlers.paths import HOME_CLASSIC_PATH, HOME_V2_PATH
        from travelogue.web.studio_handlers import static_handlers

        if path == HOME_V2_PATH:
            static_handlers.send_redirect(self, "/")
            return
        if path in ("/", HOME_CLASSIC_PATH):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        if self.studio_dispatch_GET(path):
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if self.studio_mode:
            if self.studio_dispatch_POST(path):
                return
            self.send_error(404)
            return
        if path in (SAVE_PATH, PROMOTE_TIER_PATH):
            if not is_loopback_host(self.studio_host):
                self._json_response(
                    403,
                    {
                        "ok": False,
                        "error": "E_STUDIO_AUTH",
                        "message": user_message("E_STUDIO_AUTH"),
                    },
                )
                return
            if path == SAVE_PATH:
                self._handle_save_copy()
                return
            self._handle_promote_tier()
            return
        self.send_error(404)

    def do_PATCH(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if self.studio_mode and self.studio_dispatch_PATCH(path):
            return
        if self.studio_mode:
            self.send_error(405)
            return
        self.send_error(405)

    def do_DELETE(self) -> None:  # noqa: N802
        path = unquote(self.path.split("?", 1)[0])
        if self.studio_mode and self.studio_dispatch_DELETE(path):
            return
        if self.studio_mode:
            self.send_error(405)
            return
        self.send_error(405)

    def _serve_trip_static(self, trip_id: str, rel_path: str) -> bool:
        # PDG · deleting gate：拒绝再 open 即将/正在删除的目录
        try:
            from travelogue.web.studio_jobs import get_job_store

            if get_job_store().is_trip_deleting(trip_id):
                self.send_error(404)
                return True
        except Exception:
            _log.debug("deleting gate check failed", exc_info=True)
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

        query = ""
        if "?" in self.path:
            query = self.path.split("?", 1)[1]

        if (
            should_inject_studio_chrome(rel_path, query)
            and target.suffix.lower() in {".html", ".htm"}
        ):
            from travelogue.web.studio_chrome import is_share_preview_query

            html = target.read_text(encoding="utf-8", errors="replace")
            html = inject_studio_chrome(
                html,
                studio_token=self.studio_token,
                share_mode=is_share_preview_query(query),
            )
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
        # V6 · style change: default repick cover; keepCover=true skips repick
        keep_cover = payload.get("keepCover") is True
        repick_cover = payload.get("repickCover")
        if repick_cover is None:
            repick_cover = not keep_cover
        else:
            repick_cover = bool(repick_cover) and not keep_cover
        fit_below_threshold = False
        svc = app_context_for_trip_json(self.trip_json_path, cfg=self.app_config).trip_service()
        rendered: list[str] = []
        try:
            with self._app_config_scope():

                def mutator(trip: dict) -> list[str]:
                    nonlocal fit_below_threshold
                    updated = apply_copy_patches(trip, patches)
                    style_patch = next(
                        (
                            p
                            for p in patches
                            if isinstance(p, dict)
                            and p.get("path") == "meta.coverOpeningStyle"
                        ),
                        None,
                    )
                    if style_patch and repick_cover:
                        from travelogue.cover_engine.joint import repick_cover_for_style

                        style_id = str(
                            (trip.get("meta") or {}).get("coverOpeningStyle") or ""
                        ).strip()
                        if style_id:
                            repick_cover_for_style(trip, style_id, layout="web")
                            for key in (
                                "coverAssetId",
                                "curation.coverByLayout",
                                "curation.coverStyleExplain",
                                "curation.coverJointLocked",
                            ):
                                if key not in updated:
                                    updated.append(key)
                    elif style_patch and keep_cover:
                        from travelogue.cover_engine.fit import style_fit_below_threshold
                        from travelogue.cover_engine.joint import apply_style_keep_cover
                        from travelogue.domain.cover_view import layout_eligible_assets

                        style_id = str(
                            (trip.get("meta") or {}).get("coverOpeningStyle") or ""
                        ).strip()
                        if style_id:
                            apply_style_keep_cover(trip, style_id)
                            for key in (
                                "curation.coverStyleExplain",
                                "curation.coverJointLocked",
                            ):
                                if key not in updated:
                                    updated.append(key)
                            curation = trip.get("curation") or {}
                            cover_by = curation.get("coverByLayout") or {}
                            asset_id = ""
                            if isinstance(cover_by, dict):
                                asset_id = str(cover_by.get("web") or "")
                            if not asset_id:
                                asset_id = str(trip.get("coverAssetId") or "")
                            if asset_id:
                                for asset in layout_eligible_assets(trip):
                                    if str(asset.get("id") or "") == asset_id:
                                        fit_below_threshold = style_fit_below_threshold(
                                            asset, style_id
                                        )
                                        break
                    return updated

                updated = svc.update(self.trip_json_path, mutator)
                if self.auto_rerender:
                    from travelogue.web.rerender import rerender_draft_trip

                    rendered = rerender_draft_trip(self.trip_json_path)
        except TripConflictError as exc:
            self._json_response(409, client_error_payload(exc))
            return
        except CopyPatchError as exc:
            self._json_response(400, client_error_payload(exc))
            return
        except Exception:
            _log.exception("copy patch failed for %s", self.trip_json_path)
            self._json_response(500, internal_error_payload())
            return
        self._json_response(
            200,
            {
                "ok": True,
                "updated": updated,
                "rendered": rendered,
                "fitBelowThreshold": fit_below_threshold,
            },
        )

    def _handle_promote_tier(self) -> None:
        payload = self._read_json_body()
        if not payload:
            return
        defer_rerender = payload.get("rerender") is False
        # D-FEED-05 · tier=material|demote → 取消精选；默认 featured 升格
        # FE-SFI-07 · action=restoreTimeOutlier → 移回主行程（豁免再隔离）
        raw_tier = str(payload.get("tier") or payload.get("action") or "featured").strip().lower()
        demote = raw_tier in ("material", "demote")
        restore_outlier = raw_tier in ("restoretimeoutlier", "restore_outlier", "restore-outlier")
        asset_ids = payload.get("assetIds")
        if not isinstance(asset_ids, list):
            asset_ids = []
        ids = [str(aid).strip() for aid in asset_ids if str(aid).strip()]
        if not ids and not restore_outlier:
            self._json_response(400, {"ok": False, "error": "assetIds required"})
            return
        svc = app_context_for_trip_json(self.trip_json_path, cfg=self.app_config).trip_service()
        rendered: list[str] = []
        try:
            with self._app_config_scope():

                def mutator(trip: dict) -> list[str]:
                    if restore_outlier:
                        from travelogue.curation.time_outlier import exempt_time_outlier

                        assets_by_id = {
                            str(a.get("id")): a
                            for a in (trip.get("assets") or [])
                            if isinstance(a, dict) and a.get("id")
                        }
                        target_ids = list(ids)
                        if not target_ids:
                            target_ids = [
                                str(x)
                                for x in (
                                    (trip.get("curation") or {}).get(
                                        "excludedTimeOutlierAssetIds"
                                    )
                                    or []
                                )
                                if x
                            ]
                        changed_ids: list[str] = []
                        for aid in target_ids:
                            asset = assets_by_id.get(aid)
                            if not asset:
                                continue
                            exempt_time_outlier(asset)
                            changed_ids.append(aid)
                        curation = trip.setdefault("curation", {})
                        excluded = [
                            x
                            for x in (curation.get("excludedTimeOutlierAssetIds") or [])
                            if str(x) not in set(changed_ids)
                        ]
                        if excluded:
                            curation["excludedTimeOutlierAssetIds"] = excluded
                        else:
                            curation.pop("excludedTimeOutlierAssetIds", None)
                        return changed_ids
                    if demote:
                        from travelogue.web.tier_patch import apply_tier_demotions

                        return apply_tier_demotions(trip, ids)
                    return apply_tier_promotions(trip, ids)

                changed = svc.update(self.trip_json_path, mutator)
                if self.auto_rerender and changed and not defer_rerender and not restore_outlier:
                    from travelogue.web.rerender import rerender_draft_trip

                    rendered = rerender_draft_trip(self.trip_json_path)
        except TripConflictError as exc:
            self._json_response(409, client_error_payload(exc))
            return
        except TierPatchError as exc:
            self._json_response(400, client_error_payload(exc))
            return
        except Exception:
            _log.exception("tier patch failed for %s", self.trip_json_path)
            self._json_response(500, internal_error_payload())
            return
        if restore_outlier:
            self._json_response(
                200,
                {
                    "ok": True,
                    "restored": changed,
                    "needsRecurate": True,
                    "message": "已移回主行程，请重新分章以更新章节",
                },
            )
            return
        if demote:
            self._json_response(200, {"ok": True, "demoted": changed, "rendered": rendered})
            return
        self._json_response(200, {"ok": True, "promoted": changed, "rendered": rendered})

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
    if not is_loopback_host(host):
        raise SystemExit(
            f"Trip preview refuses to bind to {host!r}; use 127.0.0.1 (loopback only)."
        )
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
        studio_host=host,
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
    from travelogue.web.studio_auth import ensure_studio_bind_allowed, new_studio_token
    from travelogue.web.studio_handlers.import_handlers import ensure_studio_trust_local_album

    # Match start-studio.bat / desktop launcher: local folder import works out of the box.
    # Explicit TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0 still locks down.
    ensure_studio_trust_local_album()
    ensure_studio_bind_allowed(host, allow_lan=allow_lan)
    trips_dir = trips_dir.resolve()
    trips_dir.mkdir(parents=True, exist_ok=True)
    sweep_stale_uploads(trips_dir)
    try:
        from travelogue.web.studio_trip_delete import sweep_deleting_tombstones

        sweep_deleting_tombstones(trips_dir)
    except Exception:
        _log.debug("sweep_deleting_tombstones skipped", exc_info=True)

    pinned_cfg = app_config or get_config()
    studio_token = new_studio_token() if allow_lan else None
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
    from travelogue.desktop.single_instance import record_running_instance
    from travelogue.web.studio_lifecycle import (
        bind_studio_server,
        clear_studio_server,
        register_studio_server,
    )

    start_folder_picker_service()

    def _warm_playwright() -> None:
        try:
            from travelogue.export.longshot import warm_playwright_browser

            if warm_playwright_browser():
                print("  playwright: warmed (longshot ready)")
            else:
                print("  playwright: unavailable (client longshot fallback)")
        except Exception:
            _log.debug("playwright warm skipped (optional)", exc_info=True)

    threading.Thread(target=_warm_playwright, daemon=True, name="playwright-warm").start()

    try:
        server, bound_port = bind_studio_server(host, port, handler)
    except OSError as exc:
        raise SystemExit(f"无法绑定 Studio 端口 {port}+：{exc}") from exc

    # Handler was created with the preferred port; update if we moved.
    if bound_port != port and getattr(handler, "keywords", None) is not None:
        handler.keywords["studio_port"] = bound_port
        print(f"  port {port} busy → using {bound_port}")

    try:
        record_running_instance(host=host, port=bound_port)
    except OSError:
        _log.debug("failed to write studio instance state", exc_info=True)

    shutdown_event = threading.Event()
    register_studio_server(server, shutdown_event)
    url = f"http://{host}:{bound_port}/"
    print(f"Studio mode · trips: {trips_dir}")
    print(f"  workbench: {url}")
    print(f"  import API: POST {url.rstrip('/')}/__travelogue/import")
    if studio_token:
        masked = f"****{studio_token[-4:]}" if len(studio_token) > 4 else "****"
        bootstrap = f"{url.rstrip('/')}/?studio_token={studio_token}"
        print(f"  LAN bootstrap (open once on this network): {bootstrap}")
        print(f"  studio token fingerprint: {masked}")
        print("  LAN mode: home requires bootstrap → HttpOnly session; APIs require session/token")
    print("  Ctrl+C or POST /__travelogue/shutdown to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        clear_studio_server(server)
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
