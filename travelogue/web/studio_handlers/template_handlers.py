"""Phase 13 template list + route replay (admin/Studio API)."""



from __future__ import annotations



from urllib.parse import parse_qs, urlparse



from travelogue.templates.registry import check_template_health, get_registry

from travelogue.templating.admin_store import append_audit, get_store_revision

from travelogue.templating.decision_log import list_decisions

from travelogue.templating.resolver import is_template_locked, resolve_effective_template

from travelogue.templating.roles import require_template_role

from travelogue.templating.router import (

    RouterMode,

    apply_template_selection,

    replay_template_decision,

    route_template,

)

from travelogue.web.studio_handlers.common import resolve_trip_dir_listed, studio_ctx

from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol



_MODE_HINTS = {

    "smart": "根据天数、地点与视频占比自动匹配模板；不确定时回退视觉游记。",

    "manual": "全程使用你指定的模板，适合已知体裁（活动回顾、多日游记等）。",

}





def _template_labels() -> dict[str, str]:

    return {

        "visual-journal": "视觉游记",

        "event-recap": "活动回顾",

    }





def _sort_templates(items: list[dict], order: tuple[str, ...]) -> list[dict]:

    rank = {tid: i for i, tid in enumerate(order)}



    def key(row: dict) -> tuple[int, str]:

        tid = str(row.get("templateId") or "")

        return (rank.get(tid, 999), tid)



    return sorted(items, key=key)





def handle_templates_list(handler: StudioHandlerProtocol) -> None:

    ctx = studio_ctx(handler)

    reg = get_registry()

    tr = ctx.cfg.template_router

    from travelogue.templating.admin_store import get_effective_lifecycle



    allow_beta = frozenset(tr.beta_allowlist_trip_ids)

    items = []

    for rec in reg.list_for_consumer(include_beta=bool(allow_beta), allowlist=allow_beta or None):

        lc = get_effective_lifecycle(rec.template_id, default=rec.lifecycle)

        items.append(

            {

                "templateId": rec.template_id,

                "label": _template_labels().get(rec.template_id, rec.template_id),

                "lifecycle": lc,

                "version": rec.version,
                "revision": rec.revision,

            }

        )

    from travelogue.templating.admin_store import load_runtime
    from travelogue.templating.discovery import sort_consumer_templates

    rt = load_runtime()
    recommended = tuple(str(x) for x in (rt.get("recommended_templates") or tr.display_order))
    sort_mode = str(getattr(tr, "discovery_sort_mode", None) or "recommended")
    team = tuple(str(x) for x in (rt.get("recommended_templates") or tr.display_order))
    items = sort_consumer_templates(
        items,
        display_order=tr.display_order,
        recommended=recommended,
        sort_mode=sort_mode,
        team_templates=team,
    )

    handler._json_response(

        200,

        {

            "ok": True,

            "defaultMode": "smart",

            "smartLabel": "智能匹配（推荐）",

            "modeHints": _MODE_HINTS,

            "templates": items,

            "routerEnabled": tr.enabled,

            "shadowMode": tr.shadow_mode,

            "adminRevision": get_store_revision(),

        },

    )





def _load_trip(handler: StudioHandlerProtocol, trip_id: str):

    ctx = studio_ctx(handler)

    try:

        trip_json = ctx.trip_service().resolve_trip_json(trip_id, trips_dir=ctx.trips_root)

        trip = ctx.trip_service().load(trip_json)

        return ctx, trip_json.parent, trip

    except Exception:

        return None





def _template_operator_role(handler: StudioHandlerProtocol) -> str | None:

    ctx = studio_ctx(handler)

    ok, role, _code = require_template_role(

        handler.headers,

        host=handler.studio_host,

        allow_lan=handler.studio_allow_lan,

        minimum="template_operator",

        cfg=ctx.cfg,

    )

    return role if ok else None





def handle_template_replay(handler: StudioHandlerProtocol) -> None:

    payload = handler._read_json_body() or {}

    trip_id = str(payload.get("tripId") or "").strip()

    if not trip_id:

        handler._json_response(400, {"ok": False, "error": "tripId required"})

        return



    loaded = _load_trip(handler, trip_id)

    if loaded is None:

        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})

        return

    ctx, _trip_dir, trip = loaded

    replay = replay_template_decision(trip, cfg=ctx.cfg)

    role = _template_operator_role(handler)

    if role:
        tid = str((trip.get("templateSelection") or {}).get("resolvedTemplateId") or "*")
        append_audit(
            "replay",
            operator=role,
            template_id=tid,
            detail={"tripId": trip_id, "match": replay.get("match")},
        )
        from travelogue.templating.metrics import record_admin_replay

        record_admin_replay(operator=role, template_id=tid, trip_id=trip_id)

    handler._json_response(200, {"ok": True, "tripId": trip_id, **replay})





def handle_template_recompute(handler: StudioHandlerProtocol) -> None:

    """Debug: recompute templateSelection (respects lock)."""

    if not _template_operator_role(handler):

        handler._json_response(

            403,

            {"ok": False, "error": "E_TEMPLATE_PERMISSION_DENIED", "message": "需要 template_operator"},

        )

        return

    payload = handler._read_json_body() or {}

    trip_id = str(payload.get("tripId") or "").strip()

    if not trip_id:

        handler._json_response(400, {"ok": False, "error": "tripId required"})

        return

    dry_run = bool(payload.get("dryRun") or payload.get("dry_run"))

    loaded = _load_trip(handler, trip_id)

    if loaded is None:

        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})

        return

    ctx, trip_dir, trip = loaded

    if is_template_locked(trip):

        handler._json_response(

            409,

            {

                "ok": False,

                "error": "E_TEMPLATE_LOCKED",

                "message": "文案已锁定，禁止重算模板",

            },

        )

        return

    mode = str(payload.get("mode") or (trip.get("templateSelection") or {}).get("mode") or "smart")

    if mode not in ("smart", "manual"):

        mode = "smart"

    requested = payload.get("templateId") or payload.get("requestedTemplateId")

    if dry_run:

        fresh = route_template(

            trip,

            mode=mode,  # type: ignore[arg-type]

            requested_template_id=str(requested) if requested else None,

            cfg=ctx.cfg,

        )

        handler._json_response(

            200,

            {"ok": True, "tripId": trip_id, "dryRun": True, "selection": fresh, "features": replay_template_decision(trip, cfg=ctx.cfg)["features"]},

        )

        return

    before = dict(trip.get("templateSelection") or {})

    selection = apply_template_selection(

        trip,

        mode=mode,  # type: ignore[arg-type]

        requested_template_id=str(requested) if requested else None,

        cfg=ctx.cfg,

        recompute=True,

        trip_dir=trip_dir,

        log_action="recompute",

    )

    ctx.trip_service().save(trip, trip_dir / "trip.json")

    role = _template_operator_role(handler) or "studio"

    append_audit(

        "recompute",

        operator=role,

        template_id=str(selection.get("resolvedTemplateId") or "*"),

        detail={"tripId": trip_id, "beforeHash": before.get("decisionHash"), "afterHash": selection.get("decisionHash")},

    )

    handler._json_response(200, {"ok": True, "tripId": trip_id, "selection": selection, "changed": before.get("decisionHash") != selection.get("decisionHash")})





def handle_template_decisions(handler: StudioHandlerProtocol) -> None:

    """List per-trip template decision log (AC-P13-07)."""

    query = parse_qs(urlparse(handler.path).query)

    trip_id = (query.get("tripId") or query.get("trip_id") or [""])[0].strip()

    if not trip_id:

        handler._json_response(400, {"ok": False, "error": "tripId query required"})

        return

    try:

        limit = int((query.get("limit") or ["20"])[0])

    except ValueError:

        limit = 20

    ctx = studio_ctx(handler)

    trip_dir = resolve_trip_dir_listed(ctx, trip_id)

    if trip_dir is None:

        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})

        return

    handler._json_response(

        200,

        {"ok": True, "tripId": trip_id, "decisions": list_decisions(trip_dir, limit=limit)},

    )





def handle_template_preview(handler: StudioHandlerProtocol) -> None:

    """One-off route preview for templateId without persisting trip (PRD §4.4)."""

    if not _template_operator_role(handler):

        handler._json_response(403, {"ok": False, "error": "E_TEMPLATE_PERMISSION_DENIED"})

        return

    payload = handler._read_json_body() or {}

    trip_id = str(payload.get("tripId") or "").strip()

    template_id = str(payload.get("templateId") or "").strip()

    if not trip_id or not template_id:

        handler._json_response(400, {"ok": False, "error": "tripId and templateId required"})

        return

    loaded = _load_trip(handler, trip_id)

    if loaded is None:

        handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})

        return

    ctx, _trip_dir, trip = loaded

    healthy, errors = check_template_health(template_id)

    preview_trip = dict(trip)

    preview_trip["templateSelection"] = {

        **dict(preview_trip.get("templateSelection") or {}),

        "mode": "manual",

        "requestedTemplateId": template_id,

        "resolvedTemplateId": template_id,

    }

    preview_trip["templateId"] = template_id

    dry_render = bool(payload.get("render") or payload.get("dryRender"))
    body: dict = {
        "ok": True,
        "tripId": trip_id,
        "templateId": template_id,
        "healthy": healthy,
        "healthErrors": errors,
        "effectiveTemplate": resolve_effective_template(preview_trip),
    }
    if dry_render and healthy:
        import json
        import shutil
        import tempfile
        from pathlib import Path

        from travelogue.render.engine import render_trip

        tmp = Path(tempfile.mkdtemp(prefix="tpl-preview-"))
        trip_path = tmp / "trip.json"
        trip_path.write_text(json.dumps(preview_trip, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            render_trip(
                trip_path,
                out_dir=tmp,
                trip=preview_trip,
                validate=True,
                update_pipeline=False,
                cfg=ctx.cfg,
            )
            index = tmp / "index.html"
            body["rendered"] = index.is_file()
            body["previewBytes"] = index.stat().st_size if index.is_file() else 0
        except Exception as exc:
            body["rendered"] = False
            body["renderError"] = str(exc)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        body["note"] = "传 render=true 触发一次性预览渲染（不落库）"
    handler._json_response(200, body)


