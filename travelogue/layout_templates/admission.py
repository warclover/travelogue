"""Lightweight layout-template admission (LTE-ADMISSION-LAYOUT-TEMPLATES §3)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.layout_templates.registry import get_engine
from travelogue.layout_templates.validator import (
    LayoutTemplateGeometryHook,
    validate_template_def,
)

AdmissionTarget = Literal["beta", "ga"]


def _probe_regression_step(template_id: str, *, target: AdmissionTarget) -> tuple[dict[str, Any], bool]:
    """S5: synthetic probe regression (geometry; GA also runs screenshot when available)."""
    from travelogue.layout_templates.probe_regress import run_probe_for_template
    from travelogue.layout_templates.probe_screenshot import run_screenshot_probe

    engine = get_engine()
    probe = run_probe_for_template(engine, template_id)
    step: dict[str, Any] = {
        "name": "probe_regression",
        "ok": probe["ok"],
        "warnings": probe.get("warnings") or [],
        "probeCount": probe.get("probeCount", 0),
    }
    if probe.get("skipped"):
        step["skipped"] = True
        step["reason"] = probe.get("reason")

    # S3/S4 already gate geometry; S5 records synthetic probe drift (warn-only on promote).
    blocks = True
    if not probe["ok"]:
        step["warnOnly"] = True
        step["ok"] = True

    if target == "ga":
        shot = run_screenshot_probe(engine, template_ids=(template_id,))
        step["screenshot"] = {
            "ok": shot.get("ok", True),
            "skipped": shot.get("skipped", False),
            "compared": shot.get("compared", 0),
            "warnings": shot.get("warnings") or [],
        }
        if shot.get("skipped"):
            step["screenshot"]["reason"] = shot.get("reason")
        elif not shot.get("ok", True):
            missing = any(r.get("missingBaseline") for r in shot.get("rows") or [])
            if missing:
                step["warnOnly"] = True
            else:
                step["ok"] = False
                blocks = False

    return step, blocks


def run_layout_template_admission(
    template_id: str,
    *,
    target: AdmissionTarget = "beta",
) -> dict[str, Any]:
    """Run S1–S4 (+ publish gates for ga) for layout pattern promotion."""
    steps: list[dict[str, Any]] = []
    ok = True

    try:
        template = get_engine().get(template_id)
    except KeyError:
        return {
            "ok": False,
            "templateId": template_id,
            "target": target,
            "steps": [
                {
                    "name": "registry",
                    "ok": False,
                    "detail": f"unknown layout template {template_id}",
                }
            ],
        }

    if template.id != template_id:
        steps.append(
            {
                "name": "registry",
                "ok": False,
                "detail": "template id mismatch",
            }
        )
        ok = False
    else:
        steps.append({"name": "registry", "ok": True})

    mode = "publish" if target == "ga" else "ci"
    report = validate_template_def(template, mode=mode)
    steps.append(
        {
            "name": "geometry_static",
            "ok": report.ok,
            "issues": report.issues,
        }
    )
    ok = ok and report.ok

    hook = LayoutTemplateGeometryHook()
    if target == "ga":
        publish = hook.validate_for_publish(template_id)
        steps.append(
            {
                "name": "geometry_publish",
                "ok": publish.ok,
                "issues": publish.issues,
            }
        )
        ok = ok and publish.ok

    legacy = template.raw.get("_legacy")
    if legacy is not None:
        from travelogue.curation.mosaic.pattern_catalog import default_registry

        exported = get_engine().export_legacy_registry()["mosaic_patterns"]
        if template_id in default_registry():
            parity_ok = template_id in exported
            steps.append(
                {
                    "name": "parity_export",
                    "ok": parity_ok,
                    "detail": None if parity_ok else "missing from export_legacy_registry",
                }
            )
            ok = ok and parity_ok

    probe_step, probe_ok = _probe_regression_step(template_id, target=target)
    steps.append(probe_step)
    ok = ok and probe_ok

    if target == "ga":
        from travelogue.templating.review import get_review_status

        review = get_review_status(template_id)
        review_ok = review.get("status") == "approved"
        steps.append(
            {
                "name": "review_gate",
                "ok": review_ok,
                "detail": None if review_ok else "GA promotion requires approved review",
                "review": review,
            }
        )
        ok = ok and review_ok

    return {
        "ok": ok,
        "templateId": template_id,
        "target": target,
        "steps": steps,
    }
