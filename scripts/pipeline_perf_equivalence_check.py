#!/usr/bin/env python3
"""Pipeline Perf V1 · AC-PPF-07a E-A equivalence gate.

Compares decision-critical fingerprints between two runs with identical E-B
knobs (face_detect_max_edge / webp_method / webp_pyramid) while toggling E-A
items (deferred derivatives, scan peek, worker signals, parallel ingest plan).

Default mode: self-reflexivity on a tiny synthetic album (CI-safe).
Optional: ``--baseline-trip`` / ``--candidate-trip`` for offline golden diffs.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class PerfEqReport:
    name: str
    ok: bool
    diffs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "diffs": self.diffs,
            "notes": self.notes,
        }


def ea_fingerprint(trip: dict) -> dict[str, Any]:
    """Decision-critical fields for AC-PPF-07a (cull / structure / cover / NIMA)."""
    assets = [a for a in (trip.get("assets") or []) if isinstance(a, dict)]
    asset_rows = []
    for a in sorted(assets, key=lambda x: str(x.get("id") or "")):
        q = a.get("quality") if isinstance(a.get("quality"), dict) else {}
        ae = q.get("aesthetic") if isinstance(q.get("aesthetic"), dict) else {}
        sig = ae.get("signals") if isinstance(ae.get("signals"), dict) else {}
        asset_rows.append(
            {
                "id": a.get("id"),
                "contentSig": a.get("contentSig"),
                "mediaClass": a.get("mediaClass"),
                "layoutEligible": a.get("layoutEligible"),
                "excludedLowRes": bool(q.get("excludedLowRes")),
                "learnedAesthetic": sig.get("learnedAesthetic"),
                "learnedMetric": sig.get("learnedMetric"),
                "aestheticOverall": ae.get("overall"),
            }
        )
    chapters = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        screens = []
        for sc in ch.get("screens") or []:
            if not isinstance(sc, dict):
                continue
            slots = []
            for sl in sc.get("slots") or []:
                if isinstance(sl, dict) and sl.get("assetId"):
                    slots.append(str(sl["assetId"]))
            screens.append(
                {
                    "patternId": sc.get("patternId"),
                    "assetIds": slots,
                }
            )
        item_ids: list[str] = []
        for item in ch.get("items") or []:
            if not isinstance(item, dict):
                continue
            if item.get("assetId"):
                item_ids.append(str(item["assetId"]))
            for sub in item.get("assetIds") or []:
                item_ids.append(str(sub))
        chapters.append(
            {
                "id": ch.get("id"),
                "itemAssetIds": item_ids,
                "screens": screens,
            }
        )
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    return {
        "coverAssetId": trip.get("coverAssetId"),
        "momentAssetId": trip.get("momentAssetId"),
        "closingAssetId": curation.get("closingAssetId"),
        "assets": asset_rows,
        "chapters": chapters,
    }


def diff_fingerprints(a: dict[str, Any], b: dict[str, Any], *, prefix: str = "") -> list[str]:
    diffs: list[str] = []
    if a.keys() != b.keys():
        diffs.append(f"{prefix}keys {sorted(a.keys())} != {sorted(b.keys())}")
        return diffs
    for key in sorted(a.keys()):
        path = f"{prefix}{key}"
        va, vb = a[key], b[key]
        if isinstance(va, dict) and isinstance(vb, dict):
            diffs.extend(diff_fingerprints(va, vb, prefix=path + "."))
        elif isinstance(va, list) and isinstance(vb, list):
            if len(va) != len(vb):
                diffs.append(f"{path}: len {len(va)} != {len(vb)}")
                continue
            for i, (xa, xb) in enumerate(zip(va, vb, strict=False)):
                if isinstance(xa, dict) and isinstance(xb, dict):
                    diffs.extend(diff_fingerprints(xa, xb, prefix=f"{path}[{i}]."))
                elif xa != xb:
                    diffs.append(f"{path}[{i}]: {xa!r} != {xb!r}")
        elif va != vb:
            diffs.append(f"{path}: {va!r} != {vb!r}")
    return diffs


def _ea_base_config(*, deferred: bool, parallel: bool) -> Any:
    from dataclasses import replace

    from travelogue.config import (
        AestheticConfig,
        AppConfig,
        IngestConfig,
        PipelineConfig,
        VisionConfig,
    )

    base = AppConfig()
    # Lock E-B knobs identical on both sides (D1).
    ingest = replace(
        base.ingest,
        webp_method=2,
        face_detect_max_edge=1024,
        webp_pyramid=False,
        webp_widths=(800, 1600, 2400, 3200),
        webp_ingest_widths=(800, 1600),
        detect_faces=False,
        generate_crops=False,
        webp_quality=82,
    )
    pipeline = replace(
        base.pipeline,
        deferred_derivatives=deferred,
        parallel_ingest=parallel,
        parallel_ingest_workers=2 if parallel else 1,
        parallel_ingest_min_photos=2,
        parallel_embed=False,
    )
    aesthetic = replace(
        base.aesthetic,
        enabled=True,
        ml_calibrate=False,  # CI may lack pyiqa; rules path only
        warm_learned_on_ingest=False,
    )
    return replace(
        base,
        ingest=ingest,
        pipeline=pipeline,
        aesthetic=aesthetic,
        vision=VisionConfig(enabled="false"),
    )


def _run_synthetic(tmp: Path, *, deferred: bool, parallel: bool) -> dict:
    from PIL import Image

    from travelogue.media.ingest import ingest_into_trip
    from travelogue.services.trip_factory import create_trip

    album = tmp / ("album-def" if deferred else "album-full")
    album.mkdir(parents=True, exist_ok=True)
    for i in range(4):
        Image.new("RGB", (1600, 1200), (20 * i, 60, 100)).save(
            album / f"p{i}.jpg", quality=90
        )
    trip_json = create_trip(
        "ppf-ea-" + ("d" if deferred else "f"),
        tmp / "trips",
        title="ppf-ea",
    )
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = _ea_base_config(deferred=deferred, parallel=parallel)
    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=cfg,
        min_assets=4,
        dedupe=False,
    )
    # Minimal structure so selected_asset_ids / chapter fingerprint are defined
    ids = [a["id"] for a in trip["assets"]]
    trip["coverAssetId"] = ids[0]
    trip["chapters"] = [
        {
            "id": "ch-1",
            "items": [{"assetId": i} for i in ids],
            "screens": [
                {
                    "patternId": "single",
                    "slots": [{"assetId": ids[0]}],
                }
            ],
        }
    ]
    return trip


def run_self_check(work: Path) -> PerfEqReport:
    """E-A deferred ON vs OFF with locked E-B — ingest fingerprints must match."""
    a = _run_synthetic(work / "a", deferred=True, parallel=False)
    b = _run_synthetic(work / "b", deferred=False, parallel=False)
    fa, fb = ea_fingerprint(a), ea_fingerprint(b)
    # srcset widths differ by design under deferred; strip file-dependent noise
    # by only comparing decision fields in ea_fingerprint (already stripped).
    diffs = diff_fingerprints(fa, fb)
    return PerfEqReport(
        name="ea-deferred-on-vs-off",
        ok=not diffs,
        diffs=diffs[:50],
        notes=["E-B locked; aesthetic ml off for CI"],
    )


def run_trip_pair(baseline: Path, candidate: Path) -> PerfEqReport:
    a = json.loads(baseline.read_text(encoding="utf-8"))
    b = json.loads(candidate.read_text(encoding="utf-8"))
    diffs = diff_fingerprints(ea_fingerprint(a), ea_fingerprint(b))
    return PerfEqReport(
        name=f"{baseline.name} vs {candidate.name}",
        ok=not diffs,
        diffs=diffs[:80],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-trip", type=Path, default=None)
    parser.add_argument("--candidate-trip", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--work", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.baseline_trip and args.candidate_trip:
        report = run_trip_pair(args.baseline_trip, args.candidate_trip)
    else:
        import tempfile

        work = args.work or Path(tempfile.mkdtemp(prefix="ppf-ea-"))
        work.mkdir(parents=True, exist_ok=True)
        report = run_self_check(work)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"{report.name}: {'OK' if report.ok else 'FAIL'}")
        for d in report.diffs[:20]:
            print(f"  - {d}")
        for n in report.notes:
            print(f"  note: {n}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
