"""Studio trip intent, cohort, template, and copy-intent handlers."""

from __future__ import annotations

import copy

from travelogue.web.studio_errors import client_error_payload
from travelogue.web.studio_handlers.common import load_trip_or_404, studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def handle_patch_intent(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.trip import apply_intent

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    try:
        kwargs: dict = {}
        if "title" in payload:
            kwargs["title"] = payload.get("title")
        if "places" in payload:
            from travelogue.services.copy_subject import is_generic_place

            kwargs["places"] = payload.get("places")
            if "placesUserSet" in payload:
                kwargs["places_user_set"] = bool(payload.get("placesUserSet"))
            else:
                raw_places = payload.get("places") or []
                kwargs["places_user_set"] = bool(
                    raw_places
                    and not all(is_generic_place(str(p)) for p in raw_places)
                )
        if "userNotes" in payload:
            kwargs["user_notes"] = payload.get("userNotes")
        if "travelPlan" in payload:
            kwargs["travel_plan"] = payload.get("travelPlan")
        if "featuredSubjects" in payload:
            kwargs["featured_subjects"] = payload.get("featuredSubjects")
        if not kwargs:
            handler._json_response(400, {"ok": False, "error": "no intent fields"})
            return
        from travelogue.templating.guardrails import validate_edit_payload
        from travelogue.templating.resolver import resolve_effective_template

        fields: dict[str, str] = {}
        if "title" in kwargs:
            fields["meta.title"] = "meta.title"
        if "places" in kwargs:
            fields["meta.places"] = "meta.places"
        gerrs = validate_edit_payload(resolve_effective_template(trip), fields)
        if gerrs:
            handler._json_response(
                403,
                {"ok": False, "error": "E_TEMPLATE_GUARDRAIL", "message": gerrs[0]},
            )
            return
        intent = apply_intent(trip, **kwargs)
        svc.save(trip, trip_json)
    except (ValueError, TypeError) as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    handler._json_response(200, {"ok": True, "intent": intent})


def handle_get_cohort(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.services.cohort import build_cohort_studio_payload

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    _trip_dir, trip = loaded
    ctx = studio_ctx(handler)
    enabled = bool(ctx.app_config.cohort.enabled)
    payload = build_cohort_studio_payload(trip, cohort_enabled=enabled)
    handler._json_response(200, {"ok": True, **payload})


def handle_patch_cohort(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.cohort_faces import apply_cohort_tags
    from travelogue.services.trip import apply_intent

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    svc = ctx.trip_service()
    if not ctx.app_config.cohort.enabled:
        handler._json_response(
            400,
            {"ok": False, "error": "E_COHORT_DISABLED", "message": "cohort.enabled is false in config"},
        )
        return
    try:
        if "featuredSubjects" in payload:
            apply_intent(trip, featured_subjects=payload.get("featuredSubjects"))
        refresh = bool(payload.get("refresh"))
        summary = None
        if refresh or "featuredSubjects" in payload:
            summary = apply_cohort_tags(trip, trip_dir=trip_dir, cfg=ctx.app_config)
            if summary:
                cur = trip.setdefault("curation", {})
                cur["cohort"] = summary
        if "featuredSubjects" not in payload and not refresh:
            handler._json_response(400, {"ok": False, "error": "no cohort fields"})
            return
        svc.save(trip, trip_json)
    except (ValueError, TypeError) as exc:
        handler._json_response(400, client_error_payload(exc))
        return
    from travelogue.services.cohort import build_cohort_studio_payload

    body = build_cohort_studio_payload(trip, cohort_enabled=True)
    body["summary"] = (trip.get("curation") or {}).get("cohort") or summary
    handler._json_response(200, {"ok": True, **body})


def handle_patch_copy_intent(
    handler: StudioHandlerProtocol, trip_id: str, chapter_id: str
) -> None:
    from travelogue.services.decor_line import apply_chapter_copy_intent, validate_copy_intent

    payload = handler._read_json_body()
    if payload is None:
        return
    if not isinstance(payload, dict):
        handler._json_response(400, {"ok": False, "error": "invalid JSON body"})
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    chapters = trip.get("chapters") or []
    chapter = next((ch for ch in chapters if ch.get("id") == chapter_id), None)
    if chapter is None:
        handler._json_response(
            404,
            {"ok": False, "error": "E_CHAPTER_NOT_FOUND", "message": "chapter not found"},
        )
        return
    chapter_index = next(
        (idx for idx, ch in enumerate(chapters) if ch.get("id") == chapter_id),
        None,
    )
    if payload.get("clear"):
        intent_payload: dict | None = {"mood": None, "focus": None, "note": None}
    else:
        intent_payload = {k: payload[k] for k in ("mood", "focus", "note") if k in payload}
        if not intent_payload:
            handler._json_response(400, {"ok": False, "error": "no copyIntent fields"})
            return
    staging = copy.deepcopy(chapter)
    staging_curation = staging.setdefault("curation", {})
    staging_existing = dict(staging_curation.get("copyIntent") or {})
    for key in ("mood", "focus", "note"):
        if intent_payload is None or key not in intent_payload:
            continue
        val = intent_payload[key]
        if val is None or (isinstance(val, str) and not str(val).strip()):
            staging_existing.pop(key, None)
        else:
            staging_existing[key] = str(val).strip()
    if staging_existing:
        staging_curation["copyIntent"] = staging_existing
    else:
        staging_curation.pop("copyIntent", None)
    errs = validate_copy_intent(staging, chapter_index=chapter_index)
    if errs:
        handler._json_response(
            400,
            {"ok": False, "error": "E_COPY_INTENT_INVALID", "message": errs[0]},
        )
        return
    intent = apply_chapter_copy_intent(chapter, intent_payload)
    trip_json = trip_dir / "trip.json"
    studio_ctx(handler).trip_service().save(trip, trip_json)
    handler._json_response(
        200,
        {"ok": True, "chapterId": chapter_id, "copyIntent": intent or None},
    )


def handle_post_cohort_refresh(handler: StudioHandlerProtocol, trip_id: str) -> None:
    from travelogue.curation.cohort_faces import apply_cohort_tags

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    if not ctx.app_config.cohort.enabled:
        handler._json_response(
            400,
            {"ok": False, "error": "E_COHORT_DISABLED", "message": "cohort.enabled is false in config"},
        )
        return
    summary = apply_cohort_tags(trip, trip_dir=trip_dir, cfg=ctx.app_config)
    if summary:
        trip.setdefault("curation", {})["cohort"] = summary
    ctx.trip_service().save(trip, trip_json)
    handler._json_response(200, {"ok": True, "summary": summary})


def handle_patch_template(handler: StudioHandlerProtocol, trip_id: str) -> None:
    """受控调整模板策略（PRD §5.10.2）；锁定态拒绝。"""
    from travelogue.templating.resolver import is_template_locked
    from travelogue.templating.router import apply_template_selection
    from travelogue.templating.summary import build_template_summary

    payload = handler._read_json_body()
    if not payload:
        return
    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip = loaded
    if is_template_locked(trip):
        handler._json_response(
            409,
            {
                "ok": False,
                "error": "E_TEMPLATE_LOCKED",
                "message": "模板已锁定，无法调整",
            },
        )
        return
    mode_raw = str(payload.get("mode") or payload.get("templateMode") or "smart").strip().lower()
    mode = "manual" if mode_raw == "manual" else "smart"
    template_id = payload.get("templateId") or payload.get("template_id")
    template_id_str = str(template_id).strip() if template_id else None
    if mode == "manual" and not template_id_str:
        handler._json_response(400, {"ok": False, "error": "templateId required for manual mode"})
        return
    ctx = studio_ctx(handler)
    selection = apply_template_selection(
        trip,
        mode=mode,  # type: ignore[arg-type]
        requested_template_id=template_id_str,
        cfg=ctx.cfg,
        recompute=True,
        trip_dir=trip_dir,
        log_action="user_adjust",
    )
    trip_json = trip_dir / "trip.json"
    ctx.trip_service().save(trip, trip_json)
    handler._json_response(
        200,
        {"ok": True, "template": build_template_summary(trip), "templateSelection": selection},
    )
