"""Studio homepage holdback telemetry alert (OQ-TELEMETRY · TELEMETRY §3).

Reads funnel jsonl (or an M20-i drill report JSON) and evaluates §17.2 rollback
criteria via ``studio_telemetry_aggregate``.  Optionally posts to Slack when
``TRAVELOGUE_STUDIO_TELEMETRY_SLACK_WEBHOOK`` is set.

Behavior is additive: without a webhook the script only prints and exits with
the same code semantics as ``studio_homepage_m20i_drill`` (ROLLBACK → 1).

Usage:
    python scripts/studio_telemetry_alert.py
    python scripts/studio_telemetry_alert.py --input ~/.travelogue/telemetry/studio-homepage-events.jsonl
    python scripts/studio_telemetry_alert.py --report holdback-funnel.json --notify
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent


def _load_aggregate():
    import importlib.util

    path = _SCRIPTS / "studio_telemetry_aggregate.py"
    spec = importlib.util.spec_from_file_location("studio_telemetry_aggregate", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["studio_telemetry_aggregate"] = mod
    spec.loader.exec_module(mod)
    return mod


def _webhook_url(explicit: str | None) -> str | None:
    url = (explicit or os.environ.get("TRAVELOGUE_STUDIO_TELEMETRY_SLACK_WEBHOOK") or "").strip()
    return url or None


def _flags_from_report(report: dict[str, Any]) -> list[str]:
    flags_block = report.get("flags") if isinstance(report.get("flags"), dict) else {}
    for key in ("all", "funnel"):
        raw = flags_block.get(key)
        if isinstance(raw, list) and raw:
            return [str(f) for f in raw]
    if report.get("should_rollback") is True:
        return ["ROLLBACK: report.should_rollback=true"]
    return []


def _summary_from_report(report: dict[str, Any]) -> dict[str, Any]:
    funnel = report.get("funnel") if isinstance(report.get("funnel"), dict) else {}
    if funnel and not funnel.get("variants"):
        return funnel
    variants = funnel.get("variants")
    if isinstance(variants, dict):
        return variants
    return {}


def evaluate(
    *,
    events: list[dict[str, Any]] | None = None,
    report: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Return (rollback_flags, variant_summary_dict)."""
    agg = _load_aggregate()
    if report is not None:
        flags = _flags_from_report(report)
        summary = _summary_from_report(report)
        if flags or summary:
            return flags, summary
    if events is None:
        events = []
    summary_obj = agg.funnel_summary(events)
    flags = agg.rollback_flags(summary_obj)
    summary = {
        v: {
            "homepage_view": f.homepage_view,
            "cta_click": f.cta_click,
            "import_start": f.import_start,
            "import_success": f.import_success,
            "import_conversion": round(f.import_conversion, 4),
            "cta_per_view": round(f.cta_per_view, 4),
            "js_error_rate": round(f.js_error_rate, 6),
        }
        for v, f in summary_obj.items()
    }
    return flags, summary


def format_slack_message(flags: list[str], summary: dict[str, Any]) -> str:
    lines = ["*Travelogue Studio 首页 holdback 告警*"]
    for variant in sorted(summary):
        s = summary[variant]
        if isinstance(s, dict):
            lines.append(
                f"• `{variant}` PV={s.get('homepage_view', 0)} "
                f"conv={s.get('import_conversion', 0)} "
                f"cta/PV={s.get('cta_per_view', 0)} "
                f"js_err={s.get('js_error_rate', 0)}"
            )
    lines.append("")
    if flags:
        for flag in flags:
            lines.append(f"• {flag}")
    else:
        lines.append("• 无 §17.2 回滚触发")
    return "\n".join(lines)


def post_slack(webhook: str, text: str, *, timeout: float = 10.0) -> None:
    payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Slack webhook HTTP {resp.status}")


def exit_code_for_flags(flags: list[str]) -> int:
    if any(f.startswith("ROLLBACK:") for f in flags):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio homepage telemetry Slack alert")
    parser.add_argument("--input", type=Path, default=None, help="telemetry jsonl 路径")
    parser.add_argument("--report", type=Path, default=None, help="M20-i drill 报告 JSON")
    parser.add_argument(
        "--webhook",
        default=None,
        help="Slack webhook（默认 TRAVELOGUE_STUDIO_TELEMETRY_SLACK_WEBHOOK）",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="有 webhook 时发送 Slack（无 webhook 仅打印）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印消息，不发送 Slack",
    )
    args = parser.parse_args(argv)

    agg = _load_aggregate()
    events: list[dict[str, Any]] | None = None
    report: dict[str, Any] | None = None

    if args.report and args.report.is_file():
        report = json.loads(args.report.read_text(encoding="utf-8"))
    elif args.input and args.input.is_file():
        events = agg.parse_events(args.input.read_text(encoding="utf-8-sig").splitlines())
    else:
        default = agg._events_path()
        if default.is_file():
            events = agg.parse_events(default.read_text(encoding="utf-8-sig").splitlines())
        else:
            print(f"无 telemetry 输入：{default}", file=sys.stderr)
            return 1

    flags, summary = evaluate(events=events, report=report)
    message = format_slack_message(flags, summary)
    print(message)

    webhook = _webhook_url(args.webhook)
    if args.notify and webhook and not args.dry_run:
        try:
            post_slack(webhook, message)
            print("Slack: sent", file=sys.stderr)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"Slack: failed ({exc})", file=sys.stderr)
            return 2
    elif args.notify and not webhook:
        print("Slack: skipped (no webhook configured)", file=sys.stderr)

    return exit_code_for_flags(flags)


if __name__ == "__main__":
    raise SystemExit(main())
