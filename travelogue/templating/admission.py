"""Template admission pipeline (PRD §5.9)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT
from travelogue.services.validate import validate_schema
from travelogue.templates.registry import check_template_health, get_registry
from travelogue.templating.admin_store import get_effective_lifecycle
from travelogue.templating.guardrails import ga_guardrail_errors


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
            import travelogue.render.admission_golden  # noqa: F401 — registers hook
            from travelogue.domain.admission_hooks import run_golden_render_step

            trip_render = json.loads(fixture.read_text(encoding="utf-8"))
            step = run_golden_render_step(template_id, trip_render)
            steps.append(step)
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
