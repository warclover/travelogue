"""ALG-V3 blind dogfood · run one On/Off arm and snapshot HTML + algoV3."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from travelogue.config import app_config_scope, get_config
from travelogue.config.loader import load_config
from travelogue.curation.algo_v3_summary import attach_algo_v3_summary
from travelogue.render.engine import render_trip
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.layout import apply_layout_to_trip
from travelogue.services.trip import persist_trip_snapshot

ROOT = Path("docs/acceptance-records/attachments/alg3-blind-2026-08-02")
TRIP_ID = "demo-3ee2727aea"


def _pattern_fingerprint(trip: dict) -> list[str]:
    out: list[str] = []
    for ch in trip.get("chapters") or []:
        for it in ch.get("items") or []:
            if not isinstance(it, dict):
                continue
            pid = it.get("patternId") or it.get("layoutHint") or it.get("type")
            aids = it.get("assetIds") or ([it.get("assetId")] if it.get("assetId") else [])
            out.append(f"{pid}:{','.join(str(a) for a in aids if a)}")
    return out


def run_arm(arm: str, cfg_path: Path) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    trip_path = Path("trips") / TRIP_ID / "trip.json"
    svc = app_context_for_trip_json(trip_path).trip_service()
    trip = svc.load(trip_path)
    cfg = load_config(cfg_path)
    with app_config_scope(cfg):
        apply_layout_to_trip(trip, export_layout="web", cfg=get_config())
        summary = attach_algo_v3_summary(trip, cfg=get_config())
        persist_trip_snapshot(svc, trip_path, trip)
        render_trip(trip_path, trip_path.parent, export_mode="draft", validate=False)

    fp = _pattern_fingerprint(trip)
    payload = {
        "arm": arm,
        "tripId": TRIP_ID,
        "cloneGateEffective": summary.get("cloneGateEffective"),
        "visionEffective": summary.get("visionEffective"),
        "ssgMode": summary.get("ssgMode"),
        "rejectFunnelTop": summary.get("rejectFunnelTop"),
        "patternCount": len(fp),
        "patternsHead": fp[:40],
    }
    (ROOT / f"{arm}-algoV3.json").write_text(
        json.dumps({"summary": payload, "algoV3": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (ROOT / f"{arm}-patterns.json").write_text(
        json.dumps(fp, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copy2(trip_path.parent / "index.html", ROOT / f"{arm}-index.html")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    arm = sys.argv[1]
    cfg = Path(sys.argv[2])
    run_arm(arm, cfg)
