"""Phase 13 concurrent / conflict scenarios (PRD §13.2 · G5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.config import AppConfig, TemplateRouterConfig
from travelogue.services.trip_factory import create_trip
from travelogue.templating.admin_store import (
    AdminRevisionConflict,
    get_store_revision,
    update_template_lifecycle,
)
from travelogue.templating.router import apply_template_selection, route_template
from travelogue.templates.registry import get_registry


def _cfg(**kwargs) -> AppConfig:
    tr = TemplateRouterConfig(**kwargs)
    return AppConfig(template_router=tr)


def test_concurrent_manual_disabled_template_falls_back(tmp_path: Path) -> None:
    """C1: manual 指定不可用模板时回退默认。"""
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["A"]}}
    sel = route_template(
        trip,
        mode="manual",
        requested_template_id="event-recap",
        cfg=_cfg(allowed_templates=("visual-journal",)),
    )
    assert sel["resolvedTemplateId"] == "visual-journal"
    assert sel.get("fallbackUsed") is True


def test_concurrent_admin_revision_conflict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """C2: 双 Admin revision 冲突 → AdminRevisionConflict。"""
    state = tmp_path / "template_admin_state.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"revision": 3, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)

    reg = get_registry()
    rec = reg.get("visual-journal")
    with pytest.raises(AdminRevisionConflict):
        update_template_lifecycle(
            "visual-journal",
            "beta",
            current=rec.lifecycle,
            expected_revision=2,
            operator="test",
        )


def test_concurrent_copy_locked_blocks_recompute() -> None:
    """C6: copy_locked + recompute → 保留原 hash。"""
    trip = {
        "templateSelection": {
            "mode": "smart",
            "resolvedTemplateId": "visual-journal",
            "decisionHash": "sha256:locked",
        },
        "pipeline": {"locks": {"copy": True}},
    }
    out = apply_template_selection(trip, mode="smart", recompute=True)
    assert out["decisionHash"] == "sha256:locked"


def test_concurrent_beta_not_in_allowlist(tmp_path: Path) -> None:
    """C7: 非白名单 smart 不命中 beta-only 路由。"""
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip(
        "trip-no-beta",
        trips,
        cfg=_cfg(
            beta_allowlist_trip_ids=("other-trip",),
            allowed_templates=("visual-journal", "event-recap"),
        ),
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assert trip["templateSelection"]["resolvedTemplateId"] == "visual-journal"


def test_concurrent_unhealthy_template_excluded_from_consumer(monkeypatch: pytest.MonkeyPatch) -> None:
    """C3: health 未通过的模板不参与 consumer 列表与路由。"""
    from travelogue.templates.registry import get_registry

    monkeypatch.setattr(
        "travelogue.templates.registry.check_template_health",
        lambda tid, registry=None: (tid != "event-recap", [] if tid != "event-recap" else ["broken"]),
    )
    ids = [r.template_id for r in get_registry().list_for_consumer(include_beta=True)]
    assert "event-recap" not in ids

    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-02", "places": ["X"]}}
    sel = route_template(
        trip,
        mode="smart",
        cfg=_cfg(allowed_templates=("visual-journal", "event-recap")),
    )
    assert sel["resolvedTemplateId"] == "visual-journal"


def test_concurrent_router_disabled_all_default() -> None:
    """C5: 全局关闭路由器时 smart 一律默认模板。"""
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-05", "places": ["A", "B"]}}
    sel = route_template(trip, mode="smart", cfg=_cfg(enabled=False))
    assert sel["resolvedTemplateId"] == "visual-journal"
    assert sel.get("mode") == "fallback" or sel.get("fallbackUsed") is True


def test_concurrent_render_stable_registry_while_manifest_disk_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C4: 渲染编译使用 registry template_dir；manifest 磁盘损坏不阻断（健康检查快照）。"""
    import json

    from travelogue.paths import FIXTURES_DIR
    from travelogue.render.dual_layout_regression import prepare_trip_web_screens
    from travelogue.render.engine import render_html
    from travelogue.templates.registry import get_registry

    reg = get_registry()
    rec = reg.get("visual-journal")
    manifest = rec.manifest_path
    original = manifest.read_text(encoding="utf-8")
    trip = json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    trip = prepare_trip_web_screens(trip)
    trip.setdefault("templateSelection", {})["resolvedTemplateId"] = "visual-journal"

    monkeypatch.setattr(
        "travelogue.render.engine.check_template_health",
        lambda tid, registry=None: (True, []),
    )
    try:
        manifest.write_text('{"invalid": true}', encoding="utf-8")
        html = render_html(
            trip,
            template_id="visual-journal",
            layout_engine_override="screens",
            export_layout_override="web",
        )
        assert len(html) > 200
        assert rec.template_dir.is_dir()
    finally:
        manifest.write_text(original, encoding="utf-8")


def test_admin_store_revision_monotonic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "runs" / "template_admin_state.json"
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    reg = get_registry()
    rec = reg.get("visual-journal")
    rev = get_store_revision()
    out = update_template_lifecycle(
        "visual-journal",
        "beta",
        current=rec.lifecycle,
        expected_revision=rev,
        operator="test",
    )
    assert out["revision"] == rev + 1
