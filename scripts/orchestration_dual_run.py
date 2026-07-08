#!/usr/bin/env python3
"""Dual-run pipeline.orchestration paths (PRD §3.3 · M-B3 DoD).

Phase 1 (AC-ARC-06v2): legacy Studio path vs unified Studio path.
Phase 2 (AC-ARC-06v2): unified Studio path vs CLI-equivalent run_trip chain.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EQUIV_TITLE = "orch-equiv"
EQUIV_TRIP_ID = "orch-equiv"


def _arch_studio_config(*, orchestration: str):
    from scripts.arch_equivalence_check import arch_equivalent_config

    base = arch_equivalent_config()
    return replace(
        base,
        pipeline=replace(base.pipeline, orchestration=orchestration, parallel_embed=False),
    )


def _make_album(work_dir: Path, n: int = 8) -> Path:
    from tests.studio_test_helpers import make_test_album

    return make_test_album(work_dir, n)


def _run_studio_import(
    album: Path,
    *,
    orchestration: str,
    work_dir: Path,
    stop_after: str = "full",
) -> dict:
    from scripts.arch_equivalence_check import normalize_trip
    from travelogue.web.studio_pipeline import run_studio_pipeline

    cfg = _arch_studio_config(orchestration=orchestration)
    trips_dir = work_dir / orchestration / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        trip_id=EQUIV_TRIP_ID,
        title=EQUIV_TITLE,
        dedupe=False,
        force=True,
        app_config=cfg,
        stop_after=stop_after,
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    return normalize_trip(trip)


def _run_cli_equivalent(album: Path, *, work_dir: Path) -> dict:
    """run_trip chain mirroring unified Studio (ingest → featured → clustering → curate)."""
    from scripts.arch_equivalence_check import normalize_trip
    from travelogue.curation.layout_density import resolve_import_layout_density
    from travelogue.orchestrator.run import run_trip
    from travelogue.orchestrator.studio_profile import StudioProfile
    from travelogue.services.trip import apply_intent
    from travelogue.services.trip_factory import create_trip
    from travelogue.web.studio_pipeline import _apply_featured_detected_intent

    cfg = _arch_studio_config(orchestration="unified")
    trips_dir = work_dir / "cli-equiv" / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    trip_json = create_trip(
        EQUIV_TRIP_ID,
        trips_dir,
        title=EQUIV_TITLE,
        place="旅途",
        export_layout="auto",
        cfg=cfg,
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    apply_intent(
        trip,
        title=EQUIV_TITLE,
        layout_density=resolve_import_layout_density(None, import_mode="quick_share", app_cfg=cfg),
        photo_cull_enabled=True,
        keep_near_duplicates=False,
    )
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    profile = StudioProfile.studio_default()
    profile.ingest.use_parallel_embed = False
    profile.ingest.max_photos = cfg.ingest.max_photos

    ingest_stats: dict = {}

    def capture_stats(stats: dict) -> None:
        ingest_stats.update(stats)

    profile.ingest.on_complete = capture_stats

    run_trip(
        trip_json,
        from_stage="ingest",
        until="ingest",
        album_dir=album,
        dedupe=False,
        validate=False,
        cfg=cfg,
        studio_profile=profile,
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    _apply_featured_detected_intent(trip, ingest_stats)
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    run_trip(
        trip_json,
        from_stage="clustering",
        until="structure",
        dedupe=False,
        validate=False,
        cfg=cfg,
        studio_profile=profile,
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    return normalize_trip(trip)


def compare_phase1(*, work_dir: Path, album: Path) -> dict:
    from scripts.arch_equivalence_check import diff_normalized
    from tests._golden.helpers import layout_snapshot

    legacy = _run_studio_import(album, orchestration="legacy", work_dir=work_dir / "phase1")
    unified = _run_studio_import(album, orchestration="unified", work_dir=work_dir / "phase1")
    l3a = diff_normalized(legacy, unified)
    snap_l = layout_snapshot(legacy.get("chapters") or [])
    snap_u = layout_snapshot(unified.get("chapters") or [])
    l3b_ok = snap_l == snap_u
    return {
        "phase": "legacy_vs_unified",
        "ok": not l3a and l3b_ok,
        "l3aDiff": l3a,
        "l3bOk": l3b_ok,
    }


def compare_phase2(*, work_dir: Path, album: Path) -> dict:
    from scripts.arch_equivalence_check import diff_normalized
    from tests._golden.helpers import layout_snapshot

    unified = _run_studio_import(
        album,
        orchestration="unified",
        work_dir=work_dir / "phase2",
        stop_after="structure",
    )
    cli = _run_cli_equivalent(album, work_dir=work_dir / "phase2")
    l3a = diff_normalized(unified, cli)
    snap_u = layout_snapshot(unified.get("chapters") or [])
    snap_c = layout_snapshot(cli.get("chapters") or [])
    l3b_ok = snap_u == snap_c
    return {
        "phase": "unified_vs_cli",
        "ok": not l3a and l3b_ok,
        "l3aDiff": l3a,
        "l3bOk": l3b_ok,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dual-run pipeline.orchestration equivalence")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "orchestration-dual")
    parser.add_argument("--phase", choices=("1", "2", "all"), default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    args.work_dir.mkdir(parents=True, exist_ok=True)
    album = _make_album(args.work_dir / "album")

    reports: list[dict] = []
    if args.phase in ("1", "all"):
        reports.append(compare_phase1(work_dir=args.work_dir, album=album))
    if args.phase in ("2", "all"):
        reports.append(compare_phase2(work_dir=args.work_dir, album=album))

    payload = {"ok": all(r["ok"] for r in reports), "reports": reports}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            status = "OK" if report["ok"] else "FAIL"
            print(f"{status} phase={report['phase']}")
            for line in report.get("l3aDiff") or []:
                print(f"  L3a: {line}")
            if not report.get("l3bOk"):
                print("  L3b: layout_snapshot mismatch")
        print("orchestration_dual_run: OK" if payload["ok"] else "orchestration_dual_run: FAIL")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
