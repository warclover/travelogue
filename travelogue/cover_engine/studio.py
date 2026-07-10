"""Studio / preview helpers (API-CSE-09/10)."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.registry import get_default_style_id, get_style, list_assignable_styles, list_styles
from travelogue.cover_engine.resolve import resolve_style_id


def studio_style_options() -> list[dict[str, Any]]:
    """Active styles for Studio layout sheet (id, label, blurb, sort_order)."""
    return [
        {
            "id": r.id,
            "label": r.studio_label or r.label,
            "blurb": r.studio_blurb,
            "sort_order": r.sort_order,
        }
        for r in list_assignable_styles()
    ]


def list_preview_matrix(*, include_draft: bool = False) -> list[dict[str, Any]]:
    statuses = ("active", "draft") if include_draft else ("active",)
    rows: list[dict[str, Any]] = []
    for status in statuses:
        for r in list_styles(status=status):  # type: ignore[arg-type]
            fixture = r.preview_fixtures[0] if r.preview_fixtures else ""
            rows.append(
                {
                    "style_id": r.id,
                    "fixture_ref": fixture,
                    "blurb": r.studio_blurb,
                }
            )
    return rows


def render_preview_context(
    style_id: str,
    asset_ref: str,
    *,
    title: str = "示例书名",
    hook: str = "示例导语",
    place: str = "示例地点",
) -> dict[str, Any]:
    """Assemble a non-persisted preview context for Handlebars / static pages."""
    resolved = resolve_style_id(style_id)
    rec = get_style(resolved)
    return {
        "coverOpeningStyle": resolved,
        "coverAssetRef": asset_ref,
        "title": title,
        "hook": hook,
        "place": place,
        "label": rec.label if rec else resolved,
        "blurb": rec.studio_blurb if rec else "",
        "defaultStyleId": get_default_style_id(),
    }
