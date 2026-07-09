#!/usr/bin/env python3
"""Architecture equivalence gate (PRD §3.2.2 · M-B0).

Compares normalized trip.json snapshots and layout signatures. Self-reflexivity
smoke: run the same deterministic pipeline twice and expect an empty diff.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_FIXTURES = (
    "golden-mixed-scenes",
    "schemas/fixtures/trip.render_golden.json",
)

_WALL_CLOCK_KEYS = frozenset({"ts", "timestamp", "wallClockMs", "wall_clock_ms", "startedAt", "finishedAt"})


@dataclass
class EquivalenceReport:
    name: str
    ok: bool
    l3a_diff: list[str] = field(default_factory=list)
    l3b_diff: list[str] = field(default_factory=list)
    layout_snapshot_a: dict[str, Any] | None = None
    layout_snapshot_b: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "l3aDiff": self.l3a_diff,
            "l3bDiff": self.l3b_diff,
            "notes": self.notes,
        }

    def summary(self) -> str:
        if self.ok:
            return "OK"
        parts = []
        if self.l3a_diff:
            parts.append(f"L3a {len(self.l3a_diff)} diff(s)")
        if self.l3b_diff:
            parts.append(f"L3b {len(self.l3b_diff)} diff(s)")
        return "FAIL: " + ", ".join(parts)


def arch_equivalent_config():
    """Deterministic profile per PRD §3.2.2 / phase7 NR collect."""
    from dataclasses import replace

    from travelogue.config import (
        AppConfig,
        ClusteringConfig,
        IngestConfig,
        LayoutScoringConfig,
        MosaicConfig,
        PipelineConfig,
        VisionConfig,
    )

    base = AppConfig()
    scoring = LayoutScoringConfig(
        incremental=False,
        skip_duplicate_signatures=False,
    )
    return replace(
        base,
        vision=VisionConfig(
            enabled="false",
            batch_size=0,
            session_singleton=False,
            prefer_web_derivative=False,
            batch_auto_tune=False,
            dynamic_backoff=False,
            prefetch=False,
        ),
        pipeline=PipelineConfig(parallel_embed=False),
        ingest=IngestConfig(webp_method=6),
        clustering=ClusteringConfig(
            enabled="true",
            deterministic=True,
            deterministic_strict=True,
        ),
        mosaic=MosaicConfig(deterministic_strict=True),
        layout=replace(base.layout, scoring=scoring),
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalize_scalar(value: Any) -> Any:
    if _is_number(value):
        rounded = round(float(value), 6)
        if math.isfinite(rounded) and abs(rounded - round(rounded)) < 1e-12:
            return int(round(rounded))
        return rounded
    return value


def _should_drop_key(path: tuple[str, ...], key: str) -> bool:
    if key in {
        "updatedAt",
        "appliedAt",
        "computedAt",
        "aestheticAlignmentAt",
        "createdAt",
        "curatedAt",
        "ingestedAt",
        "submittedAt",
    }:
        return True
    if key == "ingestBatchId":
        return True
    if key == "lastBatchId" and path == ("pipeline",):
        return True
    if key == "revision" and path == ("meta",):
        return True
    if key == "runId" and "runs" in path:
        return True
    if key == "timings" and path == ("pipeline",):
        return True
    if key == "weightsHash":
        return True
    if key.endswith("Ms") and path and path[0] in {"pipeline", "curation"}:
        return True
    if key == "screenId" and "screens" in path:
        return True
    if key in _WALL_CLOCK_KEYS and path[:2] == ("pipeline", "runs"):
        return True
    if key == "elapsedMs" and path[-2:] == ("embedStats",):
        return True
    if key == "ts" and len(path) >= 2 and path[-2] == "decisionLog":
        return True
    return False


def _normalize_node(value: Any, path: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _should_drop_key(path, str(key)):
                continue
            out[str(key)] = _normalize_node(item, path + (str(key),))
        return out
    if isinstance(value, list):
        return [_normalize_node(item, path + (str(index),)) for index, item in enumerate(value)]
    return _normalize_scalar(value)


def normalize_trip(trip: dict[str, Any]) -> dict[str, Any]:
    return _normalize_node(deepcopy(trip))


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def diff_normalized(left: dict[str, Any], right: dict[str, Any], *, limit: int = 20) -> list[str]:
    diffs: list[str] = []

    def walk(a: Any, b: Any, path: str) -> None:
        if len(diffs) >= limit:
            return
        if type(a) is not type(b):
            diffs.append(f"{path}: type {type(a).__name__} != {type(b).__name__}")
            return
        if isinstance(a, dict):
            keys = sorted(set(a) | set(b))
            for key in keys:
                child = f"{path}.{key}" if path else key
                if key not in a:
                    diffs.append(f"{child}: missing in left")
                elif key not in b:
                    diffs.append(f"{child}: missing in right")
                else:
                    walk(a[key], b[key], child)
        elif isinstance(a, list):
            if len(a) != len(b):
                diffs.append(f"{path}: list length {len(a)} != {len(b)}")
            for index, (ai, bi) in enumerate(zip(a, b)):
                walk(ai, bi, f"{path}[{index}]")
        elif a != b:
            diffs.append(f"{path}: {a!r} != {b!r}")

    walk(left, right, "")
    return diffs


def _load_trip_fixture(name: str) -> tuple[dict[str, Any], str]:
    path = Path(name)
    if path.suffix == ".json" and path.is_file():
        trip = json.loads(path.read_text(encoding="utf-8"))
        return trip, str(path)
    from scripts.phase3_ig2_report import load_fixture_trip

    return load_fixture_trip(name), f"fixture:{name}"


def _run_arch_pipeline(trip: dict[str, Any], *, work_dir: Path, label: str) -> dict[str, Any]:
    from copy import deepcopy

    from scripts.phase3_ig2_report import _prepare_trip
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    body = _prepare_trip(deepcopy(trip))
    cfg = arch_equivalent_config()
    target = work_dir / label
    target.mkdir(parents=True, exist_ok=True)
    run_clustering_layer(body, trip_dir=target, cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=target, cfg=cfg)
    return body


def check_self_reflexivity(name: str, *, work_dir: Path) -> EquivalenceReport:
    from tests._golden.helpers import layout_snapshot

    trip, source = _load_trip_fixture(name)
    if trip.get("chapters") and source.endswith("trip.render_golden.json"):
        left = normalize_trip(trip)
        right = normalize_trip(deepcopy(trip))
        snap = layout_snapshot(trip.get("chapters") or [])
        report = EquivalenceReport(name=name, ok=True, layout_snapshot_a=snap, layout_snapshot_b=snap)
        report.l3a_diff = diff_normalized(left, right)
        report.ok = not report.l3a_diff
        report.notes.append("static fixture: normalized duplicate + layout snapshot")
        return report

    run_a = _run_arch_pipeline(trip, work_dir=work_dir, label="run-a")
    run_b = _run_arch_pipeline(trip, work_dir=work_dir, label="run-b")
    norm_a = normalize_trip(run_a)
    norm_b = normalize_trip(run_b)
    snap_a = layout_snapshot(run_a.get("chapters") or [])
    snap_b = layout_snapshot(run_b.get("chapters") or [])
    report = EquivalenceReport(
        name=name,
        ok=True,
        layout_snapshot_a=snap_a,
        layout_snapshot_b=snap_b,
    )
    report.l3a_diff = diff_normalized(norm_a, norm_b)
    if snap_a != snap_b:
        report.l3b_diff.append("layout_snapshot mismatch")
    report.ok = not report.l3a_diff and not report.l3b_diff
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Architecture equivalence check (PRD §3.2.2)")
    parser.add_argument(
        "fixtures",
        nargs="*",
        default=list(DEFAULT_FIXTURES),
        help="clustering fixture id or path to trip.json",
    )
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "arch-equivalence")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    reports: list[EquivalenceReport] = []
    for fixture in args.fixtures:
        path = Path(fixture)
        if path.suffix == ".json" and not path.is_absolute():
            candidate = ROOT / fixture
            fixture_name = str(candidate) if candidate.is_file() else fixture
        else:
            fixture_name = fixture
        reports.append(check_self_reflexivity(fixture_name, work_dir=args.work_dir / path.stem))

    payload = {"ok": all(r.ok for r in reports), "reports": [r.to_dict() for r in reports]}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            print(f"{report.summary()} {report.name}")
            for line in report.l3a_diff + report.l3b_diff:
                print(f"  - {line}")
        print("arch_equivalence_check: OK" if payload["ok"] else "arch_equivalence_check: FAIL")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
