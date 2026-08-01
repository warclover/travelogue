#!/usr/bin/env python3
"""DES-SFI-01 / QA-SFI-06 · measure longshot vertical chrome vs photo (real trips).

Opens ``index-longshot.html`` at CAPTURE_WIDTH, unions photo element Y ranges,
and reports non-photo vertical pixel share + density levers for the compact gate.

Usage:
  python scripts/sfi_longshot_attribution.py trips/demo-1d4f92d534
  python scripts/sfi_longshot_attribution.py trips/demo-1d4f92d534 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

CAPTURE_WIDTH = 428

PHOTO_SELECTORS = (
    ".cover-hero__img",
    ".media-card__visual",
    ".layout-slot__img",
    "img.media-card__visual",
    ".layout-slot img",
)

CHROME_SELECTORS = {
    "chapterHeader": ".chapter-header, [data-block='chapter-header']",
    "chapterLead": ".chapter-lead, [data-block='chapter-lead']",
    "decorLine": ".chapter-decor-line, [data-block='decor-line']",
    "coverPanel": ".cover-opening__panel",
    "coverTitle": ".cover-opening__title",
    "hook": "[data-block='hook-line']",
    "epilogue": ".epilogue, [data-block='epilogue'], .epilogue-screen",
    "closing": ".cover-closing, .longshot-boundary-footer",
}


def _serve(trip_dir: Path) -> tuple[ThreadingHTTPServer, str]:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(trip_dir), **kwargs)

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    return server, f"http://127.0.0.1:{port}/index-longshot.html"


def measure_trip(trip_dir: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    html = trip_dir / "index-longshot.html"
    if not html.is_file():
        raise FileNotFoundError(f"missing index-longshot.html under {trip_dir}")

    server, url = _serve(trip_dir)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": CAPTURE_WIDTH, "height": 900})
            page.goto(url, wait_until="networkidle", timeout=120_000)
            # Compact CSS binds html[data-longshot-density] (not capturing), so
            # B3 / this script see FE-SFI-09 levers without invalidating DES baseline mode.
            page.wait_for_timeout(400)
            metrics = page.evaluate(
                """({ photoSelectors, chromeSelectors, captureWidth }) => {
                  const main = document.querySelector('main') || document.body;
                  const scrollH = Math.max(main.scrollHeight, main.offsetHeight, 1);
                  const photoEls = [];
                  for (const sel of photoSelectors) {
                    document.querySelectorAll(sel).forEach((el) => photoEls.push(el));
                  }
                  const uniq = Array.from(new Set(photoEls));
                  const ranges = [];
                  const assetIds = [];
                  for (const el of uniq) {
                    const r = el.getBoundingClientRect();
                    const top = r.top + window.scrollY;
                    const bottom = r.bottom + window.scrollY;
                    if (bottom <= top) continue;
                    ranges.push([Math.max(0, top), Math.min(scrollH, bottom)]);
                    const card = el.closest('[data-asset-id], [data-block=\"media-card\"]');
                    const aid = (card && (card.getAttribute('data-asset-id') || '')) || '';
                    if (aid) assetIds.push(aid);
                    const w = Math.round(r.width);
                    // track max photo width (logical)
                    el._w = w;
                  }
                  ranges.sort((a, b) => a[0] - b[0]);
                  const merged = [];
                  for (const [a, b] of ranges) {
                    if (!merged.length || a > merged[merged.length - 1][1]) {
                      merged.push([a, b]);
                    } else {
                      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], b);
                    }
                  }
                  let photoPx = 0;
                  for (const [a, b] of merged) photoPx += Math.max(0, b - a);
                  const nonPhotoPx = Math.max(0, scrollH - photoPx);
                  const chrome = {};
                  for (const [key, sel] of Object.entries(chromeSelectors)) {
                    let h = 0;
                    let n = 0;
                    document.querySelectorAll(sel).forEach((el) => {
                      const r = el.getBoundingClientRect();
                      h += Math.max(0, r.height);
                      n += 1;
                    });
                    chrome[key] = { count: n, totalHeightCss: Math.round(h) };
                  }
                  const chapterHeaders = Array.from(
                    document.querySelectorAll('.chapter-header h2, [data-block=\"chapter-header\"] h2')
                  ).map((el) => (el.textContent || '').trim());
                  const coverTitles = Array.from(
                    document.querySelectorAll('.cover-opening__title, .cover-closing__title')
                  ).map((el) => (el.textContent || '').trim()).filter(Boolean);
                  const titleCounts = {};
                  for (const t of coverTitles) titleCounts[t] = (titleCounts[t] || 0) + 1;
                  const assetCount = {};
                  for (const a of assetIds) assetCount[a] = (assetCount[a] || 0) + 1;
                  const reused = Object.entries(assetCount).filter(([, c]) => c > 1);
                  const widths = uniq.map((el) => Math.round(el.getBoundingClientRect().width));
                  const maxPhotoW = widths.length ? Math.max(...widths) : 0;
                  const chapters = document.querySelectorAll('section.chapter').length;
                  const screens = document.querySelectorAll(
                    '.layout-screen, [data-block=\"layout-screen\"], .media-card[data-group-id]'
                  ).length;
                  return {
                    captureWidth,
                    scrollHeightCss: Math.round(scrollH),
                    photoVerticalPx: Math.round(photoPx),
                    nonPhotoVerticalPx: Math.round(nonPhotoPx),
                    nonPhotoVerticalRatio: nonPhotoPx / scrollH,
                    photoElementCount: uniq.length,
                    chapterCount: chapters,
                    screenishCount: screens,
                    chapterHeaderHeights: chrome.chapterHeader,
                    chapterHeaders,
                    coverTitleOccurrences: coverTitles,
                    coverTitleDupMax: Math.max(0, ...Object.values(titleCounts), 0),
                    reusedAssetCount: reused.length,
                    reusedAssets: reused.slice(0, 12).map(([id, c]) => ({ id, count: c })),
                    uniquePhotoAssetIds: Object.keys(assetCount).length,
                    maxPhotoWidthCss: maxPhotoW,
                    chrome,
                  };
                }""",
                {
                    "photoSelectors": list(PHOTO_SELECTORS),
                    "chromeSelectors": CHROME_SELECTORS,
                    "captureWidth": CAPTURE_WIDTH,
                },
            )
            browser.close()
    finally:
        server.shutdown()

    trip_json = trip_dir / "trip.json"
    meta: dict[str, Any] = {}
    if trip_json.is_file():
        try:
            data = json.loads(trip_json.read_text(encoding="utf-8"))
            m = data.get("meta") or {}
            meta = {
                "tripId": data.get("tripId") or trip_dir.name,
                "title": m.get("displayTitle") or m.get("title"),
                "assetCount": len(data.get("assets") or []),
            }
        except (OSError, json.JSONDecodeError):
            meta = {"tripId": trip_dir.name}

    metrics["trip"] = meta
    metrics["tripDir"] = str(trip_dir.resolve())
    metrics["source"] = "index-longshot.html"
    metrics["method"] = "playwright-y-union-css-px"
    metrics["note"] = (
        "非照片纵向占比 = 1 − (照片元素 Y 并集高度 / main.scrollHeight)；"
        "逻辑宽 428；与 PNG 逐行扫描同构（CSS px）"
    )
    return metrics


def format_markdown(m: dict[str, Any]) -> str:
    trip = m.get("trip") or {}
    ratio = float(m.get("nonPhotoVerticalRatio") or 0)
    hdr = m.get("chapterHeaderHeights") or {}
    lines = [
        f"# 长图归因表 · {trip.get('tripId') or Path(m.get('tripDir') or '').name}",
        "",
        f"- **展示名**：{trip.get('title') or '—'}",
        f"- **样本**：`{m.get('tripDir')}` · `{m.get('source')}`",
        f"- **方法**：{m.get('method')} · 逻辑宽 {m.get('captureWidth')}px",
        f"- **资产数（trip.json）**：{trip.get('assetCount')}",
        "",
        "## 纵向像素",
        "",
        "| 指标 | 值 |",
        "|------|-----|",
        f"| main 滚动高（CSS px） | {m.get('scrollHeightCss')} |",
        f"| 照片 Y 并集高 | {m.get('photoVerticalPx')} |",
        f"| 非照片纵向高 | {m.get('nonPhotoVerticalPx')} |",
        f"| **非照片纵向占比** | **{ratio:.1%}** |",
        f"| 照片元素数 | {m.get('photoElementCount')} |",
        f"| 最大照片宽（CSS） | {m.get('maxPhotoWidthCss')} |",
        f"| 章数 | {m.get('chapterCount')} |",
        "",
        "## 密度杠杆（默认档基线）",
        "",
        "| 杠杆 | 观测 |",
        "|------|------|",
        f"| 章头带 | count={hdr.get('count')} · Σheight≈{hdr.get('totalHeightCss')}px |",
        f"| 章名列表 | {', '.join(m.get('chapterHeaders') or []) or '—'} |",
        f"| 封面题名出现次数 | {len(m.get('coverTitleOccurrences') or [])} · maxDup={m.get('coverTitleDupMax')} |",
        f"| 封面题名文本 | {m.get('coverTitleOccurrences')} |",
        f"| 复用资产（>1 次入屏） | {m.get('reusedAssetCount')} / unique={m.get('uniquePhotoAssetIds')} |",
        "| 屏缝 | 合同保持 4px（CSS `--longshot-gap` / journal） |",
        "",
        "## 处方对照（D-SFI-11）",
        "",
        "| 杠杆 | 默认档现状 | 紧凑档处方 |",
        "|------|------------|------------|",
        "| 章头带 | 每章全头（见 Σheight） | 首章全头；第 2 章起 ≤48px |",
        "| 封面文案 | 题名重复见 maxDup | 题名/日期各一次 |",
        "| moment 复用 | reusedAssetCount | 代表图 + N 徽标 |",
        "| 屏缝 | 4px | **保持 4px** |",
        "",
        f"> {m.get('note')}",
        "",
    ]
    return "\n".join(lines)


def format_compare(baseline: dict[str, Any], current: dict[str, Any]) -> str:
    """QA-SFI-06 · before/after compact comparison (AC-SFI-12)."""
    b = float(baseline.get("nonPhotoVerticalRatio") or 0)
    c = float(current.get("nonPhotoVerticalRatio") or 0)
    drop = (b - c) / b if b > 0 else 0.0
    target = b * 0.6  # ≥40% relative drop → ≤ 60% of baseline
    ok = c <= target + 1e-9 if b > 0 else False
    return "\n".join(
        [
            "# 紧凑档前后对比 · QA-SFI-06",
            "",
            f"- **基线册**：`{baseline.get('tripDir')}`",
            f"- **当前册**：`{current.get('tripDir')}`",
            "",
            "| 指标 | 基线（默认） | 当前 |",
            "|------|-------------|------|",
            f"| 非照片纵向占比 | {b:.1%} | {c:.1%} |",
            f"| 相对降幅 | — | {drop:.1%} |",
            f"| AC-SFI-12 目标（基线×0.6） | — | ≤{target:.1%} |",
            f"| **脚本门** | — | {'✅ 通过' if ok else '❌ 未达'} |",
            "",
            "> 盲评仍须另附 5 席表（敢发偏好 ≥3/5）。",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trip_dir", type=Path, help="Trip directory with index-longshot.html")
    ap.add_argument("--json", action="store_true", help="Print JSON instead of markdown")
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Write markdown (and .json sidecar) to this path",
    )
    ap.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Prior attribution JSON (or trip dir) for compact before/after compare",
    )
    args = ap.parse_args(argv)
    trip_dir = args.trip_dir.resolve()
    metrics = measure_trip(trip_dir)
    compare_md = ""
    if args.baseline:
        base_path = args.baseline.resolve()
        if base_path.is_dir():
            baseline = measure_trip(base_path)
        else:
            baseline = json.loads(base_path.read_text(encoding="utf-8"))
        compare_md = format_compare(baseline, metrics)
        metrics["compare"] = {
            "baselineRatio": baseline.get("nonPhotoVerticalRatio"),
            "currentRatio": metrics.get("nonPhotoVerticalRatio"),
            "relativeDrop": (
                (
                    float(baseline.get("nonPhotoVerticalRatio") or 0)
                    - float(metrics.get("nonPhotoVerticalRatio") or 0)
                )
                / float(baseline.get("nonPhotoVerticalRatio") or 1)
                if float(baseline.get("nonPhotoVerticalRatio") or 0) > 0
                else None
            ),
        }
    if args.json and not args.out:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0
    md = format_markdown(metrics)
    if compare_md:
        md = compare_md + "\n---\n\n" + md
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        side = args.out.with_suffix(".json")
        side.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.out} and {side}", file=sys.stderr)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
