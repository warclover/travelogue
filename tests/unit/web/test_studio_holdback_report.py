"""Tests for scripts/studio_holdback_report.py (M20-i · holdback 合并报告)."""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import json
import sys
from pathlib import Path

_SCRIPT = repo_root(__file__) / "scripts" / "studio_holdback_report.py"
_spec = importlib.util.spec_from_file_location("studio_holdback_report", _SCRIPT)
hb_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_holdback_report"] = hb_mod
_spec.loader.exec_module(hb_mod)


def _event(variant: str, name: str) -> dict:
    return {"ts": "2026-06-01T00:00:00.000+00:00", "event": name, "meta": {"variant": variant}}


def test_classify_flags() -> None:
    buckets = hb_mod.classify_flags([
        "ROLLBACK: import 转化率下降 20%",
        "WARN: v3 无 JS error 基线",
        "INSUFFICIENT_DATA: 缺少对照",
        "OK: v2 LCP P95 vs v3 = +5%",
    ])
    assert len(buckets["rollback"]) == 1
    assert len(buckets["warn"]) == 1
    assert len(buckets["insufficient"]) == 1
    assert len(buckets["ok"]) == 1


def test_build_holdback_report_triggers_rollback() -> None:
    events = (
        [_event("v3", "homepage_view")] * 10
        + [_event("v3", "import_start")] * 10
        + [_event("v3", "import_success")] * 10
        + [_event("v2", "homepage_view")] * 10
        + [_event("v2", "import_start")] * 10
        + [_event("v2", "import_success")] * 5  # 50% vs 100%
    )
    lcp = {
        "v2": {"n": 10, "p95": 2000.0, "metric": "lcp"},
        "classic": {"n": 10, "p95": 1000.0, "metric": "lcp"},
    }
    report = hb_mod.build_holdback_report(events, lcp)
    assert report["should_rollback"] is True
    assert any("import 转化率" in f for f in report["flags"]["funnel"])
    assert any(f.startswith("ROLLBACK") for f in report["flags"]["lcp"])
    assert "v2" in report["funnel"]
    assert report["lcp"]["v2"]["p95"] == 2000.0


def test_build_holdback_report_ok_without_lcp() -> None:
    events = (
        [_event("v3", "homepage_view")] * 5
        + [_event("v2", "homepage_view")] * 5
    )
    report = hb_mod.build_holdback_report(events, None)
    assert report["should_rollback"] is False
    assert report["lcp"] is None
    assert report["flags"]["lcp"] == []


def test_main_writes_json(tmp_path) -> None:
    jsonl = tmp_path / "events.jsonl"
    jsonl.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in [
            _event("v2", "homepage_view"),
            _event("v3", "homepage_view"),
        ]),
        encoding="utf-8",
    )
    lcp_json = tmp_path / "lcp.json"
    lcp_json.write_text(json.dumps({
        "summary": {
            "v2": {"n": 5, "p95": 1100.0, "p50": 1000.0, "metric": "fcp"},
            "v3": {"n": 5, "p95": 1000.0, "p50": 900.0, "metric": "fcp"},
        },
    }), encoding="utf-8")
    out = tmp_path / "holdback.json"
    rc = hb_mod.main([
        "--telemetry", str(jsonl),
        "--lcp-json", str(lcp_json),
        "--out", str(out),
    ])
    assert rc == 0
    body = json.loads(out.read_text(encoding="utf-8"))
    assert "funnel" in body
    assert "lcp" in body
    assert "should_rollback" in body
