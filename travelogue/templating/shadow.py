"""Shadow routing: record smart decision without changing render template (PRD §9.2)."""

from __future__ import annotations

from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.templates.registry import DEFAULT_TEMPLATE_ID


def apply_shadow_overlay(
    selection: dict[str, Any],
    *,
    cfg: AppConfig | None = None,
) -> dict[str, Any]:
    """When shadow_mode enabled, keep render on default but log shadow pick."""
    app = cfg or get_config()
    if not app.template_router.shadow_mode:
        return selection
    if selection.get("mode") == "manual":
        return selection
    shadow_tid = selection.get("resolvedTemplateId")
    default = app.template_router.default_template or DEFAULT_TEMPLATE_ID
    if shadow_tid and shadow_tid != default:
        selection = dict(selection)
        selection["shadowResolvedTemplateId"] = shadow_tid
        selection["resolvedTemplateId"] = default
        selection["shadowActive"] = True
        selection["reasonCodes"] = list(selection.get("reasonCodes") or []) + ["R_SHADOW_RECORD_ONLY"]
    return selection
