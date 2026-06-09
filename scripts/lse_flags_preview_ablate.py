#!/usr/bin/env python3
"""Side-by-side HTML preview + single-capability ablation for LSE flags.

Usage:
  python scripts/lse_flags_preview_ablate.py demo-1506104ebf
  python scripts/lse_flags_preview_ablate.py demo-1506104ebf --ablate-only
  python scripts/lse_flags_preview_ablate.py demo-1506104ebf --preview-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lse_flags_curate_compare import (
    _cfg_variant,
    _diff_report,
    _pattern_sequence,
    _prepare_trip,
    _run_variant,
    _screen_signatures,
)

import travelogue.curation.screen_planner  # noqa: F401
from travelogue.config import AppConfig, get_config
from travelogue.config.layout import LayoutStrategyCapabilitiesConfig
from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS
from travelogue.render.engine import render_trip

CAP_ABLATIONS: list[tuple[str, dict[str, Any]]] = [
    ("saliency_scoring", {"saliency_scoring": True}),
    ("tone_harmony", {"tone_harmony": True}),
    ("beat_profile", {"beat_profile": "classic_magazine"}),
    ("hungarian_assignment", {"hungarian_assignment": True}),
    ("quality_unified", {"quality_unified": True}),
    ("segment_order_optimizer", {"segment_order_optimizer": True}),
    ("highlight_windows", {"highlight_windows": True}),
    ("editorial_hints", {"editorial_hints": True}),
]


def _caps_from_overrides(**overrides: Any) -> LayoutStrategyCapabilitiesConfig:
    return LayoutStrategyCapabilitiesConfig(**overrides)


def _full_caps() -> LayoutStrategyCapabilitiesConfig:
    return _caps_from_overrides(
        saliency_scoring=True,
        tone_harmony=True,
        hungarian_assignment=True,
        quality_unified=True,
        segment_order_optimizer=True,
        highlight_windows=True,
        editorial_hints=True,
        beat_profile="classic_magazine",
    )


def _summary_from_body(body: dict, *, label: str, cfg: AppConfig) -> dict[str, Any]:
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.layout_engine.registry import get_strategy_pack

    chapters = body.get("chapters") or []
    metrics = compute_layout_metrics(chapters, body.get("assets") or [])
    curation = body.get("curation") or {}
    ls = curation.get("layoutStrategy") or {}
    pack = get_strategy_pack(cfg.layout.strategy_engine.default_strategy_id) if cfg.layout.strategy_engine.enabled else None
    from travelogue.layout_engine.adapter import mosaic_config_from_pack

    mosaic_cfg = mosaic_config_from_pack(cfg, pack) if pack else None
    return {
        "label": label,
        "chapterCount": len(chapters),
        "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
        "patternSequence": _pattern_sequence(chapters),
        "screenSignatures": _screen_signatures(chapters),
        "layoutStrategy": ls,
        "capabilityFlags": ls.get("capabilityFlags"),
        "mosaicDecisionLogCount": len(curation.get("mosaicDecisionLog") or []),
        "layoutDecisionLogCount": len(curation.get("layoutDecisionLog") or []),
        "metrics": metrics,
        "mosaicRuntime": {
            "lse_saliency_scoring": getattr(mosaic_cfg, "lse_saliency_scoring", False),
            "lse_tone_harmony": getattr(mosaic_cfg, "lse_tone_harmony", False),
            "lse_beat_profile": getattr(mosaic_cfg, "lse_beat_profile", "flat"),
            "lse_hungarian_assignment": getattr(mosaic_cfg, "lse_hungarian_assignment", False),
            "toneContinuityWeight": float((mosaic_cfg.weights or {}).get("tone_continuity") or 0.0)
            if mosaic_cfg
            else 0.0,
        },
    }


def _run_curated_body(
    trip: dict,
    *,
    label: str,
    cfg: AppConfig,
    work_dir: Path,
) -> tuple[dict[str, Any], dict]:
    """Run curate once and return (summary dict, curated trip body)."""
    body = _prepare_trip(trip)
    trip_dir = work_dir / label
    trip_dir.mkdir(parents=True, exist_ok=True)
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    run_clustering_layer(body, trip_dir=trip_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=trip_dir, cfg=cfg)
    return _summary_from_body(body, label=label, cfg=cfg), body


def _render_variant(
    trip_path: Path,
    curated: dict,
    *,
    index_name: str,
    copy_css: bool,
) -> Path:
    out_dir = trip_path.parent
    render_trip(
        trip_path,
        out_dir,
        trip=curated,
        validate=False,
        copy_css=copy_css,
        index_name=index_name,
        layout_engine=LAYOUT_ENGINE_SCREENS,
        export_layout_override="web",
        update_pipeline=False,
    )
    return out_dir / index_name


def _write_compare_html(
    out_path: Path,
    *,
    title: str,
    baseline_html: str,
    caps_html: str,
    diff: dict[str, Any],
    ablation_rows: list[dict[str, Any]] | None,
) -> None:
    changes = diff.get("firstPatternChanges") or []
    change_items = "\n".join(
        f'<li><button type="button" data-screen="{row["index"] + 1}">'
        f'屏 {row["index"] + 1}: {row.get("from") or "—"} → {row.get("to") or "—"}'
        f"</button></li>"
        for row in changes
    )
    ablation_table = ""
    if ablation_rows:
        rows = "\n".join(
            f"<tr><td>{r['capability']}</td>"
            f"<td>{r['screensChanged']}/{r['screensTotal']}</td>"
            f"<td>{r['screensChangedPct']}%</td>"
            f"<td>{r['patternOnlyChanges']}</td></tr>"
            for r in sorted(ablation_rows, key=lambda x: -x["screensChangedPct"])
        )
        ablation_table = f"""
<h2>单能力消融（相对 baseline）</h2>
<table>
  <thead><tr><th>能力</th><th>变更屏</th><th>变更%</th><th>pattern变</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>LSE A/B · {title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 14px/1.4 system-ui, sans-serif; background: #1a1a1a; color: #eee; }}
    header {{ padding: 12px 16px; background: #111; border-bottom: 1px solid #333; }}
    header h1 {{ margin: 0 0 8px; font-size: 18px; }}
    .meta {{ color: #aaa; font-size: 13px; }}
    .panels {{ display: grid; grid-template-columns: 1fr 1fr; height: calc(100vh - 220px); min-height: 480px; }}
    .panel {{ display: flex; flex-direction: column; border-right: 1px solid #333; }}
    .panel:last-child {{ border-right: none; }}
    .panel label {{ padding: 8px 12px; background: #222; font-weight: 600; }}
    iframe {{ flex: 1; width: 100%; border: none; background: #fff; }}
    aside {{ padding: 12px 16px; max-height: 200px; overflow: auto; border-top: 1px solid #333; }}
    aside ul {{ list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-wrap: wrap; gap: 6px; }}
    aside button {{ cursor: pointer; padding: 4px 8px; border: 1px solid #555; background: #333; color: #eee; border-radius: 4px; }}
    aside button:hover {{ background: #444; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 8px; font-size: 13px; }}
    th, td {{ border: 1px solid #444; padding: 6px 8px; text-align: left; }}
    th {{ background: #222; }}
  </style>
</head>
<body>
  <header>
    <h1>LSE 对比 · {title}</h1>
    <div class="meta">
      左：baseline（LSE 关） · 右：capabilities 全开 ·
      变更 {diff.get("screensChanged", 0)}/{diff.get("screensTotal", 0)} 屏（{diff.get("screensChangedPct", 0)}%）
    </div>
  </header>
  <div class="panels">
    <div class="panel">
      <label>Baseline · LSE off</label>
      <iframe id="frame-baseline" src="{baseline_html}"></iframe>
    </div>
    <div class="panel">
      <label>Caps full · LSE on</label>
      <iframe id="frame-caps" src="{caps_html}"></iframe>
    </div>
  </div>
  <aside>
    <strong>点击跳转到变更屏（1-based index，两侧同步滚动）</strong>
    <ul id="jump-list">{change_items or "<li>无 pattern 差异记录</li>"}</ul>
    {ablation_table}
  </aside>
  <script>
    function scrollFrame(frame, screenIndex) {{
      var doc = frame.contentDocument;
      if (!doc) return;
      var el = doc.querySelector('[data-screen-index="' + screenIndex + '"]');
      if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
    document.getElementById('jump-list').addEventListener('click', function (e) {{
      var btn = e.target.closest('button[data-screen]');
      if (!btn) return;
      var idx = btn.getAttribute('data-screen');
      scrollFrame(document.getElementById('frame-baseline'), idx);
      scrollFrame(document.getElementById('frame-caps'), idx);
    }});
  </script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def run_ablation(
    trip: dict,
    *,
    base_cfg: AppConfig,
    work_dir: Path,
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cap_name, overrides in CAP_ABLATIONS:
        caps = _caps_from_overrides(**overrides)
        label = f"ablate_{cap_name}"
        candidate = _run_variant(
            trip,
            label=label,
            cfg=_cfg_variant(base_cfg, enabled=True, caps=caps),
            work_dir=work_dir,
        )
        diff = _diff_report(baseline, candidate)
        rows.append(
            {
                "capability": cap_name,
                "enabled": overrides,
                **diff,
            }
        )
        print(
            f"  ablate {cap_name}: {diff['screensChanged']}/{diff['screensTotal']} "
            f"({diff['screensChangedPct']}%)"
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="LSE preview + single-cap ablation")
    parser.add_argument("trip_id", nargs="?", default="demo-1506104ebf")
    parser.add_argument("--trip-dir", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "lse-flags-compare")
    parser.add_argument("--ablate-only", action="store_true")
    parser.add_argument("--preview-only", action="store_true")
    args = parser.parse_args()

    trip_dir = args.trip_dir or (ROOT / "trips" / args.trip_id)
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        print(f"trip not found: {trip_path}", file=sys.stderr)
        return 1

    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    title = (trip.get("meta") or {}).get("title") or trip_dir.name
    base_cfg = get_config(reload=True)
    work = args.out / trip_dir.name
    work.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {trip_dir.name} ({title}) ===")

    baseline = _run_variant(
        trip,
        label="baseline_lse_off",
        cfg=_cfg_variant(base_cfg, enabled=False),
        work_dir=work,
    )
    caps = _run_variant(
        trip,
        label="caps_full_lse_on",
        cfg=_cfg_variant(base_cfg, enabled=True, caps=_full_caps()),
        work_dir=work,
    )
    diff = _diff_report(baseline, caps)
    print(f"baseline vs caps_full: {diff['screensChanged']}/{diff['screensTotal']} ({diff['screensChangedPct']}%)")

    ablation_rows: list[dict[str, Any]] | None = None
    if not args.preview_only:
        print("\n--- 单能力消融 ---")
        ablation_rows = run_ablation(trip, base_cfg=base_cfg, work_dir=work, baseline=baseline)
        ablation_path = work / "ablation_report.json"
        ablation_path.write_text(
            json.dumps(
                {
                    "tripId": trip_dir.name,
                    "title": title,
                    "baselineVsCapsFull": diff,
                    "ablations": ablation_rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\n消融报告: {ablation_path}")

    if not args.ablate_only:
        print("\n--- 渲染 HTML 预览 ---")
        _, baseline_body = _run_curated_body(
            trip,
            label="render_baseline",
            cfg=_cfg_variant(base_cfg, enabled=False),
            work_dir=work / "_render",
        )
        _, caps_body = _run_curated_body(
            trip,
            label="render_caps",
            cfg=_cfg_variant(base_cfg, enabled=True, caps=_full_caps()),
            work_dir=work / "_render",
        )
        baseline_index = "index-lse-baseline.html"
        caps_index = "index-lse-caps-full.html"
        _render_variant(trip_path, baseline_body, index_name=baseline_index, copy_css=True)
        _render_variant(trip_path, caps_body, index_name=caps_index, copy_css=False)

        preview_dir = work / "preview"
        rel_baseline = f"../../../../trips/{trip_dir.name}/{baseline_index}"
        rel_caps = f"../../../../trips/{trip_dir.name}/{caps_index}"
        compare_html = preview_dir / "compare.html"
        _write_compare_html(
            compare_html,
            title=title,
            baseline_html=rel_baseline,
            caps_html=rel_caps,
            diff=diff,
            ablation_rows=ablation_rows,
        )
        print(f"并排预览: {compare_html}")
        print(f"Baseline HTML: {trip_dir / baseline_index}")
        print(f"Caps full HTML: {trip_dir / caps_index}")
        print("\n打开方式: 用浏览器直接打开 compare.html，或启动 Studio 后访问 trip 下的 index-lse-*.html")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
