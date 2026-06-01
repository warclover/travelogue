"""Tests for scripts/studio_telemetry_aggregate.py (M20-i · TELEMETRY §3)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "studio_telemetry_aggregate.py"
_spec = importlib.util.spec_from_file_location("studio_telemetry_aggregate", _SCRIPT)
agg_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
# dataclass 装饰器会查 cls.__module__ in sys.modules（Py3.12+），需先注册。
sys.modules["studio_telemetry_aggregate"] = agg_mod
_spec.loader.exec_module(agg_mod)


def _jsonl(records: list[dict]) -> list[str]:
    return [json.dumps(r, ensure_ascii=False) for r in records]


def test_parse_events_skips_bad_lines() -> None:
    lines = [
        json.dumps({"ts": "2026-06-01T00:00:00.000+00:00", "event": "homepage_view"}),
        "{not json}",
        "",
        json.dumps({"ts": "x", "noevent": 1}),  # 无 event 丢弃
    ]
    events = agg_mod.parse_events(lines)
    assert len(events) == 1
    assert events[0]["event"] == "homepage_view"


def test_aggregate_by_day_variant_event() -> None:
    recs = [
        {"ts": "2026-06-01T10:00:00.000+00:00", "event": "homepage_view", "meta": {"variant": "v2"}},
        {"ts": "2026-06-01T11:00:00.000+00:00", "event": "homepage_view", "meta": {"variant": "v2"}},
        {"ts": "2026-06-02T10:00:00.000+00:00", "event": "homepage_view", "meta": {"variant": "v3"}},
    ]
    out = agg_mod.aggregate(agg_mod.parse_events(_jsonl(recs)))
    assert out[("2026-06-01", "v2", "homepage_view")] == 2
    assert out[("2026-06-02", "v3", "homepage_view")] == 1


def test_funnel_ratios() -> None:
    recs = (
        [{"ts": "2026-06-01T00:00:00.000+00:00", "event": "homepage_view", "meta": {"variant": "v2"}}] * 10
        + [{"ts": "2026-06-01T00:00:00.000+00:00", "event": "cta_click", "meta": {"variant": "v2"}}] * 5
        + [{"ts": "2026-06-01T00:00:00.000+00:00", "event": "import_start", "meta": {"variant": "v2"}}] * 4
        + [{"ts": "2026-06-01T00:00:00.000+00:00", "event": "import_success", "meta": {"variant": "v2"}}] * 2
    )
    summary = agg_mod.funnel_summary(agg_mod.parse_events(_jsonl(recs)))
    f = summary["v2"]
    assert f.homepage_view == 10
    assert f.cta_per_view == pytest.approx(0.5)
    assert f.import_conversion == pytest.approx(0.5)


def test_rollback_flags_triggers_on_conversion_drop() -> None:
    recs = (
        # v3 baseline：转化 100%
        [{"event": "import_start", "meta": {"variant": "v3"}}] * 10
        + [{"event": "import_success", "meta": {"variant": "v3"}}] * 10
        # v2：转化 50% → 下降 50% > 15% 阈值
        + [{"event": "import_start", "meta": {"variant": "v2"}}] * 10
        + [{"event": "import_success", "meta": {"variant": "v2"}}] * 5
    )
    summary = agg_mod.funnel_summary(agg_mod.parse_events(_jsonl(recs)))
    flags = agg_mod.rollback_flags(summary)
    assert any("import 转化率下降" in f for f in flags)


def test_rollback_flags_insufficient_without_holdback() -> None:
    recs = [{"event": "homepage_view", "meta": {"variant": "v2"}}]
    summary = agg_mod.funnel_summary(agg_mod.parse_events(_jsonl(recs)))
    flags = agg_mod.rollback_flags(summary)
    assert any("INSUFFICIENT_DATA" in f for f in flags)


def test_main_writes_csv(tmp_path) -> None:
    src = tmp_path / "events.jsonl"
    src.write_text(
        "\n".join(_jsonl([
            {"ts": "2026-06-01T00:00:00.000+00:00", "event": "homepage_view", "meta": {"variant": "v2"}},
            {"ts": "2026-06-01T00:00:00.000+00:00", "event": "cta_click", "meta": {"variant": "v2"}},
        ])),
        encoding="utf-8",
    )
    out = tmp_path / "report.csv"
    rc = agg_mod.main(["--input", str(src), "--out", str(out)])
    assert rc == 0
    body = out.read_text(encoding="utf-8")
    assert "date,variant,event,count" in body
    assert "v2,cta_click,1" in body or "v2,homepage_view,1" in body
