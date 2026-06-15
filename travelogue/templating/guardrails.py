"""Editable guardrails from manifest (PRD §5.8)."""

from __future__ import annotations

import fnmatch
from typing import Any

from travelogue.templates.registry import get_registry
from travelogue.templating.manifest_meta import load_template_meta


def guardrails_for(template_id: str) -> dict[str, Any]:
    rec = get_registry().get(template_id)
    meta = load_template_meta(str(rec.manifest_path))
    return {
        "editableScopes": list(meta.get("editableScopes") or ()),
        "lockedScopes": list(meta.get("lockedScopes") or ()),
        "placeholders": meta.get("placeholders") or {},
    }


def _path_matches(pattern: str, field_path: str) -> bool:
    return fnmatch.fnmatch(field_path, pattern) or fnmatch.fnmatch(field_path, pattern.replace(".*", "*"))


def is_field_editable(template_id: str, field_path: str) -> bool:
    g = guardrails_for(template_id)
    locked = g.get("lockedScopes") or []
    for pat in locked:
        if _path_matches(str(pat), field_path):
            return False
    editable = g.get("editableScopes") or []
    if not editable:
        return False
    return any(_path_matches(str(pat), field_path) for pat in editable)


def copy_path_to_scope(path: str) -> str:
    """Map inline-edit path to guardrail scope pattern."""
    p = str(path or "").strip()
    if p in ("meta.hook", "meta.title", "meta.subtitle", "meta.coverOpeningStyle", "epilogue"):
        return p
    if p.startswith("chapters.") and ".items." in p:
        parts = p.split(".")
        if len(parts) >= 5 and parts[2] == "items":
            field = ".".join(parts[4:])
            return f"chapters.*.items.*.{field}"
    if p.startswith("chapters.") and p.endswith(".lead"):
        return "chapters.*.lead"
    if p.startswith("chapters.") and p.endswith(".decorLine"):
        return "chapters.*.decorLine"
    if p.endswith(".curation.memoryAnchors") and p.startswith("chapters."):
        return "chapters.*.curation.memoryAnchors"
    if p.startswith("assets.") and p.endswith(".caption"):
        return "assets.*.caption"
    if p.startswith("assets.") and p.endswith(".voice.transcript"):
        return "assets.*.voice.transcript"
    if p.startswith("items.") and p.endswith(".caption"):
        return "items.*.caption"
    if p.startswith("items.") and p.endswith(".title"):
        return "items.*.title"
    return p


def enforce_copy_paths(trip: dict, paths: list[str]) -> None:
    """Raise ValueError(E_TEMPLATE_GUARDRAIL) if any path is locked."""
    from travelogue.templating.resolver import resolve_effective_template

    tid = resolve_effective_template(trip)
    blocked: list[str] = []
    for raw in paths:
        scope = copy_path_to_scope(raw)
        if not is_field_editable(tid, scope):
            blocked.append(raw)
    if blocked:
        from travelogue.templating.metrics import record_guardrail_violation

        record_guardrail_violation(template_id=tid, paths=blocked)
        raise ValueError(f"E_TEMPLATE_GUARDRAIL: {blocked[0]}")


def validate_edit_payload(template_id: str, fields: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in fields:
        if not is_field_editable(template_id, key):
            errors.append(f"guardrail: field not editable: {key}")
    if errors:
        from travelogue.templating.metrics import record_guardrail_violation

        record_guardrail_violation(template_id=template_id, paths=[e.split(": ", 1)[-1] for e in errors])
    return errors


def ga_guardrail_errors(
    template_id: str,
    *,
    lifecycle: str,
    manifest_path: str | None = None,
) -> list[str]:
    if lifecycle != "ga":
        return []
    if manifest_path:
        from travelogue.templating.manifest_meta import load_template_meta

        meta = load_template_meta(manifest_path)
        editable = meta.get("editableScopes") or ()
        locked = meta.get("lockedScopes") or ()
    else:
        try:
            g = guardrails_for(template_id)
        except Exception:
            return [f"ga template {template_id} guardrails unavailable"]
        editable = g.get("editableScopes") or ()
        locked = g.get("lockedScopes") or ()
    if not editable or not locked:
        return [f"ga template {template_id} must declare editableScopes and lockedScopes"]
    return []
