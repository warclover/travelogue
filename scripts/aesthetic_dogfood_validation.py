"""AA · dogfood validation for AC-SC-03/04 (≥3 albums, landscape pilot)."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config.aesthetic_stratified import config_summary, landscape_pilot_config  # noqa: E402
from travelogue.curation.album_profile import compute_album_profile, write_album_profile  # noqa: E402
from travelogue.curation.aesthetic_purpose_blind import (  # noqa: E402
    automated_purpose_win_report,
    export_purpose_blind_signoff,
)
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment  # noqa: E402
from travelogue.config import get_config  # noqa: E402

DOGFOOD_TRIPS: list[dict[str, str]] = [
    {
        "tripId": "demo-fc8b3a5c08",
        "tripDir": "trips/demo-fc8b3a5c08",
        "profile": "landscape_heavy",
        "labels": "docs/acceptance-records/aesthetic-human-labels.demo-fc8b3a5c08.v3.json",
    },
    {
        "tripId": "demo-1a737d6205",
        "tripDir": "trips/demo-1a737d6205",
        "profile": "mixed_portrait",
        "labels": "docs/acceptance-records/aesthetic-human-labels.demo-1a737d6205.json",
    },
    {
        "tripId": "demo-2025-6",
        "tripDir": "trips/demo-2025-6",
        "profile": "mixed_travel",
        "labels": "docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json",
    },
]


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_dogfood(
    *,
    calibration_path: Path,
    use_album_relative: bool = True,
    persist_profiles: bool = False,
) -> dict[str, Any]:
    aligned_cfg = landscape_pilot_config(
        calibration_path,
        use_album_relative=use_album_relative,
        stratum_blend_only=("landscape",),
    )
    from dataclasses import replace

    rules_cfg = replace(
        aligned_cfg,
        ml_calibrate=False,
        use_stratum_blend=False,
        use_album_relative=False,
        source="rules",
    )

    app_cfg = get_config()
    per_trip: dict[str, Any] = {}
    wins = 0
    comparable = 0

    for spec in DOGFOOD_TRIPS:
        trip_dir = _resolve(Path(spec["tripDir"]))
        trip = _load_json(trip_dir / "trip.json")
        trip_id = str(spec["tripId"])
        assets = copy.deepcopy(list(trip.get("assets") or []))

        if app_cfg.aesthetic.enabled:
            apply_aesthetic_alignment(assets, trip_dir=trip_dir, cfg=app_cfg, trip=trip)

        profile = compute_album_profile({**trip, "assets": assets})
        if persist_profiles:
            write_album_profile({**trip, "assets": assets})
            trip.setdefault("curation", {})["albumProfile"] = profile
            _save_json(trip_dir / "trip.json", trip)

        labels_doc = _load_json(_resolve(Path(spec["labels"])))
        label_rows = list(labels_doc.get("rows") or [])

        automated = automated_purpose_win_report(
            assets,
            label_rows,
            rules_cfg=rules_cfg,
            aligned_cfg=aligned_cfg,
            album_relative=use_album_relative,
        )
        signoff = export_purpose_blind_signoff(trip_id, automated)

        if automated.get("comparablePurposes"):
            comparable += int(automated["comparablePurposes"])
        if automated.get("automatedWinCount") is not None:
            wins += int(automated["automatedWinCount"])

        per_trip[trip_id] = {
            "profileTag": spec["profile"],
            "albumProfile": profile,
            "labelsPath": spec["labels"],
            "automated": automated,
            "signoff": signoff,
            "acSc03Passed": bool(automated.get("passed")),
            "acSc04AlbumProfile": bool(profile.get("strata")),
        }

    winrate = round(100.0 * wins / comparable, 2) if comparable else None
    return {
        "version": "1",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "notes": "Dogfood · landscape stratum-blend pilot · food 语料搁置",
        "pilotConfig": config_summary(aligned_cfg),
        "calibrationSource": str(calibration_path.relative_to(ROOT)).replace("\\", "/"),
        "useAlbumRelative": use_album_relative,
        "trips": per_trip,
        "aggregate": {
            "automatedWinCount": wins,
            "comparablePurposes": comparable,
            "automatedWinratePct": winrate,
            "targetWinratePct": 60.0,
            "passedAcSc03": winrate is not None and winrate >= 60.0,
        },
        "acceptance": {
            "AC-SC-03": {
                "passed": winrate is not None and winrate >= 60.0,
                "automatedWinratePct": winrate,
                "note": "自动化 proxy；人工 pairwise 待补",
            },
            "AC-SC-04": {
                "passed": all(t.get("acSc04AlbumProfile") for t in per_trip.values()),
                "note": "albumProfile 已计算；skew 册回归待 curate 对比",
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · stratified dogfood validation")
    parser.add_argument(
        "--calibration",
        type=Path,
        default=Path("docs/acceptance-records/aesthetic-stratum-calibration.merged.v3.json"),
    )
    parser.add_argument("--no-album-relative", action="store_true")
    parser.add_argument("--persist-profiles", action="store_true", help="Write albumProfile to trip.json")
    parser.add_argument("--write", type=Path, default=Path("docs/acceptance-records/aesthetic-dogfood-validation.v3.json"))
    args = parser.parse_args(argv)

    out = run_dogfood(
        calibration_path=_resolve(args.calibration),
        use_album_relative=not args.no_album_relative,
        persist_profiles=bool(args.persist_profiles),
    )
    write_path = _resolve(args.write)
    _save_json(write_path, out)
    print(write_path)
    print(f"AC-SC-03 automated winrate={out['aggregate']['automatedWinratePct']}%")
    print(f"AC-SC-04 albumProfile={out['acceptance']['AC-SC-04']['passed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
