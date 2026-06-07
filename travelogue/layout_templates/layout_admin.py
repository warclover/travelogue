"""Layout template admin helpers for Studio (R-P16-12 · W3)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_templates.admission import run_layout_template_admission
from travelogue.layout_templates.promotion import validate_lifecycle_transition
from travelogue.layout_templates.registry import get_engine
from travelogue.layout_templates.validator import LayoutTemplateGeometryHook


def is_layout_template_id(template_id: str) -> bool:
    try:
        get_engine().get(template_id)
        return True
    except KeyError:
        return False


def layout_template_admin_row(template_id: str, *, exposure_shares: dict[str, float] | None = None) -> dict[str, Any]:
    """Admin list row for one LTE YAML template."""
    template = get_engine().get(template_id)
    hook = LayoutTemplateGeometryHook()
    aspects = hook.slot_aspect_table(template_id)
    shares = exposure_shares if exposure_shares is not None else {}
    return {
        "templateId": template.id,
        "registryKind": "layout_pattern",
        "category": "layout",
        "lifecycle": template.status,
        "version": template.version,
        "displayName": template.display_name,
        "kind": template.kind,
        "photoCount": {
            "min": template.photo_count_min,
            "max": template.photo_count_max,
        },
        "gridClass": template.render_grid_class,
        "stageAspect": template.stage.aspect,
        "stageCols": list(template.stage.cols or ()),
        "stageRows": list(template.stage.rows or ()),
        "exposureShare": shares.get(template.id, 0.0),
        "slotAspects": [
            {
                "index": row.index,
                "role": row.role,
                "displayAspect": round(row.display_aspect, 4),
            }
            for row in aspects
        ],
        "scoring": template.scoring,
    }


def list_layout_templates_for_admin(*, active_only: bool = False) -> list[dict[str, Any]]:
    from travelogue.curation.layout_metrics import template_exposure_shares_from_trips

    engine = get_engine()
    shares = template_exposure_shares_from_trips()
    if active_only:
        return [layout_template_admin_row(t.id, exposure_shares=shares) for t in engine.list_active()]
    return [
        layout_template_admin_row(tid, exposure_shares=shares) for tid in sorted(engine._templates)
    ]


def layout_template_geometry_detail(template_id: str) -> dict[str, Any]:
    """Extended geometry payload for Studio detail / probe panels."""
    template = get_engine().get(template_id)
    hook = LayoutTemplateGeometryHook()
    from travelogue.layout_templates.css_gen import grid_templates_for

    cols, rows = grid_templates_for(template)
    return {
        "templateId": template.id,
        "registryKind": "layout_pattern",
        "displayName": template.display_name,
        "lifecycle": template.status,
        "version": template.version,
        "stage": {
            "aspect": template.stage.aspect,
            "cols": list(template.stage.cols or ()),
            "rows": list(template.stage.rows or ()),
            "grid": list(template.stage.grid or ()),
        },
        "slots": [
            {
                "index": s.index,
                "rect": list(s.rect),
                "role": s.role,
                "fit": s.fit,
            }
            for s in template.slots
        ],
        "render": {
            "gridClass": template.render_grid_class,
            "cssBundle": template.render_css_bundle,
            "gridTemplateColumns": cols,
            "gridTemplateRows": rows,
        },
        "slotAspects": layout_template_admin_row(template_id)["slotAspects"],
        "admissionBeta": run_layout_template_admission(template_id, target="beta"),
    }


def run_admission_for_template(
    template_id: str,
    *,
    target: str = "beta",
) -> dict[str, Any]:
    if is_layout_template_id(template_id):
        return run_layout_template_admission(template_id, target=target)  # type: ignore[arg-type]
    from travelogue.templating.admission import run_admission_check

    return run_admission_check(template_id)


def layout_template_promotion_plan(
    template_id: str,
    *,
    target: str = "beta",
) -> dict[str, Any]:
    """Admission gates + GitOps YAML patch hint for experimental→beta→ga (AC-P16-09)."""
    template = get_engine().get(template_id)
    transition_err = validate_lifecycle_transition(template.status, target)
    admission = run_layout_template_admission(template_id, target=target)  # type: ignore[arg-type]
    next_version = template.version + 1 if target != template.status else template.version
    yaml_path = f"travelogue/layout_templates/templates/{template_id}.yaml"
    review_status = None
    review_required = target == "ga"
    if review_required:
        from travelogue.templating.review import get_review_status

        review_status = get_review_status(template_id)
    can_promote = bool(admission.get("ok")) and transition_err is None
    if review_required and (review_status or {}).get("status") != "approved":
        can_promote = False
    return {
        "templateId": template_id,
        "currentStatus": template.status,
        "currentVersion": template.version,
        "targetStatus": target,
        "transitionError": transition_err,
        "admission": admission,
        "reviewStatus": review_status,
        "reviewRequired": review_required,
        "canPromote": can_promote,
        "yamlPath": yaml_path,
        "yamlPatch": {
            "status": target,
            "version": next_version,
        },
        "gitOpsNote": "Edit YAML status/version and run validate + export --sync-journal before merge.",
        "workflow": [
            "experimental → submit_for_review → beta (admission S1–S3)",
            "beta → approve_review → ga (admission + review_gate S7)",
        ],
    }
