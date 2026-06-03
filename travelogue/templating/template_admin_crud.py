"""Template admin CRUD extensions (P14 · PRD §5.5 / AC-08/15)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT
from travelogue.templates.registry import (
    EVENT_RECAP_TEMPLATE_ID,
    TemplateRegistryError,
    _record_from_dir,
    check_template_health,
    get_registry,
    reset_registry_for_tests,
)
from travelogue.templating.admin_store import append_audit, get_effective_lifecycle


def count_trips_referencing_template(trips_root: Path, template_id: str) -> int:
    if not trips_root.is_dir():
        return 0
    count = 0
    for trip_json in trips_root.glob("*/trip.json"):
        try:
            trip = json.loads(trip_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        sel = trip.get("templateSelection") or {}
        resolved = sel.get("resolvedTemplateId") or trip.get("templateId")
        if str(resolved) == template_id:
            count += 1
    return count


def register_template_from_disk(template_id: str, *, operator: str = "studio") -> dict[str, Any]:
    """Register an on-disk templates/<id> directory into runtime registry."""
    tid = template_id.strip()
    if not tid or "/" in tid or "\\" in tid:
        raise ValueError("invalid templateId")
    tdir = ROOT / "templates" / tid
    if not tdir.is_dir():
        raise TemplateRegistryError(f"missing template directory: {tdir}")
    if tid == EVENT_RECAP_TEMPLATE_ID:
        rec = _record_from_dir(
            tid,
            lifecycle="experimental",
            capabilities=("video", "event", "screens"),
            curation_adapter=EVENT_RECAP_TEMPLATE_ID,
            render_adapter="visual-journal",
            fallback="visual-journal",
            shared_partials_from="visual-journal",
            shared_assets_from="visual-journal",
        )
    else:
        rec = _record_from_dir(
            tid,
            lifecycle="experimental",
            capabilities=("map", "voice", "video", "route", "screens"),
            curation_adapter=tid,
            render_adapter=tid if tid == "visual-journal" else "visual-journal",
        )
    healthy, errs = check_template_health(tid)
    if not healthy:
        raise TemplateRegistryError(f"health check failed: {'; '.join(errs)}")
    get_registry().register(rec)
    append_audit(
        "register",
        operator=operator,
        template_id=tid,
        detail={"version": rec.version, "lifecycle": rec.lifecycle},
    )
    from travelogue.templating.metrics import record_admin_crud

    record_admin_crud(action="register", operator=operator, template_id=tid)
    return {"templateId": tid, "version": rec.version, "healthy": True}


def update_template_metadata(
    template_id: str,
    patch: dict[str, Any],
    *,
    operator: str = "studio",
) -> dict[str, Any]:
    from travelogue.templating.admin_store import _LOCK, _load_unlocked, _save_unlocked
    from travelogue.templating.manifest_meta import CONTROLLED_CATEGORIES, CONTROLLED_TAGS

    allowed_keys = {"displayName", "description", "category", "tags", "bestFor"}
    clean = {k: patch[k] for k in patch if k in allowed_keys}
    if not clean:
        raise ValueError("no metadata fields to update")
    if "category" in clean and str(clean["category"]).lower() not in CONTROLLED_CATEGORIES:
        raise ValueError("invalid category")
    if "tags" in clean and isinstance(clean["tags"], list):
        clean["tags"] = [t for t in clean["tags"] if str(t).lower() in CONTROLLED_TAGS]

    with _LOCK:
        data = _load_unlocked()
        templates = data.setdefault("templates", {})
        row = dict(templates.get(template_id) or {})
        meta = dict(row.get("metadata") or {})
        meta.update(clean)
        row["metadata"] = meta
        from travelogue.templating.admin_store import _utc_now

        row["updatedAt"] = _utc_now()
        row["updatedBy"] = operator
        templates[template_id] = row
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit("metadata_update", operator=operator, template_id=template_id, detail=clean)
    from travelogue.templating.metrics import record_admin_crud

    record_admin_crud(action="metadata_update", operator=operator, template_id=template_id)
    return {"templateId": template_id, "metadata": clean, "revision": data["revision"]}


def logical_delete_template(
    template_id: str,
    *,
    trips_root: Path,
    operator: str = "studio",
    confirm_high_risk: bool = False,
) -> dict[str, Any]:
    """Logical delete → disabled; block if trips still reference template."""
    if not confirm_high_risk:
        raise ValueError("E_TEMPLATE_CONFIRM_REQUIRED")
    refs = count_trips_referencing_template(trips_root, template_id)
    if refs > 0:
        raise ValueError(f"E_TEMPLATE_REFERENCED: {refs} trips still use this template")
    from travelogue.templating.admin_store import get_store_revision, update_template_lifecycle

    reg = get_registry()
    rec = reg.get(template_id)
    current = get_effective_lifecycle(template_id, default=rec.lifecycle)
    out = update_template_lifecycle(
        template_id,
        "disabled",
        current=current,
        expected_revision=get_store_revision(),
        confirm_high_risk=True,
        operator=operator,
    )
    append_audit("logical_delete", operator=operator, template_id=template_id, detail={"refs": refs})
    from travelogue.templating.metrics import record_admin_crud

    record_admin_crud(action="logical_delete", operator=operator, template_id=template_id)
    return {"templateId": template_id, "disabled": True, "revision": out["revision"]}
