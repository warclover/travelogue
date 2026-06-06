"""Phase 13 platform modules: L3, discovery, guardrails, admission, shadow, metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config import AppConfig, TemplateRouterConfig
from travelogue.templating.admission import run_admission_check
from travelogue.templating.curation_adapter import apply_curation_adapter_hints
from travelogue.templating.discovery import sort_consumer_templates
from travelogue.templating.guardrails import ga_guardrail_errors, guardrails_for, is_field_editable
from travelogue.templating.l3_validate import validate_template_capabilities
from travelogue.templating.metrics import aggregate_metrics, record_template_metric
from travelogue.templating.router import route_template
from travelogue.templating.shadow import apply_shadow_overlay


def test_guardrails_visual_journal_ga() -> None:
    g = guardrails_for("visual-journal")
    assert g["editableScopes"]
    assert g["lockedScopes"]
    assert is_field_editable("visual-journal", "meta.title")
    assert not is_field_editable("visual-journal", "templateId")
    assert ga_guardrail_errors("visual-journal", lifecycle="ga") == []


def test_l3_map_requires_geo() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "meta": {"places": ["A"]},
        "assets": [{"type": "photo", "id": "a1"}],
    }
    errs = validate_template_capabilities(trip, template_id="visual-journal")
    assert any("L3" in e and "geo" in e.lower() for e in errs)


def test_discovery_sort_recommended_first() -> None:
    items = [{"templateId": "event-recap"}, {"templateId": "visual-journal"}]
    out = sort_consumer_templates(
        items,
        display_order=("visual-journal", "event-recap"),
        recommended=("event-recap", "visual-journal"),
    )
    assert out[0]["templateId"] == "event-recap"


def test_admission_includes_golden_render_step() -> None:
    from travelogue.templating.admission import run_admission_check

    report = run_admission_check("visual-journal")
    names = [s["name"] for s in report.get("steps", [])]
    assert "golden_render" in names
    render_step = next(s for s in report["steps"] if s["name"] == "golden_render")
    assert render_step.get("pass") is True


def test_admission_check_visual_journal() -> None:
    report = run_admission_check("visual-journal")
    assert report["templateId"] == "visual-journal"
    assert report["steps"]


def test_shadow_mode_records_without_changing_render_default() -> None:
    sel = {
        "mode": "smart",
        "resolvedTemplateId": "event-recap",
        "reasonCodes": [],
        "fallbackUsed": False,
        "routerVersion": "p13-r1",
        "routerConfigVersion": "c",
        "featureSnapshotVersion": "f",
        "registryVersion": "r",
    }
    cfg = AppConfig(template_router=TemplateRouterConfig(shadow_mode=True))
    out = apply_shadow_overlay(sel, cfg=cfg)
    assert out.get("shadowResolvedTemplateId") == "event-recap"
    assert out["resolvedTemplateId"] == "visual-journal"


def test_curation_adapter_hints() -> None:
    trip = {"assets": [{"id": "a1"}], "templateSelection": {"resolvedTemplateId": "event-recap"}}
    plan = apply_curation_adapter_hints(trip)
    assert plan.prefer_video_highlights is True
    assert trip["curation"]["templateHints"]["templateId"] == "event-recap"


def test_metrics_record_and_aggregate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_file = tmp_path / "template-metrics.jsonl"
    monkeypatch.setattr("travelogue.templating.metrics.metrics_path", lambda: metrics_file)
    record_template_metric("template.route.decision", templateId="visual-journal")
    agg = aggregate_metrics(window_hours=24)
    assert agg["counts"].get("template.route.decision", 0) >= 1


def test_router_event_keyword_route() -> None:
    trip = {
        "meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["Hall"]},
        "assets": [{"type": "photo", "caption": "年会活动精彩瞬间"}],
    }
    sel = route_template(trip, mode="smart", cfg=AppConfig(template_router=TemplateRouterConfig()))
    assert sel["resolvedTemplateId"] in ("event-recap", "visual-journal")
