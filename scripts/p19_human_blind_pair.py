#!/usr/bin/env python3
"""Generate baseline vs P19-candidate HTML pair for human blind review (solo or team).

Usage:
  python scripts/p19_human_blind_pair.py demo-b388794e0a
  python scripts/p19_human_blind_pair.py --trip-dir trips/demo-b388794e0a
  python scripts/p19_human_blind_pair.py demo-b388794e0a --reveal-labels
  python scripts/p19_human_blind_pair.py demo-b388794e0a --p19-visible
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import travelogue.curation.screen_planner  # noqa: F401
from travelogue.config import get_config
from travelogue.curation.layout_metrics import compute_layout_metrics
from travelogue.render.engine import render_trip
from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

from book_quality_baseline import (
    _curate_trip,
    _p16_cfg,
    _p19_candidate_cfg,
    _p19_visible_cfg,
)
from lse_flags_curate_compare import _diff_report, _pattern_sequence, _screen_signatures


def _lte_rollout_dogfood_full(pattern_id: str, trip_id: str | None = None) -> bool:
    """Dogfood: any template with rollout.percent>0 is eligible (spread/asymmetric 15% → 100%)."""
    from travelogue.curation.mosaic.lte_adapter import read_templates_from_lte

    if not read_templates_from_lte():
        return True
    try:
        from travelogue.layout_templates.registry import get_engine

        tpl = get_engine().get(pattern_id)
        rollout = tpl.rollout or {}
        pct = float(rollout.get("percent", 100))
    except (KeyError, TypeError, ValueError):
        return True
    if pct <= 0:
        return False
    return True


def _link_or_copy_tree(src: Path, dest: Path) -> None:
    """Stage trip media beside cache render root (avoid overwriting locked trip JS)."""
    if dest.exists():
        return
    try:
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dest), str(src)],
            check=True,
            capture_output=True,
        )
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    import shutil

    shutil.copytree(src, dest)


def _prepare_render_root(source_trip_dir: Path, render_root: Path, curated: dict) -> Path:
    render_root.mkdir(parents=True, exist_ok=True)
    trip_path = render_root / "trip.json"
    trip_path.write_text(json.dumps(curated, ensure_ascii=False, indent=2), encoding="utf-8")
    for name in ("assets", "source", "vendor"):
        src = source_trip_dir / name
        if src.is_dir():
            _link_or_copy_tree(src, render_root / name)
    return trip_path


def _render_variant(
    source_trip_dir: Path,
    render_root: Path,
    curated: dict,
    *,
    index_name: str,
    copy_css: bool,
) -> Path:
    trip_path = _prepare_render_root(source_trip_dir, render_root, curated)
    render_trip(
        trip_path,
        render_root,
        trip=curated,
        validate=False,
        copy_css=copy_css,
        index_name=index_name,
        layout_engine=LAYOUT_ENGINE_SCREENS,
        export_layout_override="web",
        update_pipeline=False,
    )
    return render_root / index_name


def _summary_from_body(body: dict, *, label: str) -> dict[str, Any]:
    chapters = body.get("chapters") or []
    return {
        "label": label,
        "screenCount": sum(len(ch.get("screens") or []) for ch in chapters),
        "patternSequence": _pattern_sequence(chapters),
        "screenSignatures": _screen_signatures(chapters),
        "metrics": compute_layout_metrics(chapters, body.get("assets") or []),
    }


def _write_compare_html(
    out_path: Path,
    *,
    title: str,
    trip_id: str,
    left_label: str,
    right_label: str,
    left_html: str,
    right_html: str,
    blind_mapping: dict[str, str],
    diff: dict[str, Any],
    reveal_labels: bool,
) -> None:
    changes = diff.get("firstPatternChanges") or []
    change_items = "\n".join(
        f'<li><button type="button" data-screen="{row["index"] + 1}">'
        f'屏 {row["index"] + 1}: {row.get("from") or "—"} → {row.get("to") or "—"}'
        f"</button></li>"
        for row in changes
    )
    mapping_note = (
        f"A={blind_mapping['A']} · B={blind_mapping['B']}"
        if reveal_labels
        else "左右随机为 A / B（填表前勿查看 compare_meta.json）"
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>P19 盲评 · {title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 14px/1.4 system-ui, sans-serif; background: #1a1a1a; color: #eee; }}
    header {{ padding: 12px 16px; background: #111; border-bottom: 1px solid #333; }}
    header h1 {{ margin: 0 0 8px; font-size: 18px; }}
    .meta {{ color: #aaa; font-size: 13px; }}
    .panels {{ display: grid; grid-template-columns: 1fr 1fr; height: calc(100vh - 320px); min-height: 420px; }}
    .panel {{ display: flex; flex-direction: column; border-right: 1px solid #333; }}
    .panel:last-child {{ border-right: none; }}
    .panel label {{ padding: 8px 12px; background: #222; font-weight: 600; }}
    iframe {{ flex: 1; width: 100%; border: none; background: #fff; }}
    aside {{ padding: 12px 16px; border-top: 1px solid #333; }}
    aside ul {{ list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-wrap: wrap; gap: 6px; }}
    aside button {{ cursor: pointer; padding: 4px 8px; border: 1px solid #555; background: #333; color: #eee; border-radius: 4px; }}
    .vote {{ margin-top: 12px; padding: 12px; background: #222; border-radius: 8px; max-width: 720px; }}
    .vote label {{ display: block; margin: 8px 0 4px; }}
    .vote select, .vote input, .vote textarea {{ width: 100%; max-width: 360px; }}
    .vote button {{ margin-top: 10px; padding: 8px 14px; cursor: pointer; }}
    pre {{ background: #111; padding: 8px; overflow: auto; font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>P19 盲评 · {title}</h1>
    <div class="meta">
      tripId={trip_id} · 变更 {diff.get("screensChanged", 0)}/{diff.get("screensTotal", 0)} 屏
      （{diff.get("screensChangedPct", 0)}%）· {mapping_note}
    </div>
  </header>
  <div class="panels">
    <div class="panel">
      <label>A · {left_label}</label>
      <iframe id="frame-a" src="{left_html}"></iframe>
    </div>
    <div class="panel">
      <label>B · {right_label}</label>
      <iframe id="frame-b" src="{right_html}"></iframe>
    </div>
  </div>
  <aside>
    <strong>变更屏跳转（两侧同步）</strong>
    <ul id="jump-list">{change_items or "<li>屏序列一致或无可跳转差异</li>"}</ul>
    <div class="vote">
      <strong>自评表（导出后写入 p19-human-blind-review.json）</strong>
      <label>整体更好</label>
      <select id="overallWinner">
        <option value="">—</option>
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="tie">平局</option>
      </select>
      <label>故事更清楚</label>
      <select id="storyClarity">
        <option value="">—</option>
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="tie">平局</option>
      </select>
      <label>分享意愿（1–5）</label>
      <input id="shareIntent" type="number" min="1" max="5" />
      <label>备注</label>
      <textarea id="notes" rows="2"></textarea>
      <button type="button" id="export-vote">导出 JSON</button>
      <pre id="vote-out" hidden></pre>
    </div>
  </aside>
  <script>
    const mapping = {json.dumps(blind_mapping)};
    document.getElementById("jump-list").addEventListener("click", (e) => {{
      const btn = e.target.closest("button[data-screen]");
      if (!btn) return;
      const n = btn.getAttribute("data-screen");
      ["frame-a", "frame-b"].forEach((id) => {{
        const fr = document.getElementById(id);
        try {{
          const doc = fr.contentDocument;
          const el = doc.querySelector('[data-screen-index="' + n + '"]')
            || doc.querySelector('.layout-screen:nth-child(' + n + ')');
          if (el) el.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }} catch (_) {{}}
      }});
    }});
    document.getElementById("export-vote").addEventListener("click", () => {{
      const overall = document.getElementById("overallWinner").value;
      const story = document.getElementById("storyClarity").value;
      const share = document.getElementById("shareIntent").value;
      const notes = document.getElementById("notes").value;
      const resolved = overall === "tie" ? "tie"
        : overall ? mapping[overall] : null;
      const payload = {{
        tripId: "{trip_id}",
        blindMapping: mapping,
        overallWinner: overall || null,
        resolvedWinner: resolved,
        storyClarity: story || null,
        shareIntent: share ? Number(share) : null,
        notes: notes || "",
      }};
      const pre = document.getElementById("vote-out");
      pre.hidden = false;
      pre.textContent = JSON.stringify(payload, null, 2);
    }});
  </script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")


def _pair_one_trip(
    trip_dir: Path,
    *,
    out_root: Path,
    seed: int | None,
    reveal_labels: bool,
    p19_visible: bool,
) -> int:
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        print(f"trip not found: {trip_path}", file=sys.stderr)
        return 1

    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    trip_id = trip_dir.name
    title = (trip.get("meta") or {}).get("title") or trip_id
    base_cfg = get_config(reload=True)
    baseline_cfg = _p16_cfg(base_cfg)
    if p19_visible:
        candidate_cfg = _p19_visible_cfg(base_cfg)
        candidate_label = "P19-visible-dogfood"
    else:
        candidate_cfg = _p19_candidate_cfg(base_cfg)
        candidate_label = "P19-candidate"

    work = out_root / trip_id
    if p19_visible:
        work = work / "visible"
    work.mkdir(parents=True, exist_ok=True)
    print(f"\nTrip: {trip_id} ({title}) · assets={len(trip.get('assets') or [])}")

    print("  Curate baseline (P16-default)...")
    baseline_body = _curate_trip(trip, work_dir=work / "curate-baseline", cfg=baseline_cfg)
    baseline_sum = _summary_from_body(baseline_body, label="P16-default")

    print(f"  Curate candidate ({candidate_label})...")
    from unittest.mock import patch

    rollout_patch = patch(
        "travelogue.curation.mosaic.lte_adapter.lte_rollout_eligible",
        _lte_rollout_dogfood_full,
    )
    if p19_visible:
        with rollout_patch:
            candidate_body = _curate_trip(trip, work_dir=work / "curate-p19", cfg=candidate_cfg)
    else:
        candidate_body = _curate_trip(trip, work_dir=work / "curate-p19", cfg=candidate_cfg)
    candidate_sum = _summary_from_body(candidate_body, label=candidate_label)

    diff = _diff_report(baseline_sum, candidate_sum)
    print(
        f"  Diff: {diff['screensChanged']}/{diff['screensTotal']} "
        f"({diff['screensChangedPct']}%) pattern-only={diff['patternOnlyChanges']}"
    )

    baseline_index = "index-p19-baseline.html"
    candidate_index = "index-p19-candidate.html"
    render_root = work / "render"
    print("  Render baseline HTML...")
    _render_variant(
        trip_dir,
        render_root,
        baseline_body,
        index_name=baseline_index,
        copy_css=True,
    )
    print("  Render candidate HTML...")
    _render_variant(
        trip_dir,
        render_root,
        candidate_body,
        index_name=candidate_index,
        copy_css=False,
    )

    rng = random.Random(seed if seed is not None else trip_id)
    swap = rng.random() < 0.5
    blind_mapping = {"A": "baseline", "B": "candidate"}
    if swap:
        blind_mapping = {"A": "candidate", "B": "baseline"}

    rel_baseline = f"../render/{baseline_index}"
    rel_candidate = f"../render/{candidate_index}"
    left_html = rel_baseline if blind_mapping["A"] == "baseline" else rel_candidate
    right_html = rel_candidate if blind_mapping["B"] == "candidate" else rel_baseline
    left_label = "A" if not reveal_labels else blind_mapping["A"]
    right_label = "B" if not reveal_labels else blind_mapping["B"]

    preview_dir = work / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    compare_html = preview_dir / "compare.html"
    _write_compare_html(
        compare_html,
        title=title,
        trip_id=trip_id,
        left_label=left_label,
        right_label=right_label,
        left_html=left_html,
        right_html=right_html,
        blind_mapping=blind_mapping,
        diff=diff,
        reveal_labels=reveal_labels,
    )

    meta = {
        "tripId": trip_id,
        "title": title,
        "assetCount": len(trip.get("assets") or []),
        "baselineLabel": "P16-default",
        "candidateLabel": candidate_label,
        "p19VisibleMode": p19_visible,
        "blindMapping": blind_mapping,
        "blindSeed": seed if seed is not None else f"tripId:{trip_id}",
        "diff": diff,
        "baseline": baseline_sum,
        "candidate": candidate_sum,
        "html": {
            "baseline": str(render_root / baseline_index),
            "candidate": str(render_root / candidate_index),
            "compare": str(compare_html),
        },
    }
    (work / "compare_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (work / "compare_report.json").write_text(
        json.dumps(
            {
                "tripId": trip_id,
                "title": title,
                "diff": diff,
                "blindMapping": blind_mapping,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n并排盲评: {compare_html}")
    print(f"  Baseline 单独打开: {render_root / baseline_index}")
    print(f"  P19 单独打开:      {render_root / candidate_index}")
    print(f"  映射（填表用）:    {work / 'compare_meta.json'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="P19 baseline vs candidate blind-review pair")
    parser.add_argument("trip_id", nargs="*", help="trip folder name under trips/")
    parser.add_argument("--trip-dir", type=Path, help="Single trip directory")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".cache" / "p19-human-blind",
        help="Output root",
    )
    parser.add_argument("--seed", type=int, default=None, help="Blind A/B RNG seed (default: tripId)")
    parser.add_argument(
        "--reveal-labels",
        action="store_true",
        help="Show baseline/candidate on compare page (non-blind debug)",
    )
    parser.add_argument(
        "--p19-visible",
        action="store_true",
        help="Candidate: subset + highlight + chapter DP + full SKU rollout (dogfood review)",
    )
    args = parser.parse_args()

    trip_dirs: list[Path] = []
    if args.trip_dir:
        trip_dirs = [args.trip_dir.resolve()]
    elif args.trip_id:
        trip_dirs = [ROOT / "trips" / tid for tid in args.trip_id]
    else:
        trip_dirs = [ROOT / "trips" / "demo-b388794e0a"]

    for trip_dir in trip_dirs:
        code = _pair_one_trip(
            trip_dir.resolve(),
            out_root=args.out,
            seed=args.seed,
            reveal_labels=args.reveal_labels,
            p19_visible=args.p19_visible,
        )
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
