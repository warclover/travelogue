"""Studio trip list, entry, aesthetic, and chapter layout handlers."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, urlparse

from travelogue.media.derivatives import stop_or_join_on_demand
from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    resolve_trip_dir_listed,
    studio_ctx,
    trip_id_from_query,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_handlers.trip_common import is_protected_demo_trip
from travelogue.web.studio_jobs import get_job_store
from travelogue.web.studio_trip_delete import (
    rename_trip_to_tombstone,
    spawn_async_rmtree,
)
from travelogue.web.studio_trip_id import is_valid_studio_trip_id
from travelogue.web.studio_trips import list_studio_trips_page

_log = logging.getLogger(__name__)


def handle_trips(handler: StudioHandlerProtocol) -> None:
    query = parse_qs(urlparse(handler.path).query)
    try:
        limit = int((query.get("limit") or ["20"])[0])
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 100))
    try:
        offset = int((query.get("offset") or ["0"])[0])
    except ValueError:
        offset = 0
    offset = max(0, offset)
    ctx = studio_ctx(handler)
    trips, total = list_studio_trips_page(ctx.trips_root, limit=limit, offset=offset)
    handler._json_response(200, {"ok": True, "trips": trips, "total": total})


def handle_delete_trip(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """PDG · begin_delete → stop on-demand → rename tombstone → 204 → async rmtree."""
    ctx = studio_ctx(handler)
    trip_dir = resolve_trip_dir_listed(ctx, trip_id)
    if trip_dir is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_TRIP_NOT_FOUND", "message": "画册不存在"},
        )
        return
    disk_id = trip_dir.name
    trip_json = trip_dir / "trip.json"
    try:
        trip = ctx.trip_service().load(trip_json)
    except Exception:
        _log.exception("load trip before delete failed for %s", trip_dir)
        handler._json_response(500, internal_error_payload())
        return
    if is_protected_demo_trip(disk_id, trip):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_TRIP_DELETE_DENIED",
                "message": "示例画册无法删除",
            },
        )
        return
    store = get_job_store()
    if not store.begin_trip_delete(disk_id):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_STUDIO_JOB_BUSY",
                "message": "导入进行中，请稍后再试",
            },
        )
        return
    try:
        stop_or_join_on_demand(trip_dir, timeout=2.0)
        tombstone = rename_trip_to_tombstone(trip_dir)
    except OSError:
        _log.exception("rename trip to tombstone failed for %s", trip_dir)
        store.end_trip_delete(disk_id)
        handler._json_response(
            500,
            {
                "ok": False,
                "error": "E_TRIP_DELETE_FAILED",
                "message": "删除失败，文件正被占用，请稍后再试",
            },
        )
        return
    except Exception:
        _log.exception("delete trip failed for %s", trip_dir)
        store.end_trip_delete(disk_id)
        handler._json_response(500, internal_error_payload())
        return
    handler.send_response(204)
    handler.end_headers()
    store.end_trip_delete(disk_id)
    spawn_async_rmtree(tombstone)


def handle_entry(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.domain.share_face_purity import migrate_share_face_purity_on_open
    from travelogue.layout_templates.css_stale import trip_render_bundle_stale
    from travelogue.services.trip import mark_render_bundle_current
    from travelogue.web.studio_entry import build_entry
    from travelogue.web.studio_jobs import get_job_store

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    # SFP D-SFP-12 · 打开预览静默 migrate（响应面立即净化；落盘 best-effort）
    title_snap = [
        (str(ch.get("id") or ""), str(ch.get("title") or ""))
        for ch in (trip.get("chapters") or [])
        if isinstance(ch, dict)
    ]
    migrated = migrate_share_face_purity_on_open(trip)
    title_after = [
        (str(ch.get("id") or ""), str(ch.get("title") or ""))
        for ch in (trip.get("chapters") or [])
        if isinstance(ch, dict)
    ]
    trip_json = _trip_dir / "trip.json"
    if not get_job_store().is_trip_busy(trip_id):
        try:
            # TripService.update always bumps revision when called. Only persist
            # when migrate mutated, and re-stamp so FirstSuccess does not false-
            # flag「预览需更新」. Also repair prior false-stale drift (rev>rendered)
            # left by older open-path writes.
            needs_persist = bool(migrated.get("changed"))
            # refresh_chapter_titles 曾把「生成串 ≠ 落盘截断」误报成章名变更。
            # 只有标题正文真的变了才撤印章并重渲，避免新建游记一打开就 pending。
            chapter_titles_changed = title_snap != title_after
            needs_stamp_repair = (not needs_persist) and trip_render_bundle_stale(
                _trip_dir, trip
            )
            if needs_persist or needs_stamp_repair:

                def _sfp_migrate(t: dict) -> bool:
                    if needs_persist:
                        migrate_share_face_purity_on_open(t)
                    # Chapter title changes must re-render HTML; stamping alone
                    # would leave 分章面板 vs 正文 <h2> out of sync.
                    if not chapter_titles_changed:
                        mark_render_bundle_current(t)
                    return True

                ctx.trip_service().update(
                    trip_json,
                    _sfp_migrate,
                    touch_updated=False,
                    bump_revision=needs_persist,
                )
                if needs_persist and chapter_titles_changed:
                    from travelogue.web.rerender import rerender_draft_trip

                    try:
                        rerender_draft_trip(trip_json)
                    except Exception:
                        _log.debug(
                            "sfp open migrate rerender skipped for %s",
                            trip_id,
                            exc_info=True,
                        )
        except Exception:
            _log.debug("sfp open migrate persist skipped for %s", trip_id, exc_info=True)

    enabled = bool(ctx.cfg.aesthetic.enabled)
    from travelogue.web.ai_surface import resolve_ai_surface_enabled
    from travelogue.web.studio_narrate import studio_llm_status

    ai_on = resolve_ai_surface_enabled(ctx.cfg)
    llm_ok = bool(studio_llm_status(cfg=ctx.cfg).get("llmAvailable")) if ai_on else False
    handler._json_response(
        200,
        {
            "ok": True,
            **build_entry(
                trip,
                trip_id,
                aesthetic_enabled=enabled,
                trip_dir=_trip_dir,
                ai_surface_enabled=ai_on,
                llm_ready=llm_ok,
            ),
        },
    )


def handle_aesthetic(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_aesthetic import build_aesthetic_studio_payload

    query = parse_qs(urlparse(handler.path).query)
    asset_id = (query.get("assetId") or query.get("asset_id") or [None])[0]
    try:
        limit = int((query.get("limit") or ["3"])[0])
    except ValueError:
        limit = 3
    limit = max(1, min(limit, 5))

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.cfg.aesthetic.enabled)
    asset_ids = [str(asset_id)] if asset_id else None
    payload = build_aesthetic_studio_payload(
        trip,
        enabled=enabled,
        asset_ids=asset_ids,
        limit=limit,
    )
    handler._json_response(200, {"ok": True, **payload})


def handle_patch_stratum_preference(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.album_profile import apply_stratum_preference
    from travelogue.web.studio_aesthetic import build_stratum_preference_studio_summary

    payload = handler._read_json_body()
    if not payload:
        return
    raw = payload.get("stratumPreference", payload.get("value"))
    if raw is None:
        handler._json_response(400, {"ok": False, "error": "stratumPreference required"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    ok, _ = trip_update_or_respond(
        handler,
        svc,
        trip_json,
        lambda t: apply_stratum_preference(t, str(raw)),
    )
    if not ok:
        return
    trip = svc.load(trip_json)
    handler._json_response(
        200,
        {"ok": True, "stratumPreference": build_stratum_preference_studio_summary(trip)},
    )


def handle_bento_preview(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.web.studio_bento_preview import build_trip_bento_preview

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    if payload is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_BENTO_PREVIEW_UNAVAILABLE", "message": "暂无预览图"},
        )
        return
    handler._json_response(200, {"ok": True, **payload})


def _ledger_bundle_fp(trip: dict) -> str:
    from travelogue.render.context import longshot_bundle_version

    return longshot_bundle_version(trip) if trip else ""


def handle_get_outputs(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """GET /trips/{id}/outputs · empty list when no ledger or flag off (AC-OLT-20)."""
    from travelogue.export.output_ledger import (
        annotate_outputs,
        output_ledger_enabled,
        read_ledger,
    )

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if not output_ledger_enabled():
        handler._json_response(200, {"ok": True, "outputs": []})
        return
    records = read_ledger(trip_dir)
    if records is None:
        handler._json_response(200, {"ok": True, "outputs": []})
        return
    handler._json_response(
        200,
        {
            "ok": True,
            "outputs": annotate_outputs(records, trip, _ledger_bundle_fp(trip)),
        },
    )


def handle_delete_output(handler: StudioHandlerProtocol, trip_id: str, output_id: str) -> None:
    from travelogue.export.output_ledger import delete_output, output_ledger_enabled

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if is_protected_demo_trip(trip_dir.name, trip):
        handler._json_response(
            403,
            {"ok": False, "error": "E_TRIP_DELETE_DENIED", "message": "示例画册无法删除"},
        )
        return
    if not output_ledger_enabled():
        handler._json_response(
            404,
            {"ok": False, "error": "E_OUTPUT_NOT_FOUND", "message": "没有这份成品"},
        )
        return
    if not delete_output(trip_dir, output_id):
        handler._json_response(
            404,
            {"ok": False, "error": "E_OUTPUT_NOT_FOUND", "message": "没有这份成品"},
        )
        return
    handler._json_response(200, {"ok": True})


def handle_chapter_layout(handler: StudioHandlerProtocol) -> None:
    from travelogue.curation.chapter_explain import (
        build_chapter_explain,
        build_layout_explain,
        ensure_snr_outlier_explain,
    )
    from travelogue.curation.mosaic_explain import build_mosaic_explain

    trip_id = trip_id_from_query(handler)
    if not trip_id or not is_valid_studio_trip_id(trip_id):
        handler._json_response(400, {"ok": False, "error": "tripId required"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    stored = ((trip.get("curation") or {}).get("clustering") or {}).get("userSummary")
    if isinstance(stored, dict) and stored.get("summary"):
        explain = dict(stored)
    else:
        explain = build_chapter_explain(trip, trip_dir=trip_dir)
    # SNR COPY-SNR-T02 · 即使命中缓存 userSummary 也补往年解释
    explain = ensure_snr_outlier_explain(explain, trip)
    curation = trip.get("curation") or {}
    layout_explain = build_layout_explain(curation)
    if layout_explain:
        explain["layoutExplain"] = layout_explain
    # LTN C6 · always refresh mosaic explain from live decision log (not stale userSummary).
    mosaic_explain = build_mosaic_explain(curation)
    if mosaic_explain:
        explain["mosaicExplain"] = mosaic_explain
    elif "mosaicExplain" in explain:
        explain.pop("mosaicExplain", None)
    handler._json_response(200, {"ok": True, **explain})


def handle_sibling_journal(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """CLG · GET /trips/{id}/sibling-journal。认不到也是 200。"""
    from travelogue.web.studio_pipeline import sibling_journal_for_trip

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    handler._json_response(
        200,
        sibling_journal_for_trip(trip, trip_id=trip_id, trips_dir=ctx.trips_root),
    )
