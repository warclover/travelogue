"""Template admission pipeline (PRD §5.9)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT
from travelogue.services.validate import validate_schema
from travelogue.templates.registry import check_template_health, get_registry
from travelogue.templating.guardrails import ga_guardrail_errors
from travelogue.templating.admin_store import get_effective_lifecycle


def run_admission_check(
    template_id: str,
    *,
    golden_trip: Path | None = None,
) -> dict[str, Any]:
    """Static + health + optional golden trip schema/manifest regression."""
    steps: list[dict[str, Any]] = []
    reg = get_registry()
    try:
        rec = reg.get(template_id)
    except Exception as exc:
        return {"ok": False, "templateId": template_id, "steps": [{"name": "registry", "pass": False, "detail": str(exc)}]}

    healthy, errs = check_template_health(template_id)
    steps.append({"name": "health", "pass": healthy, "errors": errs})

    lc = get_effective_lifecycle(template_id, default=rec.lifecycle)
    gerrs = ga_guardrail_errors(template_id, lifecycle=lc)
    steps.append({"name": "guardrails_ga", "pass": len(gerrs) == 0, "errors": gerrs})

    if rec.manifest_path.is_file():
        try:
            json.loads(rec.manifest_path.read_text(encoding="utf-8"))
            steps.append({"name": "manifest_json", "pass": True})
        except (OSError, json.JSONDecodeError) as exc:
            steps.append({"name": "manifest_json", "pass": False, "detail": str(exc)})
    else:
        steps.append({"name": "manifest_json", "pass": False, "detail": "missing manifest"})

    fixture = golden_trip or (ROOT / "schemas" / "fixtures" / "trip.render_golden.json")
    if fixture.is_file():
        try:
            trip = json.loads(fixture.read_text(encoding="utf-8"))
            trip["templateId"] = template_id
            sel = trip.setdefault("templateSelection", {})
            sel["resolvedTemplateId"] = template_id
            schema_errs = validate_schema(trip)
            steps.append(
                {
                    "name": "golden_schema",
                    "pass": len(schema_errs) == 0,
                    "errors": schema_errs[:5],
                }
            )
        except (OSError, json.JSONDecodeError) as exc:
            steps.append({"name": "golden_schema", "pass": False, "detail": str(exc)})
    else:
        steps.append({"name": "golden_schema", "pass": True, "skipped": True})

    if fixture.is_file():
        try:
            from travelogue.render.dual_layout_regression import prepare_trip_web_screens
            from travelogue.render.engine import render_html

            trip_render = json.loads(fixture.read_text(encoding="utf-8"))
            trip_render = prepare_trip_web_screens(trip_render)
            sel = trip_render.setdefault("templateSelection", {})
            sel["resolvedTemplateId"] = template_id
            trip_render["templateId"] = template_id
            html = render_html(
                trip_render,
                template_id=template_id,
                layout_engine_override="screens",
                export_layout_override="web",
            )
            steps.append(
                {
                    "name": "golden_render",
                    "pass": isinstance(html, str) and len(html) > 200,
                    "htmlBytes": len(html) if isinstance(html, str) else 0,
                }
            )
        except Exception as exc:
            steps.append({"name": "golden_render", "pass": False, "detail": str(exc)})
    else:
        steps.append({"name": "golden_render", "pass": True, "skipped": True})

    ok = all(s.get("pass") for s in steps)
    return {
        "ok": ok,
        "templateId": template_id,
        "lifecycle": lc,
        "steps": steps,
        "readyFor": "experimental" if ok else None,
    }
