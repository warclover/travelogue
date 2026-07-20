#!/usr/bin/env python3
"""LTN R-A4 · evidence baseline: debug re-curate + window signature scan.

Works on deep copies; does not write trips/*/trip.json.
Output: .cache/ltn-evidence/report.json (+ per-trip mosaic logs).

Usage:
  python scripts/ltn_evidence_baseline.py
  python scripts/ltn_evidence_baseline.py demo-2025 --out-dir .cache/ltn-evidence
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import traceback
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_TARGETS = (
    "demo-65db8fd377",
    "demo-eb9a45b3c4",
    "demo-2025",
    "demo-815dc906d3",
)
# LTN H9 · CI-safe fixtures when local demo trips are absent.
H9_FIXTURE_TARGETS = (
    "tests/fixtures/ltn/trip.ltn_oracle_positive.json",
    "tests/fixtures/ltn/trip.ltn_oracle_negative.json",
)


def _aspect_family(kind: str) -> str:
    if kind in ("portrait", "tall"):
        return "portrait"
    if kind in ("landscape", "panorama"):
        return "landscape"
    return "square"


def prepare(trip: dict) -> dict:
    body = copy.deepcopy(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    cur = body.setdefault("curation", {})
    for k in (
        "layoutMetrics",
        "mosaicDecisionLog",
        "displayedAssetIds",
        "layoutDecisionLog",
    ):
        cur.pop(k, None)
    return body


def pattern_counter(trip: dict) -> Counter:
    c: Counter = Counter()
    for ch in trip.get("chapters") or []:
        for s in ch.get("screens") or []:
            c[str(s.get("patternId") or "?")] += 1
    return c


def aggregate_mosaic_log(logs: list) -> dict:
    agg: dict = {
        "entries": len(logs),
        "by_window": {},
        "fallback_reasons": Counter(),
        "planner_paths": Counter(),
        "winners": Counter(),
        "rejected_reasons": Counter(),
        "rejected_templates": Counter(),
    }
    for raw in logs:
        if not isinstance(raw, dict):
            continue
        size = int(raw.get("windowSize") or raw.get("window_size") or 0)
        b = agg["by_window"].setdefault(
            size, {"decisions": 0, "winners": 0, "fallbacks": 0}
        )
        b["decisions"] += 1
        if raw.get("fallbackUsed"):
            b["fallbacks"] += 1
            agg["fallback_reasons"][str(raw.get("fallbackReason") or "?")] += 1
        if raw.get("winnerPatternId"):
            b["winners"] += 1
            agg["winners"][str(raw["winnerPatternId"])] += 1
        if raw.get("plannerPath"):
            agg["planner_paths"][str(raw["plannerPath"])] += 1
        for rt in raw.get("rejectedTemplates") or []:
            if isinstance(rt, dict):
                agg["rejected_reasons"][str(rt.get("reason") or "?")] += 1
                agg["rejected_templates"][
                    str(rt.get("patternId") or rt.get("templateId") or "?")
                ] += 1
    for k in (
        "fallback_reasons",
        "planner_paths",
        "winners",
        "rejected_reasons",
        "rejected_templates",
    ):
        agg[k] = dict(agg[k].most_common())
    return agg


def signature_scan(trip: dict, burst_seconds: float) -> dict:
    from travelogue.curation.burst_utils import parse_taken_ts, time_near_chain
    from travelogue.curation.layout_planner import aspect_kind_for_asset

    assets = trip.get("assets") or []
    amap = {str(a["id"]): a for a in assets if a.get("id")}
    aspects = {aid: _aspect_family(aspect_kind_for_asset(a)) for aid, a in amap.items()}
    cur = trip.get("curation") or {}
    ordered = [str(x) for x in (cur.get("displayedAssetIds") or []) if str(x) in amap]
    if not ordered:
        ordered = sorted(amap, key=lambda i: parse_taken_ts(amap[i]) or 0.0)

    out: dict = {
        "orderedCount": len(ordered),
        "portraitCount": sum(1 for a in aspects.values() if a == "portrait"),
        "landscapeCount": sum(1 for a in aspects.values() if a == "landscape"),
    }
    for size in (4, 5):
        sig: Counter = Counter()
        cohesive: Counter = Counter()
        for i in range(max(0, len(ordered) - size + 1)):
            w = ordered[i : i + size]
            kinds = [aspects.get(x, "square") for x in w]
            key = f"{kinds.count('portrait')}P{kinds.count('landscape')}L"
            sig[key] += 1
            if time_near_chain(w, amap, burst_seconds=burst_seconds):
                cohesive[key] += 1
        out[f"win{size}_signatures"] = dict(sig.most_common())
        out[f"win{size}_cohesive"] = dict(cohesive.most_common())
    bg: Counter = Counter()
    for a in assets:
        gid = a.get("burstGroupId")
        if gid:
            bg[str(gid)] += 1
    out["burstGroups"] = {
        "groups": len(bg),
        "assetsInBursts": sum(bg.values()),
        "groupsGe4": sum(1 for v in bg.values() if v >= 4),
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="LTN R-A4 evidence baseline")
    parser.add_argument("targets", nargs="*", default=list(DEFAULT_TARGETS))
    parser.add_argument(
        "--trips-dir", type=Path, default=ROOT / "trips"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=ROOT / ".cache" / "ltn-evidence"
    )
    args = parser.parse_args()

    from travelogue.config import get_config
    from travelogue.config.runtime import config_override
    from travelogue.curation.curate import run_curate

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cfg = get_config()
    cfg_dbg = replace(cfg, mosaic=replace(cfg.mosaic, log_level="debug"))
    burst_seconds = float(cfg.layout.mixed_proximity_seconds)

    targets = list(args.targets)
    # Prefer demos when present; otherwise fall back to H9 fixtures (R-A4/H9).
    if all(not (args.trips_dir / tid / "trip.json").is_file() for tid in targets):
        targets = list(H9_FIXTURE_TARGETS)

    report: dict = {"burstSeconds": burst_seconds, "trips": {}}
    for tid in targets:
        tj = Path(tid)
        if not tj.is_absolute():
            # Allow "demo-*" under trips/ or a direct fixture path.
            cand = args.trips_dir / tid / "trip.json"
            if cand.is_file():
                tj = cand
            else:
                tj = ROOT / tid
        if not tj.is_file():
            print(f"SKIP {tid}: no trip.json", flush=True)
            continue
        label = tj.stem if "fixtures" in tj.as_posix() else str(tid)
        print(f"=== {label} ===", flush=True)
        trip = json.loads(tj.read_text(encoding="utf-8"))
        row: dict = {
            "before_patterns": dict(pattern_counter(trip).most_common()),
            "signature_scan": signature_scan(trip, burst_seconds),
            "appliedLayoutDensity": (trip.get("curation") or {}).get(
                "appliedLayoutDensity"
            ),
        }
        body = prepare(trip)
        try:
            with config_override(cfg_dbg):
                run_curate(
                    body,
                    apply_layout=True,
                    trip_dir=args.out_dir / label,
                    cfg=cfg_dbg,
                )
            logs = (body.get("curation") or {}).get("mosaicDecisionLog") or []
            row["after_patterns"] = dict(pattern_counter(body).most_common())
            row["mosaic_log"] = aggregate_mosaic_log(logs)
            (args.out_dir / f"{label}-mosaic-log.json").write_text(
                json.dumps(logs, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(
                f"  recurate ok: screens={sum(row['after_patterns'].values())} "
                f"logEntries={len(logs)}",
                flush=True,
            )
        except Exception as exc:
            row["recurate_error"] = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        report["trips"][label] = row

    out = args.out_dir / "report.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {out}", flush=True)
    return 0 if report["trips"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
