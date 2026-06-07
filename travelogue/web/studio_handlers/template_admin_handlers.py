"""Template admin CRUD / lifecycle (Phase 13 · M50-W3)."""

from __future__ import annotations

from travelogue.templates.registry import TemplateRegistryError, get_registry
from travelogue.templating.admin_store import (
    AdminRevisionConflict,
    apply_rollback,
    get_effective_lifecycle,
    get_store_revision,
    list_audit,
    load_runtime,
    update_template_lifecycle,
)
from travelogue.templating.lifecycle import LifecycleTransitionError
from travelogue.templating.roles import require_template_role
from travelogue.web.studio_admin_auth import require_admin_api_access, studio_authenticated
from travelogue.web.studio_errors import client_error_payload, internal_error_payload
from travelogue.web.studio_handlers.common import studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def _auth(
    handler: StudioHandlerProtocol,
    *,
    minimum: str,
) -> bool:
    ctx = studio_ctx(handler)
    if not require_admin_api_access(handler, ctx.cfg):
        return False
    ok, role, code = require_template_role(
        handler.headers,
        host=handler.studio_host,
        allow_lan=handler.studio_allow_lan,
        minimum=minimum,  # type: ignore[arg-type]
        cfg=ctx.cfg,
        studio_authenticated=studio_authenticated(handler),
    )
    if ok:
        return True
    handler._json_response(
        403,
        {
            "ok": False,
            "error": code or "E_TEMPLATE_PERMISSION_DENIED",
            "message": "模板管理权限不足",
            "role": role,
        },
    )
    return False


def _parse_revision(handler: StudioHandlerProtocol) -> int | None:
    raw = handler.headers.get("If-Match") or handler.headers.get("X-Registry-Revision")
    if not raw:
        return None
    try:
        return int(str(raw).strip().strip('"'))
    except ValueError:
        return None


def handle_templates_admin_list(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="viewer"):
        return
    from urllib.parse import parse_qs, urlparse

    from travelogue.templating.discovery import filter_admin_templates
    from travelogue.templating.guardrails import guardrails_for

    query = parse_qs(urlparse(handler.path).query)
    reg = get_registry()
    snap = reg.admin_snapshot()
    rows = list(snap["templates"])
    rows = filter_admin_templates(
        rows,
        lifecycle=(query.get("lifecycle") or [None])[0],
        category=(query.get("category") or [None])[0],
        query=(query.get("q") or query.get("query") or [None])[0],
    )
    from travelogue.templating.admin_store import get_template_admin_row

    for row in rows:
        tid = str(row.get("templateId") or "")
        row["guardrails"] = guardrails_for(tid)
        admin_row = get_template_admin_row(tid)
        meta = admin_row.get("metadata")
        if meta:
            row["adminMetadata"] = meta
        if admin_row.get("review"):
            row["review"] = admin_row["review"]
        from travelogue.templating.review import get_review_status

        row["reviewStatus"] = get_review_status(tid).get("status")

    from travelogue.layout_templates.layout_admin import list_layout_templates_for_admin

    layout_rows = list_layout_templates_for_admin()
    exposure_eval: dict = {}
    try:
        from scripts.phase16_template_eval import evaluate_registry

        exposure_eval = evaluate_registry()
    except Exception:
        exposure_eval = {}
    handler._json_response(
        200,
        {
            "ok": True,
            "revision": snap["revision"],
            "templates": rows,
            "layoutPatterns": layout_rows,
            "exposureDebtProposals": exposure_eval.get("exposureDebtProposals") or [],
            "templateExposureShare": exposure_eval.get("templateExposureShare") or {},
            "templateRegistryVersion": exposure_eval.get("templateRegistryVersion"),
            "runtime": load_runtime(),
            "etag": str(snap["revision"]),
        },
    )


def handle_templates_admin_audit(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="viewer"):
        return
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(handler.path).query)
    try:
        limit = int((query.get("limit") or ["50"])[0])
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))
    handler._json_response(
        200,
        {
            "ok": True,
            "revision": get_store_revision(),
            "audit": list_audit(limit=limit),
        },
    )


def handle_templates_admin_rollback(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    level = str(payload.get("level") or "").strip().upper()
    template_id = str(payload.get("templateId") or "").strip() or None
    confirm = bool(payload.get("confirmHighRisk") or payload.get("confirm_high_risk"))
    try:
        result = apply_rollback(
            level,
            template_id=template_id,
            confirm_high_risk=confirm,
        )
    except ValueError as exc:
        payload = client_error_payload(exc)
        status = 428 if payload.get("error") == "E_TEMPLATE_CONFIRM_REQUIRED" else 400
        handler._json_response(status, payload)
        return
    handler._json_response(200, {"ok": True, **result})


def handle_templates_admin_patch(handler: StudioHandlerProtocol, template_id: str) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    target = str(payload.get("lifecycle") or "").strip().lower()
    if target not in ("experimental", "beta", "ga", "deprecated", "disabled"):
        handler._json_response(400, {"ok": False, "error": "invalid lifecycle"})
        return

    from travelogue.layout_templates.layout_admin import (
        is_layout_template_id,
        run_admission_for_template,
    )

    if is_layout_template_id(template_id):
        from travelogue.layout_templates.registry import get_layout_template

        try:
            tpl = get_layout_template(template_id)
        except Exception:
            handler._json_response(404, {"ok": False, "error": "E_TEMPLATE_NOT_FOUND"})
            return
        admission = run_admission_for_template(template_id, target=target)
        handler._json_response(
            200,
            {
                "ok": True,
                "layoutTemplate": True,
                "message": "Layout template lifecycle is authoritative in YAML (GitOps); edit status in templates/*.yaml.",
                "currentStatus": tpl.status,
                "requestedLifecycle": target,
                "admission": admission,
            },
        )
        return

    confirm = bool(payload.get("confirmHighRisk") or payload.get("confirm_high_risk"))
    expected = _parse_revision(handler)
    if expected is None and payload.get("revision") is not None:
        try:
            expected = int(payload["revision"])
        except (TypeError, ValueError):
            expected = None

    reg = get_registry()
    try:
        rec = reg.get(template_id)
    except TemplateRegistryError:
        handler._json_response(404, {"ok": False, "error": "E_TEMPLATE_NOT_FOUND"})
        return

    current = get_effective_lifecycle(template_id, default=rec.lifecycle)
    if target == "ga":
        from travelogue.templating.review import get_review_status, require_review_approved_for_ga

        try:
            require_review_approved_for_ga(template_id)
        except ValueError as exc:
            if str(exc) == "E_TEMPLATE_REVIEW_REQUIRED":
                handler._json_response(
                    428,
                    {
                        "ok": False,
                        "error": exc.args[0],
                        "message": "晋升 GA 前需完成人工评审（先提交评审并批准）",
                        "review": get_review_status(template_id),
                    },
                )
                return
            raise
    if target in ("beta", "ga"):
        from travelogue.templating.admission import run_admission_check

        admission = run_admission_check(template_id)
        if not admission.get("ok"):
            handler._json_response(
                428,
                {
                    "ok": False,
                    "error": "E_TEMPLATE_ADMISSION_FAILED",
                    "message": "准入检查未通过，不可晋升",
                    "admission": admission,
                },
            )
            return
    try:
        result = update_template_lifecycle(
            template_id,
            target,  # type: ignore[arg-type]
            current=current,
            expected_revision=expected,
            confirm_high_risk=confirm,
        )
    except AdminRevisionConflict:
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_TEMPLATE_REVISION_CONFLICT",
                "message": "配置已被他人更新，请刷新后重试",
                "revision": get_store_revision(),
            },
        )
        return
    except LifecycleTransitionError as exc:
        handler._json_response(
            400,
            client_error_payload(exc, default_code="E_TEMPLATE_LIFECYCLE"),
        )
        return
    except ValueError as exc:
        code = str(exc)
        if code == "E_TEMPLATE_CONFIRM_REQUIRED":
            handler._json_response(
                428,
                {
                    "ok": False,
                    "error": code,
                    "message": "下线/退役操作需二次确认（confirmHighRisk=true）",
                },
            )
            return
        handler._json_response(400, {"ok": False, "error": code})
        return

    from travelogue.templating.admission import run_admission_check

    admission = run_admission_check(template_id) if target in ("beta", "ga") else None
    handler._json_response(
        200,
        {
            "ok": True,
            "templateId": template_id,
            "lifecycle": target,
            "revision": result["revision"],
            "etag": str(result["revision"]),
            "admission": admission,
        },
    )


def handle_templates_admin_review(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    from travelogue.templating.review import (
        approve_review,
        get_review_status,
        reject_review,
        submit_for_review,
    )

    payload = handler._read_json_body() or {}
    template_id = str(payload.get("templateId") or "").strip()
    action = str(payload.get("action") or "submit").strip().lower()
    if not template_id:
        handler._json_response(400, {"ok": False, "error": "templateId required"})
        return
    operator = str(payload.get("operator") or "studio")
    try:
        if action == "submit":
            out = submit_for_review(template_id, operator=operator)
        elif action == "approve":
            if not _auth(handler, minimum="template_admin"):
                return
            out = approve_review(template_id, reviewer=operator, note=str(payload.get("note") or ""))
        elif action == "reject":
            if not _auth(handler, minimum="template_admin"):
                return
            out = reject_review(template_id, reviewer=operator, reason=str(payload.get("note") or ""))
        elif action == "status":
            out = get_review_status(template_id)
        else:
            handler._json_response(400, {"ok": False, "error": "unknown action"})
            return
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    handler._json_response(200, {"ok": True, "review": out})


def handle_templates_admin_register(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    template_id = str(payload.get("templateId") or "").strip()
    if not template_id:
        handler._json_response(400, {"ok": False, "error": "templateId required"})
        return
    try:
        from travelogue.templating.template_admin_crud import register_template_from_disk

        out = register_template_from_disk(template_id, operator="studio")
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    except Exception:
        import logging

        logging.getLogger(__name__).exception("template register failed: %s", template_id)
        handler._json_response(500, internal_error_payload())
        return
    handler._json_response(201, {"ok": True, **out})


def handle_templates_admin_delete(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    template_id = str(payload.get("templateId") or "").strip()
    if not template_id:
        handler._json_response(400, {"ok": False, "error": "templateId required"})
        return
    ctx = studio_ctx(handler)
    try:
        from travelogue.templating.template_admin_crud import logical_delete_template

        out = logical_delete_template(
            template_id,
            trips_root=ctx.trips_root,
            confirm_high_risk=bool(payload.get("confirmHighRisk")),
        )
    except ValueError as exc:
        payload = client_error_payload(exc)
        code = str(payload.get("error") or "")
        status = (
            428
            if code == "E_TEMPLATE_CONFIRM_REQUIRED"
            else 409
            if code.startswith("E_TEMPLATE_REFERENCED")
            else 400
        )
        handler._json_response(status, payload)
        return
    handler._json_response(200, {"ok": True, **out})


def handle_templates_admin_metadata(handler: StudioHandlerProtocol, template_id: str) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    try:
        from travelogue.templating.template_admin_crud import update_template_metadata

        out = update_template_metadata(template_id, payload, operator="studio")
    except ValueError as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    handler._json_response(200, {"ok": True, **out})


def handle_templates_admin_dashboard(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="viewer"):
        return
    from urllib.parse import parse_qs, urlparse

    from travelogue.templating.metrics import aggregate_metrics

    query = parse_qs(urlparse(handler.path).query)
    try:
        hours = int((query.get("hours") or ["24"])[0])
    except ValueError:
        hours = 24
    handler._json_response(
        200,
        {"ok": True, "metrics": aggregate_metrics(window_hours=hours), "runtime": load_runtime()},
    )


def handle_templates_admin_admission(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    payload = handler._read_json_body() or {}
    from travelogue.layout_templates.layout_admin import (
        is_layout_template_id,
        layout_template_promotion_plan,
        run_admission_for_template,
    )
    template_id = str(payload.get("templateId") or "").strip()
    if not template_id:
        handler._json_response(400, {"ok": False, "error": "templateId required"})
        return
    target = str(payload.get("target") or "beta").strip().lower()
    if target not in ("beta", "ga"):
        target = "beta"
    report = run_admission_for_template(template_id, target=target)
    if is_layout_template_id(template_id):
        plan = layout_template_promotion_plan(template_id, target=target)
        handler._json_response(200, {"ok": True, **report, "promotionPlan": plan})
        return
    handler._json_response(200, {"ok": True, **report})


def handle_templates_admin_decisions(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="viewer"):
        return
    from urllib.parse import parse_qs, urlparse

    from travelogue.templating.decision_log import list_decisions, list_recent_decisions

    ctx = studio_ctx(handler)
    query = parse_qs(urlparse(handler.path).query)
    trip_id = (query.get("tripId") or [""])[0].strip()
    try:
        limit = int((query.get("limit") or ["30"])[0])
    except ValueError:
        limit = 30
    if trip_id:
        from travelogue.web.studio_handlers.common import resolve_trip_dir_listed

        trip_dir = resolve_trip_dir_listed(ctx, trip_id)
        if trip_dir is None:
            handler._json_response(404, {"ok": False, "error": "E_TRIP_NOT_FOUND"})
            return
        decisions = list_decisions(trip_dir, limit=limit)
    else:
        decisions = list_recent_decisions(ctx.trips_root, limit=limit)
    handler._json_response(200, {"ok": True, "decisions": decisions})


def handle_templates_admin_runtime(handler: StudioHandlerProtocol) -> None:
    if not _auth(handler, minimum="template_admin"):
        return
    payload = handler._read_json_body() or {}
    from travelogue.layout_templates.layout_admin import (
        is_layout_template_id,
        layout_template_promotion_plan,
    )
    from travelogue.templating.config_governance import (
        approve_router_change,
        propose_layout_weight_changes,
        propose_router_change,
    )

    if payload.get("action") == "approve":
        change_id = str(payload.get("changeId") or "").strip()
        approver = str(payload.get("approver") or "studio")
        try:
            out = approve_router_change(change_id, approver=approver)
        except ValueError as exc:
            handler._json_response(400, client_error_payload(exc))
            return
        handler._json_response(200, {"ok": True, "change": out, "runtime": load_runtime()})
        return
    if payload.get("action") == "promote_layout_template":
        template_id = str(payload.get("templateId") or "").strip()
        if not template_id:
            handler._json_response(400, {"ok": False, "error": "templateId required"})
            return
        if not is_layout_template_id(template_id):
            handler._json_response(400, {"ok": False, "error": "E_NOT_LAYOUT_TEMPLATE"})
            return
        target = str(payload.get("target") or "beta").strip().lower()
        if target not in ("beta", "ga"):
            target = "beta"
        if target == "ga":
            from travelogue.templating.review import get_review_status, require_review_approved_for_ga

            try:
                require_review_approved_for_ga(template_id)
            except ValueError as exc:
                if str(exc) == "E_TEMPLATE_REVIEW_REQUIRED":
                    handler._json_response(
                        428,
                        {
                            "ok": False,
                            "error": exc.args[0],
                            "message": "布局模板晋升 GA 前需完成人工评审（先 submit_for_review 并 approve）",
                            "review": get_review_status(template_id),
                        },
                    )
                    return
                raise
        plan = layout_template_promotion_plan(template_id, target=target)
        if not plan["canPromote"]:
            handler._json_response(400, {"ok": False, "promotionPlan": plan, "error": "E_ADMISSION_FAILED"})
            return
        applied = None
        if payload.get("apply"):
            from travelogue.layout_templates.promotion import apply_layout_template_yaml_patch

            dry_run = bool(payload.get("dryRun"))
            try:
                applied = apply_layout_template_yaml_patch(
                    template_id,
                    plan["yamlPatch"],
                    dry_run=dry_run,
                )
            except (OSError, ValueError) as exc:
                handler._json_response(400, {"ok": False, "error": str(exc)})
                return
        handler._json_response(200, {"ok": True, "promotionPlan": plan, "applied": applied})
        return
    if payload.get("action") == "propose_exposure_weights":
        proposals = payload.get("proposals") or []
        if not isinstance(proposals, list) or not proposals:
            handler._json_response(400, {"ok": False, "error": "proposals array required"})
            return
        try:
            req = propose_layout_weight_changes(
                proposals,
                operator=str(payload.get("operator") or "studio"),
                reason=str(payload.get("reason") or "exposure debt rebalance"),
                template_registry_version=str(payload.get("templateRegistryVersion") or "").strip() or None,
            )
        except ValueError as exc:
            handler._json_response(400, client_error_payload(exc))
            return
        handler._json_response(202, {"ok": True, "pending": req, "message": "需第二名审批人 approve"})
        return
    patch = payload.get("patch") or payload
    if not isinstance(patch, dict):
        handler._json_response(400, {"ok": False, "error": "patch object required"})
        return
    req = propose_router_change(patch, operator=str(payload.get("operator") or "studio"), reason=str(payload.get("reason") or ""))
    handler._json_response(202, {"ok": True, "pending": req, "message": "需第二名审批人 approve"})


def handle_templates_admin_version_diff(handler: StudioHandlerProtocol, template_id: str) -> None:
    if not _auth(handler, minimum="template_operator"):
        return
    from urllib.parse import parse_qs, urlparse

    from travelogue.layout_templates.layout_admin import (
        is_layout_template_id,
        layout_template_geometry_detail,
    )

    query = parse_qs(urlparse(handler.path).query)
    va_raw = (query.get("va") or query.get("fromVersion") or [None])[0]
    vb_raw = (query.get("vb") or query.get("toVersion") or [None])[0]

    if is_layout_template_id(template_id):
        from travelogue.layout_templates.registry import get_engine

        current_version = get_engine().get(template_id).version
        va = int(va_raw) if va_raw is not None else max(1, current_version - 1)
        vb = int(vb_raw) if vb_raw is not None else current_version
        detail = layout_template_geometry_detail(template_id)
        hook_diff = None
        if va != vb:
            from travelogue.layout_templates.validator import LayoutTemplateGeometryHook

            hook_diff = LayoutTemplateGeometryHook().geometry_diff(template_id, va, vb)
        handler._json_response(
            200,
            {
                "ok": True,
                "templateId": template_id,
                "registryKind": "layout_pattern",
                "geometry": detail,
                "va": va,
                "vb": vb,
                "geometryDiff": hook_diff,
            },
        )
        return
    reg = get_registry()
    try:
        rec = reg.get(template_id)
    except TemplateRegistryError:
        handler._json_response(404, {"ok": False, "error": "E_TEMPLATE_NOT_FOUND"})
        return
    from travelogue.templating.admin_store import get_template_admin_row

    row = get_template_admin_row(template_id)
    handler._json_response(
        200,
        {
            "ok": True,
            "templateId": template_id,
            "registryVersion": rec.version,
            "registryRevision": rec.revision,
            "adminRow": row,
            "diff": {
                "lifecycle": {"registry": rec.lifecycle, "admin": row.get("lifecycle")},
                "updatedAt": row.get("updatedAt"),
                "updatedBy": row.get("updatedBy"),
            },
        },
    )
