#!/usr/bin/env python3
"""LRG dogfood acceptance report (T-LRG-03 · docs/PRD-LAYOUT-READER-REGRESSION-GUARD.md §3.3.4).

Computes the P0 dogfood JSON schema for a single rendered trip: screen-count
parity between trip.json and the rendered index.html, overlay-selector
presence counts (EXIF / ticket), and mosaic window exposure / burst-pass rate
from curation.mosaicDecisionLog.

Usage:
  python scripts/lrg_dogfood_report.py --trip trips/demo-815dc906d3
  python scripts/lrg_dogfood_report.py --trip trips/demo-815dc906d3 \
      --out docs/acceptance-records/lrg-dogfood.demo-815dc906d3.json
  python scripts/lrg_dogfood_report.py --trip trips/linzhi --html trips/linzhi/index.html
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: Structural/decorative screen kinds present in chapters[].screens that do
#: NOT render as a standalone `.layout-screen` element (they render with a
#: different wrapper class, e.g. `.breath-pause-screen`). Excluded from
#: `screenCount` so it is directly comparable to `htmlLayoutScreenCount`
#: (G-LRG-05); see PRD §3.3.1 "112↔140 屏同步" note for demo-815dc906d3.
_NON_LAYOUT_SCREEN_PATTERNS = frozenset({"screen-breath-pause"})

_LAYOUT_SCREEN_CLASS_RE = re.compile(r'class="[^"]*\blayout-screen\b(?!__|--)[^"]*"')
_MOMENT_EXIF_BAR_RE = re.compile(r"moment-exif-bar")
_CHAPTER_TICKET_RE = re.compile(r"chapter-separator--ticket")

#: 1P+NL mosaic window geometry scanned for burstPassRate (PRD §3.3.4).
#: window_len 5 == 1 portrait + 4 landscape (mosaic-5 main-portrait-3land);
#: window_len 6 == 1 portrait + 5 landscape (mosaic-6 hero-plus family).
_BURST_WINDOW_LENS = (5, 6)
_WINDOW_EXPOSURE_SIZES = (4, 5, 6, 9)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_trip_paths(trip_arg: Path) -> tuple[Path | None, Path]:
    """Return (trip_json_path_or_None, trip_dir)."""
    if trip_arg.is_file():
        return trip_arg, trip_arg.parent
    trip_dir = trip_arg
    trip_json = trip_dir / "trip.json"
    return (trip_json if trip_json.is_file() else None), trip_dir


def _aspect_family(kind: str) -> str:
    if kind in ("portrait", "tall"):
        return "portrait"
    if kind in ("landscape", "panorama"):
        return "landscape"
    return "square"


def _ordered_asset_ids(trip: dict[str, Any]) -> list[str]:
    curation = trip.get("curation") or {}
    displayed = curation.get("displayedAssetIds")
    if isinstance(displayed, list) and displayed:
        return [str(x) for x in displayed if x]
    from travelogue.curation.burst_utils import parse_taken_ts

    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    return sorted(assets_map, key=lambda aid: parse_taken_ts(assets_map.get(aid) or {}) or 0.0)


def _burst_pass_rate(trip: dict[str, Any], *, burst_seconds: float) -> dict[str, Any]:
    """1P+4L / 1P+5L sliding-window burst pass rate (PRD §3.3.4 burstPassRate)."""
    from travelogue.curation.burst_utils import time_near_chain
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    assets = trip.get("assets") or []
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    aspects = {aid: aspect_kind_for_asset(a) for aid, a in assets_map.items()}
    ordered = _ordered_asset_ids(trip)

    by_len: dict[int, dict[str, int]] = {}
    geometry_total = 0
    pass_total = 0
    for window_len in _BURST_WINDOW_LENS:
        geometry = 0
        burst_pass = 0
        for i in range(max(0, len(ordered) - window_len + 1)):
            window = ordered[i : i + window_len]
            if len(window) < window_len:
                continue
            kinds = [_aspect_family(aspects.get(aid, "square")) for aid in window]
            n_p = sum(1 for k in kinds if k == "portrait")
            n_l = sum(1 for k in kinds if k == "landscape")
            if n_p != 1 or n_l != window_len - 1:
                continue
            geometry += 1
            if time_near_chain(window, assets_map, burst_seconds=burst_seconds):
                burst_pass += 1
        by_len[window_len] = {"geometryWindows": geometry, "burstPassWindows": burst_pass}
        geometry_total += geometry
        pass_total += burst_pass

    return {
        "burstPassRate": round(pass_total / geometry_total, 4) if geometry_total else None,
        "byWindowLen": {str(k): v for k, v in by_len.items()},
    }


def _mosaic_decision_summary(trip: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    """Returns (mosaicDecisionSummary, windowExposure) from curation.mosaicDecisionLog."""
    logs = (trip.get("curation") or {}).get("mosaicDecisionLog") or []
    by_size: dict[int, dict[str, Any]] = {}
    for raw in logs:
        if not isinstance(raw, dict):
            continue
        size = int(raw.get("windowSize") or raw.get("window_size") or 0)
        if size <= 0:
            continue
        bucket = by_size.setdefault(size, {"decisions": 0, "success": 0, "fallback": 0, "patterns": []})
        bucket["decisions"] += 1
        if raw.get("fallbackUsed"):
            bucket["fallback"] += 1
        winner = str(raw.get("winnerPatternId") or "")
        if winner and not raw.get("fallbackUsed"):
            bucket["success"] += 1
            bucket["patterns"].append(winner)

    mosaic_decision_summary = {
        str(size): {
            "decisions": b["decisions"],
            "success": b["success"],
            "fallback": b["fallback"],
            "patterns": sorted(set(b["patterns"])),
        }
        for size, b in sorted(by_size.items())
    }
    window_exposure = {str(size): by_size.get(size, {}).get("decisions", 0) for size in _WINDOW_EXPOSURE_SIZES}
    return mosaic_decision_summary, window_exposure


def _pattern_histogram(trip: dict[str, Any]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for ch in trip.get("chapters") or []:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "")
            if not pid:
                continue
            histogram[pid] = histogram.get(pid, 0) + 1
    return dict(sorted(histogram.items()))


def _trip_json_screen_count(trip: dict[str, Any]) -> int:
    count = 0
    for ch in trip.get("chapters") or []:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "")
            if pid in _NON_LAYOUT_SCREEN_PATTERNS:
                continue
            count += 1
    return count


def _html_layout_screen_count(html_text: str) -> int:
    return len(_LAYOUT_SCREEN_CLASS_RE.findall(html_text))


def _moment_exif_bar_count(html_text: str) -> int:
    return len(_MOMENT_EXIF_BAR_RE.findall(html_text))


def _chapter_separator_ticket_count(html_text: str) -> int:
    return len(_CHAPTER_TICKET_RE.findall(html_text))


def build_dogfood_report(
    trip_arg: Path,
    *,
    html_path: Path | None = None,
    burst_seconds: float | None = None,
) -> dict[str, Any]:
    """Build the LRG dogfood JSON payload (PRD §3.3.4) for one trip.

    Degrades gracefully when trip.json is unavailable (e.g. gitignored
    personal albums like trips/linzhi/ on a fresh checkout): HTML-derived
    fields are still populated and a `warnings` entry records the gap instead
    of silently reporting a fabricated screenCount (AC-LRG "don't pretend").
    """
    trip_json_path, trip_dir = _resolve_trip_paths(trip_arg)
    resolved_html_path = html_path or (trip_dir / "index.html")
    warnings: list[str] = []

    html_text = ""
    if resolved_html_path.is_file():
        html_text = resolved_html_path.read_text(encoding="utf-8")
    else:
        warnings.append(f"index.html not found at {resolved_html_path}; run render first")

    trip: dict[str, Any] | None = None
    if trip_json_path is not None:
        trip = _read_json(trip_json_path)
    else:
        warnings.append(
            f"trip.json not found under {trip_dir}; trip may be gitignored on this checkout "
            "(e.g. personal album source data) — report limited to HTML-derived fields only"
        )

    trip_id = (trip or {}).get("tripId") or trip_dir.name
    html_layout_screen_count = _html_layout_screen_count(html_text) if html_text else None
    moment_exif_bar_count = _moment_exif_bar_count(html_text) if html_text else None
    chapter_separator_ticket_count = _chapter_separator_ticket_count(html_text) if html_text else None

    screen_count: int | None = None
    pattern_histogram: dict[str, int] = {}
    mosaic_decision_summary: dict[str, Any] = {}
    window_exposure: dict[str, int] = {str(s): 0 for s in _WINDOW_EXPOSURE_SIZES}
    burst_pass_rate: float | None = None
    burst_detail: dict[str, Any] = {}

    if trip is not None:
        if burst_seconds is None:
            try:
                from travelogue.config import get_config

                burst_seconds = float(get_config().layout.mixed_proximity_seconds)
            except Exception:  # pragma: no cover - config load is best-effort here
                burst_seconds = 900.0
        screen_count = _trip_json_screen_count(trip)
        pattern_histogram = _pattern_histogram(trip)
        mosaic_decision_summary, window_exposure = _mosaic_decision_summary(trip)
        burst_result = _burst_pass_rate(trip, burst_seconds=burst_seconds)
        burst_pass_rate = burst_result["burstPassRate"]
        burst_detail = burst_result["byWindowLen"]

    if screen_count is not None and html_layout_screen_count is not None and screen_count != html_layout_screen_count:
        warnings.append(
            f"screenCount ({screen_count}) != htmlLayoutScreenCount ({html_layout_screen_count}); "
            "G-LRG-05 requires parity — re-render or investigate before treating as baseline"
        )

    return {
        "tripId": trip_id,
        "screenCount": screen_count,
        "htmlLayoutScreenCount": html_layout_screen_count,
        "patternHistogram": pattern_histogram,
        "mosaicDecisionSummary": mosaic_decision_summary,
        "momentExifBarCount": moment_exif_bar_count,
        "chapterSeparatorTicketCount": chapter_separator_ticket_count,
        "burstPassRate": burst_pass_rate,
        "burstPassRateDetail": burst_detail,
        "windowExposure": window_exposure,
        "mixedProximitySeconds": burst_seconds,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LRG dogfood acceptance report (T-LRG-03)")
    ap.add_argument("--trip", type=Path, required=True, help="trip directory or trip.json path")
    ap.add_argument("--html", type=Path, help="index.html path override (default: <trip-dir>/index.html)")
    ap.add_argument("--out", type=Path, help="write JSON report here (default: print to stdout)")
    ap.add_argument(
        "--burst-seconds",
        type=float,
        default=None,
        help="override layout.mixed_proximity_seconds for burstPassRate (default: config)",
    )
    ap.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="exit 1 when screenCount != htmlLayoutScreenCount (G-LRG-05)",
    )
    args = ap.parse_args(argv)

    report = build_dogfood_report(args.trip, html_path=args.html, burst_seconds=args.burst_seconds)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
        print(f"OK lrg dogfood report -> {args.out}")
    else:
        print(payload)

    for warning in report["warnings"]:
        print(f"::warning:: {warning}", file=sys.stderr)

    if args.fail_on_mismatch:
        sc, hc = report["screenCount"], report["htmlLayoutScreenCount"]
        if sc is not None and hc is not None and sc != hc:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
