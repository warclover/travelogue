"""AA · export purpose pairwise A/B for AC-SC-03 (rules vs aligned picks)."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config  # noqa: E402
from travelogue.config.aesthetic import AestheticConfig  # noqa: E402
from travelogue.config.aesthetic_stratified import config_summary, landscape_pilot_config  # noqa: E402
from travelogue.curation.aesthetic_purpose_blind import (  # noqa: E402
    build_purpose_pairwise_html,
    export_purpose_pick_pairs,
    score_purpose_pairwise_export,
)
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment  # noqa: E402

DOGFOOD_TRIPS = [
    {
        "tripId": "demo-fc8b3a5c08",
        "tripDir": "trips/demo-fc8b3a5c08",
        "title": "锡兰之旅 · cover/hero A/B",
        "previewUrl": "http://127.0.0.1:8766/demo-fc8b3a5c08",
    },
    {
        "tripId": "demo-1a737d6205",
        "tripDir": "trips/demo-1a737d6205",
        "title": "张智慧精选 · cover/hero A/B",
        "previewUrl": "http://127.0.0.1:8766/demo-1a737d6205",
    },
    {
        "tripId": "demo-2025-6",
        "tripDir": "trips/demo-2025-6",
        "title": "东澳岛 · cover/hero A/B",
        "previewUrl": "http://127.0.0.1:8766/demo-2025-6",
    },
]


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _apply_cover_subject_clarity(cfg: AestheticConfig, value: float) -> AestheticConfig:
    cover = replace(cfg.presets.cover, subject_clarity=value)
    presets = replace(cfg.presets, cover=cover)
    return replace(cfg, presets=presets)


def export_trip_pairwise(
    spec: dict[str, str],
    *,
    calibration_path: Path,
    pairs_per_purpose: int = 6,
    purposes: tuple[str, ...] = ("cover", "hero"),
    seed: int = 42,
    use_app_config: bool = True,
    cover_subject_clarity: float | None = None,
    exclude_asset_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    trip_dir = _resolve(Path(spec["tripDir"]))
    trip = _load_json(trip_dir / "trip.json")
    trip_id = str(spec["tripId"])
    assets = copy.deepcopy(list(trip.get("assets") or []))

    if exclude_asset_ids:
        excluded = {str(aid).strip() for aid in exclude_asset_ids if str(aid).strip()}
        assets = [a for a in assets if str(a.get("id") or "") not in excluded]

    app_cfg = get_config()
    if app_cfg.aesthetic.enabled:
        apply_aesthetic_alignment(assets, trip_dir=trip_dir, cfg=app_cfg, trip=trip)

    if use_app_config and app_cfg.aesthetic.ml_calibrate:
        rules_cfg = replace(app_cfg.aesthetic, ml_calibrate=False, use_album_relative=False, source="rules")
        aligned_cfg = app_cfg.aesthetic
    else:
        rules_cfg = replace(app_cfg.aesthetic, ml_calibrate=False, use_album_relative=False, source="rules")
        aligned_cfg = landscape_pilot_config(calibration_path, use_album_relative=True)

    if cover_subject_clarity is not None:
        rules_cfg = _apply_cover_subject_clarity(rules_cfg, cover_subject_clarity)
        aligned_cfg = _apply_cover_subject_clarity(aligned_cfg, cover_subject_clarity)

    export = export_purpose_pick_pairs(
        assets,
        rules_cfg=rules_cfg,
        aligned_cfg=aligned_cfg,
        trip_id=trip_id,
        purposes=purposes,  # type: ignore[arg-type]
        pairs_per_purpose=pairs_per_purpose,
        seed=seed,
        album_relative=bool(aligned_cfg.use_album_relative),
    )
    export["exportedAt"] = datetime.now(timezone.utc).isoformat()
    pilot = config_summary(aligned_cfg)
    if cover_subject_clarity is not None:
        pilot["coverSubjectClarityOverride"] = cover_subject_clarity
    if exclude_asset_ids:
        export["excludedAssetIds"] = list(exclude_asset_ids)
    export["pilotConfig"] = pilot
    export["previewUrl"] = spec.get("previewUrl")
    return export


def _output_stem(trip_id: str, suffix: str) -> str:
    stem = f"purpose-pairwise.{trip_id}"
    if suffix:
        return f"{stem}.{suffix}"
    return stem


def merge_pairwise_verdicts(template: dict[str, Any], judged: dict[str, Any]) -> dict[str, Any]:
    """Merge human judgeVerdict from downloaded JSON into full export (keeps leftRole)."""
    by_id = {str(p.get("pairId")): p for p in (judged.get("pairs") or []) if p.get("pairId")}
    out = copy.deepcopy(template)
    for pair in out.get("pairs") or []:
        pid = str(pair.get("pairId"))
        if pid in by_id and by_id[pid].get("judgeVerdict"):
            pair["judgeVerdict"] = by_id[pid]["judgeVerdict"]
    out["scoring"] = score_purpose_pairwise_export(out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · purpose pairwise export (AC-SC-03)")
    parser.add_argument("--trip-dir", type=Path, default=None, help="Single trip; default all dogfood")
    parser.add_argument("--trip-id", type=str, default=None)
    parser.add_argument(
        "--calibration",
        type=Path,
        default=Path("docs/acceptance-records/aesthetic-stratum-calibration.merged.v3.json"),
    )
    parser.add_argument("--pairs-per-purpose", type=int, default=6)
    parser.add_argument("--purposes", type=str, default="cover,hero")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--write-dir", type=Path, default=Path("docs/acceptance-records"))
    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        help="Output suffix e.g. portrait-v2 → purpose-pairwise.{tripId}.portrait-v2.json",
    )
    parser.add_argument("--notes", type=str, default="", help="Freeform note stored in export JSON")
    parser.add_argument(
        "--cover-subject-clarity",
        type=float,
        default=None,
        help="Override presets.cover.subjectClarity for this export (e.g. 0.45 landscape)",
    )
    parser.add_argument(
        "--exclude-asset-ids",
        type=str,
        default="",
        help="Comma-separated asset IDs to omit from ranking/pairs (e.g. asset-071)",
    )
    parser.add_argument("--score", type=Path, default=None, help="Merge judged JSON into template and score")
    parser.add_argument("--template", type=Path, default=None, help="Full export JSON with leftRole mapping")
    args = parser.parse_args(argv)

    if args.score:
        template = _load_json(_resolve(args.template or args.score))
        judged = _load_json(_resolve(args.score))
        out = merge_pairwise_verdicts(template, judged)
        trip_id = str(out.get("tripId") or "unknown")
        suffix = args.suffix.strip()
        scored_name = f"purpose-pairwise-scored.{trip_id}"
        if suffix:
            scored_name = f"{scored_name}.{suffix}"
        out_path = _resolve(args.write_dir) / f"{scored_name}.json"
        _save_json(out_path, out)
        print(out_path)
        print(f"winrate={out['scoring'].get('alignedWinratePct')}% passed={out['scoring'].get('passed')}")
        return 0

    purposes = tuple(p.strip() for p in args.purposes.split(",") if p.strip())  # type: ignore[assignment]
    specs = list(DOGFOOD_TRIPS)
    if args.trip_dir:
        trip_dir = _resolve(args.trip_dir)
        trip = _load_json(trip_dir / "trip.json")
        specs = [
            {
                "tripId": args.trip_id or str(trip.get("tripId") or trip_dir.name),
                "tripDir": str(trip_dir.relative_to(ROOT)).replace("\\", "/"),
                "title": str(trip.get("meta", {}).get("title") or trip_dir.name),
                "previewUrl": f"http://127.0.0.1:8766/{trip_dir.name}",
            }
        ]

    write_dir = _resolve(args.write_dir)
    summary_trips: dict[str, Any] = {}
    suffix = (args.suffix or "").strip()
    exclude_asset_ids = tuple(
        aid.strip() for aid in args.exclude_asset_ids.split(",") if aid.strip()
    )

    for spec in specs:
        export = export_trip_pairwise(
            spec,
            calibration_path=_resolve(args.calibration),
            pairs_per_purpose=args.pairs_per_purpose,
            purposes=purposes,  # type: ignore[arg-type]
            seed=args.seed,
            cover_subject_clarity=args.cover_subject_clarity,
            exclude_asset_ids=exclude_asset_ids,
        )
        if args.notes:
            export["notes"] = args.notes
        trip_id = str(export["tripId"])
        stem = _output_stem(trip_id, suffix)
        json_path = write_dir / f"{stem}.json"
        html_path = write_dir / f"{stem}.html"
        _save_json(json_path, export)
        html_path.write_text(
            build_purpose_pairwise_html(
                export,
                image_base_url=str(spec.get("previewUrl") or ""),
                title=str(spec.get("title") or trip_id),
            ),
            encoding="utf-8",
        )
        print(json_path, f"pairs={export['pairCount']}")
        print(html_path)
        summary_trips[trip_id] = {
            "pairCount": export["pairCount"],
            "topPicks": export.get("topPicks"),
            "json": str(json_path.relative_to(ROOT)).replace("\\", "/"),
            "html": str(html_path.relative_to(ROOT)).replace("\\", "/"),
        }

    manifest = {
        "version": "1",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "purposes": list(purposes),
        "pairsPerPurpose": args.pairs_per_purpose,
        "suffix": suffix or None,
        "notes": args.notes or None,
        "trips": summary_trips,
    }
    manifest_name = "purpose-pairwise.manifest.v3.json"
    if suffix:
        manifest_name = f"purpose-pairwise.manifest.{suffix}.json"
    manifest_path = write_dir / manifest_name
    _save_json(manifest_path, manifest)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
