"""AIR unlock-gate calculator · ACP W4 / AC-ACP-11 · OQ-AIR-01 decision aid.

Reads aggregated KPI counters (from Studio homepage jsonl and/or ACP ops
summary) and returns a deterministic ``go`` / ``no-go`` / ``insufficient-data``
verdict. Never mutates config.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["go", "no-go", "insufficient-data"]

# Align sample floor with CTS G-CTS-05 「≥30 impression」spirit (SHD-ACP-05).
DEFAULT_MIN_SAMPLES = 30


@dataclass(frozen=True)
class UnlockThresholds:
    """AIR/CTS agreed floors (defaults; override via config or call args)."""

    min_samples: int = DEFAULT_MIN_SAMPLES
    config_conversion_rate: float = 0.40
    narrate_success_rate: float = 0.70
    channel_copy_rate: float = 0.30


@dataclass
class UnlockMetrics:
    """Three AIR §7 KPIs + optional CTS title_art funnel cross-check."""

    # Config conversion: settings open → save or successful ping
    config_opens: int = 0
    config_completions: int = 0
    # Narrate: clicks / ACP narrate ok vs attempts
    narrate_attempts: int = 0
    narrate_successes: int = 0
    # Channel copy: share / copy pack actions vs opportunities
    copy_opportunities: int = 0
    copy_successes: int = 0
    # Optional CTS D-CAL-27 (report only; does not drive AIR verdict)
    title_art_impressions: int = 0
    title_art_resolves: int = 0
    title_art_failures: int = 0
    source: str = "fixture"

    def rate(self, successes: int, attempts: int) -> float | None:
        if attempts <= 0:
            return None
        return successes / attempts

    @property
    def config_conversion(self) -> float | None:
        return self.rate(self.config_completions, self.config_opens)

    @property
    def narrate_success(self) -> float | None:
        return self.rate(self.narrate_successes, self.narrate_attempts)

    @property
    def channel_copy(self) -> float | None:
        return self.rate(self.copy_successes, self.copy_opportunities)


@dataclass
class UnlockGateResult:
    verdict: Verdict
    metrics: UnlockMetrics
    thresholds: UnlockThresholds
    reasons: list[str] = field(default_factory=list)
    kpi: dict[str, Any] = field(default_factory=dict)
    computed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "computedAt": self.computed_at or _utc_now_iso(),
            "reasons": list(self.reasons),
            "kpi": dict(self.kpi),
            "metrics": asdict(self.metrics),
            "thresholds": asdict(self.thresholds),
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pct(rate: float | None) -> str:
    if rate is None:
        return "n/a"
    return f"{rate * 100:.1f}%"


def compute_unlock_gate(
    metrics: UnlockMetrics,
    *,
    thresholds: UnlockThresholds | None = None,
) -> UnlockGateResult:
    """Deterministic three-state verdict (AC-ACP-11).

    Rules:
    1. If any of the three KPI denominators ``< min_samples`` → ``insufficient-data``.
    2. Else if all three rates meet floors → ``go``.
    3. Else → ``no-go``.
    """
    thr = thresholds or UnlockThresholds()
    reasons: list[str] = []
    kpi = {
        "configConversion": {
            "rate": metrics.config_conversion,
            "n": metrics.config_opens,
            "floor": thr.config_conversion_rate,
        },
        "narrateSuccess": {
            "rate": metrics.narrate_success,
            "n": metrics.narrate_attempts,
            "floor": thr.narrate_success_rate,
        },
        "channelCopy": {
            "rate": metrics.channel_copy,
            "n": metrics.copy_opportunities,
            "floor": thr.channel_copy_rate,
        },
        "titleArtFunnel": {
            "impressions": metrics.title_art_impressions,
            "resolves": metrics.title_art_resolves,
            "failures": metrics.title_art_failures,
            "entryRate": metrics.rate(
                metrics.title_art_resolves, metrics.title_art_impressions
            ),
            "note": "CTS G-CTS-05 / D-CAL-27 cross-check only (SHD-ACP-05)",
        },
    }

    samples = (
        ("configConversion", metrics.config_opens),
        ("narrateSuccess", metrics.narrate_attempts),
        ("channelCopy", metrics.copy_opportunities),
    )
    short = [name for name, n in samples if n < thr.min_samples]
    if short:
        reasons.append(
            f"insufficient samples for {', '.join(short)} "
            f"(need ≥{thr.min_samples} each)"
        )
        return UnlockGateResult(
            verdict="insufficient-data",
            metrics=metrics,
            thresholds=thr,
            reasons=reasons,
            kpi=kpi,
            computed_at=_utc_now_iso(),
        )

    checks = (
        ("configConversion", metrics.config_conversion, thr.config_conversion_rate),
        ("narrateSuccess", metrics.narrate_success, thr.narrate_success_rate),
        ("channelCopy", metrics.channel_copy, thr.channel_copy_rate),
    )
    failed: list[str] = []
    for name, rate, floor in checks:
        if rate is None or rate < floor:
            failed.append(f"{name} {_pct(rate)} < {_pct(floor)}")
    if failed:
        reasons.extend(failed)
        return UnlockGateResult(
            verdict="no-go",
            metrics=metrics,
            thresholds=thr,
            reasons=reasons,
            kpi=kpi,
            computed_at=_utc_now_iso(),
        )

    reasons.append("all AIR KPI floors met")
    return UnlockGateResult(
        verdict="go",
        metrics=metrics,
        thresholds=thr,
        reasons=reasons,
        kpi=kpi,
        computed_at=_utc_now_iso(),
    )


def metrics_from_dict(raw: dict[str, Any] | None) -> UnlockMetrics:
    raw = raw or {}
    return UnlockMetrics(
        config_opens=int(raw.get("configOpens") or raw.get("config_opens") or 0),
        config_completions=int(
            raw.get("configCompletions") or raw.get("config_completions") or 0
        ),
        narrate_attempts=int(
            raw.get("narrateAttempts") or raw.get("narrate_attempts") or 0
        ),
        narrate_successes=int(
            raw.get("narrateSuccesses") or raw.get("narrate_successes") or 0
        ),
        copy_opportunities=int(
            raw.get("copyOpportunities") or raw.get("copy_opportunities") or 0
        ),
        copy_successes=int(raw.get("copySuccesses") or raw.get("copy_successes") or 0),
        title_art_impressions=int(
            raw.get("titleArtImpressions") or raw.get("title_art_impressions") or 0
        ),
        title_art_resolves=int(
            raw.get("titleArtResolves") or raw.get("title_art_resolves") or 0
        ),
        title_art_failures=int(
            raw.get("titleArtFailures") or raw.get("title_art_failures") or 0
        ),
        source=str(raw.get("source") or "fixture"),
    )


def aggregate_studio_events(
    events_path: Path | None = None,
    *,
    ops: dict[str, Any] | None = None,
) -> UnlockMetrics:
    """Aggregate local Studio jsonl (+ optional ACP ops_summary) into KPIs.

    Event mapping (best-effort; missing events → zero denominators →
    ``insufficient-data`` until dogfood fills the funnel):

    - config: ``llm_settings_open`` → opens; ``llm_settings_save`` /
      ``llm_ping`` (meta.ok true) / ``llm_save_and_ping`` → completions
    - narrate: ``llm_narrate_click`` attempts; successes = attempts −
      ``preview_narrate_fail`` (floor 0), or ACP ``narrate`` ops ok/calls
    - copy: ``import_success`` opportunities; ``sfp_xhs_copy_pack_copied`` /
      ``first_success_copy_branch`` / ``refine_copy_branch`` successes
    - title_art: ``title_art_impression`` / ``title_art_resolve`` (D-CAL-27)
    """
    from travelogue.domain.studio_events import studio_homepage_events_path

    path = events_path or studio_homepage_events_path()
    opens = completions = 0
    narrate_attempts = narrate_fails = 0
    copy_opp = copy_ok = 0
    ta_imp = ta_res = ta_fail = 0

    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            ev = str(row.get("event") or "")
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if ev == "llm_settings_open":
                opens += 1
            elif ev in ("llm_settings_save", "llm_save_and_ping"):
                completions += 1
            elif ev == "llm_ping":
                if meta.get("ok") is True:
                    completions += 1
            elif ev == "llm_narrate_click":
                narrate_attempts += 1
            elif ev == "preview_narrate_fail":
                narrate_fails += 1
            elif ev == "import_success":
                copy_opp += 1
            elif ev in (
                "sfp_xhs_copy_pack_copied",
                "first_success_copy_branch",
                "refine_copy_branch",
            ):
                copy_ok += 1
            elif ev == "title_art_impression":
                ta_imp += 1
            elif ev == "title_art_resolve":
                ta_res += 1
                if str(meta.get("outcome") or "") in ("error", "network"):
                    ta_fail += 1

    narrate_successes = max(0, narrate_attempts - narrate_fails)
    # Prefer ACP process-local narrate stats when present (more accurate ok).
    if ops and isinstance(ops.get("narrate"), dict):
        slot = ops["narrate"]
        calls = int(slot.get("calls") or 0)
        ok = int(slot.get("ok") or 0)
        if calls > 0:
            narrate_attempts = max(narrate_attempts, calls)
            narrate_successes = ok

    return UnlockMetrics(
        config_opens=opens,
        config_completions=completions,
        narrate_attempts=narrate_attempts,
        narrate_successes=narrate_successes,
        copy_opportunities=copy_opp,
        copy_successes=copy_ok,
        title_art_impressions=ta_imp,
        title_art_resolves=ta_res,
        title_art_failures=ta_fail,
        source=f"jsonl:{path}" if path.is_file() else "empty",
    )


def format_unlock_report(result: UnlockGateResult) -> str:
    """Human-readable AIR unlock recommendation (does not change config)."""
    m = result.metrics
    t = result.thresholds
    lines = [
        "# AIR 解冻门槛建议报告",
        "",
        f"- 计算时间：{result.computed_at or _utc_now_iso()}",
        f"- 裁决：**{result.verdict}**",
        f"- 数据源：{m.source}",
        "",
        "## KPI",
        "",
        f"| KPI | 样本 n | 比率 | 门槛 |",
        f"|-----|--------|------|------|",
        f"| 配置转化 | {m.config_opens} | {_pct(m.config_conversion)} | ≥{_pct(t.config_conversion_rate)} |",
        f"| narrate 成功 | {m.narrate_attempts} | {_pct(m.narrate_success)} | ≥{_pct(t.narrate_success_rate)} |",
        f"| 渠道复制 | {m.copy_opportunities} | {_pct(m.channel_copy)} | ≥{_pct(t.channel_copy_rate)} |",
        "",
        "## 理由",
        "",
    ]
    for r in result.reasons:
        lines.append(f"- {r}")
    lines.extend(
        [
            "",
            "## CTS 交叉（D-CAL-27 / G-CTS-05，不驱动 AIR 裁决）",
            "",
            f"- title_art impression：{m.title_art_impressions}",
            f"- title_art resolve：{m.title_art_resolves}",
            f"- title_art fail (error|network)：{m.title_art_failures}",
            "",
            "> 本报告仅供 OQ-AIR-01 决策参考，**不会**自动改写 `aiSurfaceEnabled`。",
            "",
        ]
    )
    return "\n".join(lines)


def run_unlock_gate(
    *,
    metrics: UnlockMetrics | None = None,
    events_path: Path | None = None,
    thresholds: UnlockThresholds | None = None,
    include_ops: bool = True,
) -> UnlockGateResult:
    """Convenience entry: fixture metrics or live aggregate → verdict."""
    if metrics is None:
        ops = None
        if include_ops:
            try:
                from travelogue.ai.telemetry import ops_summary

                ops = ops_summary()
            except Exception:  # noqa: BLE001
                ops = None
        metrics = aggregate_studio_events(events_path, ops=ops)
    return compute_unlock_gate(metrics, thresholds=thresholds)
