"""Studio 首页 LCP P95 采集（M20-i · TELEMETRY §3 / §17.2）。

用 Playwright 在 loopback 多次加载 v2(/) 与 v3(/classic) 首页，读取
`largest-contentful-paint` 性能条目，分 variant 汇总 P50/P75/P95，并对照
§17.2「LCP P95 ↑>30%」判据（v2 vs v3 同环境）输出回滚提示。

纯函数（`percentile` / `summarize` / `lcp_rollback_flags`）import-safe，供单测；
浏览器采集路径需要 Playwright（缺失时 CLI 报错退出）。

用法：
    # 先在另一终端启动 Studio（默认 127.0.0.1:8766），再：
    python scripts/studio_lcp_measure.py --base http://127.0.0.1:8766 --runs 10 --out lcp.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

# §17.2：v2 LCP P95 相对 v3 上升超过 30% → 回滚
LCP_P95_ROLLBACK_RATIO = 1.30

# variant → 路径（M21-c 收敛后：v2 根路由，v3 仅 classic 应急入口）
VARIANT_PATHS = {"v2": "/", "v3": "/classic"}


def percentile(values: Sequence[float], p: float) -> float:
    """线性插值分位数（p ∈ [0,100]）。空序列返回 0。"""
    vals = sorted(float(v) for v in values)
    if not vals:
        return 0.0
    if len(vals) == 1:
        return vals[0]
    rank = (len(vals) - 1) * (p / 100.0)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return vals[int(rank)]
    return vals[lo] + (vals[hi] - vals[lo]) * (rank - lo)


def summarize(samples: Sequence[float]) -> dict[str, Any]:
    """→ {n, p50, p75, p95, max, mean, samples}（单位 ms）。"""
    clean = [float(s) for s in samples if s is not None and float(s) > 0]
    if not clean:
        return {"n": 0, "p50": 0.0, "p75": 0.0, "p95": 0.0, "max": 0.0, "mean": 0.0, "samples": []}
    return {
        "n": len(clean),
        "p50": round(percentile(clean, 50), 1),
        "p75": round(percentile(clean, 75), 1),
        "p95": round(percentile(clean, 95), 1),
        "max": round(max(clean), 1),
        "mean": round(sum(clean) / len(clean), 1),
        "samples": [round(s, 1) for s in clean],
    }


def lcp_rollback_flags(
    summary_by_variant: dict[str, dict[str, Any]],
    ratio: float = LCP_P95_ROLLBACK_RATIO,
) -> list[str]:
    """对照 §17.2 比较 v2 vs v3 的 P95。"""
    v2 = summary_by_variant.get("v2")
    v3 = summary_by_variant.get("v3")
    if not v2 or not v3 or v2.get("n", 0) == 0 or v3.get("n", 0) == 0:
        return ["INSUFFICIENT_DATA: 缺少 v2/v3 同环境样本，禁止仅凭单侧 LCP 自动回滚"]
    m2 = v2.get("metric", "lcp")
    m3 = v3.get("metric", "lcp")
    if m2 != m3:
        return [f"INSUFFICIENT_DATA: v2/v3 指标不一致（{m2} vs {m3}），不可比较"]
    metric = m2.upper()
    v2_p95 = v2["p95"]
    v3_p95 = v3["p95"]
    if v3_p95 <= 0:
        return ["INSUFFICIENT_DATA: v3 P95 基线为 0，无法比较"]
    delta_pct = (v2_p95 / v3_p95 - 1) * 100
    if v2_p95 > v3_p95 * ratio:
        return [
            f"ROLLBACK: v2 {metric} P95 较 v3 上升 {delta_pct:.1f}% "
            f"(v2={v2_p95:.0f}ms v3={v3_p95:.0f}ms 阈值={ratio:.0%})"
        ]
    return [f"OK: v2 {metric} P95 vs v3 = {delta_pct:+.1f}% (v2={v2_p95:.0f}ms v3={v3_p95:.0f}ms)"]


# --- 注入页面：buffered LCP + settle 后取最后一条；附带 FCP 兜底 ---
# 部分 headless 构建不发 largest-contentful-paint，FCP 作为退化代理（标注 metric）。
_PAINT_JS = """
(settleMs) => new Promise((resolve) => {
  let lcp = 0;
  function takeLcp() {
    const all = performance.getEntriesByType('largest-contentful-paint');
    if (all.length) {
      const last = all[all.length - 1];
      lcp = last.renderTime || last.loadTime || last.startTime || lcp;
    }
  }
  try {
    const po = new PerformanceObserver(() => takeLcp());
    po.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) { /* 不支持则仅靠 settle 后读取 */ }
  setTimeout(() => {
    takeLcp();
    let fcp = 0;
    const paint = performance.getEntriesByType('paint');
    for (const e of paint) if (e.name === 'first-contentful-paint') fcp = e.startTime;
    resolve({ lcp: Math.round(lcp), fcp: Math.round(fcp) });
  }, settleMs);
})
"""


def measure_paint(page, url: str, settle_ms: int = 1500) -> dict[str, float]:
    """加载 url，返回 {lcp, fcp}（ms）。lcp=0 表示该环境未发 LCP 条目。"""
    page.goto(url, wait_until="load")
    res = page.evaluate(_PAINT_JS, settle_ms) or {}
    return {"lcp": float(res.get("lcp") or 0.0), "fcp": float(res.get("fcp") or 0.0)}


def measure_lcp(page, url: str, settle_ms: int = 1500) -> float:
    """单次首屏耗时（ms）：优先 LCP，无则退化 FCP。0 表示均未采到。"""
    paint = measure_paint(page, url, settle_ms)
    return paint["lcp"] or paint["fcp"]


def run_measurements(
    base: str,
    variants: Sequence[str],
    runs: int,
    settle_ms: int,
    width: int = 1440,
    height: int = 900,
) -> dict[str, dict[str, Any]]:
    """对每个 variant 采集 `runs` 次（每次新 context，避免缓存放大）。

    每个 variant 优先用 LCP 样本；若该环境一次都未发 LCP，则退化用 FCP 并
    在 summary 标注 `metric`，便于报告区分（FCP 仅作粗粒度回归代理）。
    """
    from playwright.sync_api import sync_playwright  # 延迟导入

    out: dict[str, dict[str, Any]] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for variant in variants:
                path = VARIANT_PATHS.get(variant, "/")
                url = base.rstrip("/") + path
                lcp_samples: list[float] = []
                fcp_samples: list[float] = []
                for _ in range(runs):
                    context = browser.new_context(viewport={"width": width, "height": height})
                    page = context.new_page()
                    try:
                        paint = measure_paint(page, url, settle_ms)
                        lcp_samples.append(paint["lcp"])
                        fcp_samples.append(paint["fcp"])
                    finally:
                        context.close()
                use_lcp = any(s > 0 for s in lcp_samples)
                chosen = lcp_samples if use_lcp else fcp_samples
                summary = summarize(chosen)
                summary["metric"] = "lcp" if use_lcp else "fcp"
                out[variant] = summary
        finally:
            browser.close()
    return out


def _print_summary(summary: dict[str, dict[str, Any]], flags: list[str]) -> None:
    print("=== Studio 首页首屏耗时（ms · 分 variant）===")
    for variant in sorted(summary):
        s = summary[variant]
        print(
            f"[{variant}] metric={s.get('metric', 'lcp')} n={s['n']} "
            f"p50={s['p50']} p75={s['p75']} p95={s['p95']} max={s['max']} mean={s['mean']}"
        )
    print("\n=== §17.2 LCP 回滚判据 ===")
    for flag in flags:
        print("  - " + flag)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio 首页 LCP P95 采集")
    parser.add_argument("--base", default="http://127.0.0.1:8766", help="运行中的 Studio 基址")
    parser.add_argument("--runs", type=int, default=10, help="每 variant 采样次数")
    parser.add_argument("--settle-ms", type=int, default=1500, help="LCP 收尾等待")
    parser.add_argument("--variants", default="v2,v3", help="逗号分隔，如 v2,v3")
    parser.add_argument("--out", type=Path, default=None, help="输出 JSON 路径")
    args = parser.parse_args(argv)

    try:
        import playwright  # noqa: F401
    except ImportError:
        print("需要 playwright：pip install playwright && python -m playwright install chromium", file=sys.stderr)
        return 2

    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    summary = run_measurements(args.base, variants, args.runs, args.settle_ms)
    flags = lcp_rollback_flags(summary)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps({"base": args.base, "runs": args.runs, "summary": summary, "flags": flags},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"已写 LCP 报告：{args.out}\n")

    _print_summary(summary, flags)
    # ROLLBACK 触发时以非零码退出，便于 CI 门禁
    return 1 if any(f.startswith("ROLLBACK") for f in flags) else 0


if __name__ == "__main__":
    raise SystemExit(main())
