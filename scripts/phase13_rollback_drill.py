#!/usr/bin/env python3
"""Phase 13 rollback drill (R1–R6) — dev/staging evidence for release gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_drills(*, state_path: Path | None = None) -> dict[str, Any]:
    from travelogue.templating import admin_store
    from travelogue.templating.router import route_template
    from travelogue.templates.registry import EVENT_RECAP_TEMPLATE_ID, bootstrap_registry, get_registry
    from travelogue.templating.lifecycle import LifecycleTransitionError
    from travelogue.templating.admin_store import (
        AdminRevisionConflict,
        apply_rollback,
        get_effective_lifecycle,
        get_store_revision,
        update_template_lifecycle,
    )

    if state_path:
        admin_store._STATE_PATH = state_path  # type: ignore[attr-defined]
        state_path.parent.mkdir(parents=True, exist_ok=True)

    drills: list[dict[str, Any]] = []

    # R1 — L1
    try:
        apply_rollback("L1", confirm_high_risk=True, operator="drill")
        trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["A"]}}
        sel = route_template(trip, mode="smart")
        r1_ok = sel["resolvedTemplateId"] == "visual-journal" and sel.get("fallbackUsed") is True
        drills.append(
            {
                "id": "R1",
                "name": "L1 关闭路由器",
                "automated": True,
                "pass": r1_ok,
                "evidence": {"resolvedTemplateId": sel["resolvedTemplateId"], "fallbackUsed": sel.get("fallbackUsed")},
            }
        )
        with admin_store._LOCK:
            data = admin_store._load_unlocked()
            rt = dict(data.get("runtime") or {})
            rt["template_router_enabled"] = True
            data["runtime"] = rt
            admin_store._save_unlocked(data)
    except Exception as exc:
        drills.append({"id": "R1", "name": "L1 关闭路由器", "automated": True, "pass": False, "error": str(exc)})

    # R2 — L2 disable event-recap
    try:
        reg = get_registry()
        rec = reg.get(EVENT_RECAP_TEMPLATE_ID)
        current = get_effective_lifecycle(EVENT_RECAP_TEMPLATE_ID, default=rec.lifecycle)
        if current != "disabled":
            rev = get_store_revision()
            update_template_lifecycle(
                EVENT_RECAP_TEMPLATE_ID,
                "disabled",
                current=current,
                expected_revision=rev,
                confirm_high_risk=True,
                operator="drill",
            )
        visible = [t.template_id for t in reg.list_for_consumer(include_beta=True)]
        r2_ok = EVENT_RECAP_TEMPLATE_ID not in visible
        drills.append(
            {
                "id": "R2",
                "name": "L2 单模板下线",
                "automated": True,
                "pass": r2_ok,
                "evidence": {"consumerTemplates": visible},
            }
        )
    except (LifecycleTransitionError, AdminRevisionConflict, ValueError) as exc:
        drills.append({"id": "R2", "name": "L2 单模板下线", "automated": True, "pass": False, "error": str(exc)})

    # R3 — L3
    try:
        apply_rollback("L3", confirm_high_risk=True, operator="drill")
        rt = admin_store.load_runtime()
        r3_ok = rt.get("template_router_enabled") is False and rt.get("allowed_templates") == ["visual-journal"]
        drills.append(
            {
                "id": "R3",
                "name": "L3 平台应急",
                "automated": True,
                "pass": r3_ok,
                "evidence": rt,
            }
        )
    except Exception as exc:
        drills.append({"id": "R3", "name": "L3 平台应急", "automated": True, "pass": False, "error": str(exc)})

    # R4 — simulated threshold (dev: inject metrics + check)
    try:
        from travelogue.templating.metrics import aggregate_metrics, record_template_metric

        for _ in range(25):
            record_template_metric("template.route.fallback", templateId="event-recap")
        for _ in range(5):
            record_template_metric("template.route.decision", templateId="visual-journal", mode="smart")
        agg = aggregate_metrics(window_hours=1)
        fb_rate = float((agg.get("rates") or {}).get("fallback_rate") or 0)
        r4_ok = fb_rate > 0.2
        drills.append(
            {
                "id": "R4",
                "name": "自动回滚触发模拟",
                "automated": True,
                "pass": r4_ok,
                "evidence": {"fallback_rate_1h": fb_rate, "threshold": 0.2},
                "note": "开发环境注入 metrics；生产由监控告警触发 L1",
            }
        )
    except Exception as exc:
        drills.append({"id": "R4", "name": "自动回滚触发模拟", "automated": True, "pass": False, "error": str(exc)})

    # R5 — high risk confirm
    try:
        try:
            apply_rollback("L2", template_id="visual-journal", confirm_high_risk=False)
            r5_ok = False
        except ValueError as exc:
            r5_ok = str(exc) == "E_TEMPLATE_CONFIRM_REQUIRED"
        drills.append(
            {
                "id": "R5",
                "name": "高风险未确认拦截",
                "automated": True,
                "pass": r5_ok,
            }
        )
    except Exception as exc:
        drills.append({"id": "R5", "name": "高风险未确认拦截", "automated": True, "pass": False, "error": str(exc)})

    # R6 — replay match (fixture)
    try:
        fixture = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "phase13_template_route_eval",
            ROOT / "scripts" / "phase13_template_route_eval.py",
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        ev = mod.build_eval(
            trip_json_path=fixture,
            trips_dir=ROOT / "trips",
            seed_template_selection=True,
        )
        r6_ok = ev.get("replay_match") is True
        drills.append(
            {
                "id": "R6",
                "name": "回放一致性抽检",
                "automated": True,
                "pass": r6_ok,
                "evidence": {"decisionHash": ev.get("decisionHash"), "replay_match": ev.get("replay_match")},
            }
        )
    except Exception as exc:
        drills.append({"id": "R6", "name": "回放一致性抽检", "automated": True, "pass": False, "error": str(exc)})

    # Restore dev runtime so local pytest / Studio are not left in L3
    try:
        with admin_store._LOCK:
            data = admin_store._load_unlocked()
            data["runtime"] = {}
            admin_store._save_unlocked(data)
    except Exception:
        pass
    try:
        reg = get_registry()
        rec = reg.get(EVENT_RECAP_TEMPLATE_ID)
        if get_effective_lifecycle(EVENT_RECAP_TEMPLATE_ID, default=rec.lifecycle) == "disabled":
            rev = get_store_revision()
            update_template_lifecycle(
                EVENT_RECAP_TEMPLATE_ID,
                rec.lifecycle,
                current="disabled",
                expected_revision=rev,
                confirm_high_risk=True,
                operator="drill-restore",
            )
    except Exception:
        pass

    passed = sum(1 for d in drills if d.get("pass") is True)
    return {
        "phase": "P13.1",
        "generatedAt": _utc_now(),
        "environment": "dev-automated",
        "operator": "phase13_rollback_drill.py",
        "drills": drills,
        "summary": f"自动化演练 {passed}/{len(drills)} 通过",
        "allPass": passed == len(drills),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 rollback drill")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase13-rollback-drill.json",
    )
    parser.add_argument("--state", type=Path, default=None, help="isolated admin state json")
    parser.add_argument(
        "--use-project-state",
        action="store_true",
        help="写入项目 runs/template_admin_state.json（默认用临时文件）",
    )
    args = parser.parse_args()

    state_path = args.state
    if state_path is None and not args.use_project_state:
        import tempfile

        state_path = Path(tempfile.mkdtemp(prefix="p13-drill-")) / "template_admin_state.json"

    report = run_drills(state_path=state_path)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write} ({report['summary']})")
    else:
        print(text)
    return 0 if report.get("allPass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
