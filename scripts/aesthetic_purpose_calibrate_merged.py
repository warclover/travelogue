"""AA · merged purpose weight grid (cover × landscape) + dongao cover pairwise re-export."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config  # noqa: E402
from travelogue.curation.aesthetic_purpose_calibrate import (  # noqa: E402
    apply_recommended_presets,
    run_purpose_weight_calibration,
    run_purpose_weight_calibration_merged,
)
from travelogue.curation.aesthetic_purpose_blind import build_purpose_pairwise_html  # noqa: E402
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402
from travelogue.config.aesthetic_stratified import landscape_pilot_config  # noqa: E402

CALIBRATION_PATH = Path("docs/acceptance-records/aesthetic-stratum-calibration.merged.v3.json")
CORPUS_PATH = Path("docs/acceptance-records/aesthetic-alignment-corpus.v3.json")
MERGED_LABELS = Path("docs/acceptance-records/aesthetic-human-labels.merged.v3.json")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pilot_cfg() -> Any:
    app = get_config()
    cal = _resolve(CALIBRATION_PATH)
    base = landscape_pilot_config(cal, use_album_relative=True)
    return replace(
        base,
        presets=app.aesthetic.presets,
        mllm=app.aesthetic.mllm,
        portrait_lite_enabled=app.aesthetic.portrait_lite_enabled,
    )


def _apply_cover_weights_to_config(weights: dict[str, float]) -> None:
    path = ROOT / "config.yaml"
    text = path.read_text(encoding="utf-8")
    block = (
        "  presets:\n"
        f"    cover:\n"
        f"      composition: {weights.get('composition', 0.3)}\n"
        f"      exposure: {weights.get('exposure', 0.15)}\n"
        f"      color: {weights.get('color', 0.25)}\n"
        f"      lighting: {weights.get('lighting', 0.15)}\n"
        f"      subjectClarity: {weights.get('subjectClarity', 0.15)}\n"
    )
    if "presets:" in text:
        text = re.sub(r"  presets:\n(?:    [^\n]+\n)+", block, text, count=1)
    else:
        text = text.replace("  portrait_lite_enabled:", block + "  portrait_lite_enabled:")
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · cover purpose calibrate (landscape)")
    parser.add_argument(
        "--write",
        type=Path,
        default=Path("docs/acceptance-records/aesthetic-purpose-calibration.cover-landscape.v3.json"),
    )
    parser.add_argument("--export-dongao-cover", action="store_true")
    parser.add_argument("--pairs", type=int, default=8)
    args = parser.parse_args(argv)

    if not pyiqa_available():
        print("E_AA_PURPOSE: pyiqa not installed", file=sys.stderr)
        return 2

    corpus = _load_json(_resolve(CORPUS_PATH))
    labels_doc = _load_json(_resolve(MERGED_LABELS))
    rows = list(labels_doc.get("rows") or [])
    trip_specs = [
        t
        for t in (corpus.get("trips") or [])
        if not str(t.get("tripId") or "").startswith("TBD")
        and t.get("ingestStatus") != "deferred"
    ]

    cfg = _pilot_cfg()
    merged_landscape = run_purpose_weight_calibration_merged(
        trip_specs=trip_specs,
        label_rows=rows,
        root=ROOT,
        purposes=("cover",),
        strata_filter=frozenset({"landscape"}),
        cfg=cfg,
    )

    dongao_spec = next(t for t in trip_specs if t["tripId"] == "demo-2025-6")
    dongao_labels = _load_json(
        _resolve(
            Path(
                dongao_spec.get("existingLabels")
                or "docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json"
            )
        )
    )
    dongao_cover = run_purpose_weight_calibration(
        trip_dir=_resolve(Path(dongao_spec["tripDir"])),
        label_rows=list(dongao_labels.get("rows") or []),
    )

    cover_rec = (merged_landscape["calibration"].get("purposes") or {}).get("cover", {}).get("recommended", {})
    cover_weights = merged_landscape.get("recommendedCoverWeights") or {}

    out = {
        "version": "1",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "notes": "P2-4 · cover purpose grid · landscape stratum · merged v3",
        "mergedLandscape": merged_landscape,
        "dongaoTrip": dongao_cover,
        "recommended": {
            "cover": cover_rec,
            "coverWeights": cover_weights,
            "tunedCoverSrcc": (merged_landscape.get("tunedPurposeSrcc") or {}).get("cover", {}).get("srcc"),
        },
        "configYamlSnippet": {"aesthetic": {"presets": {"cover": cover_weights}}},
    }

    write_path = _resolve(args.write)
    _save_json(write_path, out)
    print(write_path)
    print(
        f"cover dim={cover_rec.get('dim')} emphasis={cover_rec.get('emphasis')} "
        f"srcc={cover_rec.get('srcc')} tuned={out['recommended']['tunedCoverSrcc']}"
    )
    print("weights", cover_weights)

    if cover_weights:
        _apply_cover_weights_to_config(cover_weights)
        get_config(reload=True)

    if args.export_dongao_cover:
        from scripts.aesthetic_purpose_pairwise_export import export_trip_pairwise

        spec = {
            "tripId": "demo-2025-6",
            "tripDir": "trips/demo-2025-6",
            "title": "东澳岛 · cover A/B（调权后）",
            "previewUrl": "http://127.0.0.1:8766/demo-2025-6",
        }
        export = export_trip_pairwise(
            spec,
            calibration_path=_resolve(CALIBRATION_PATH),
            pairs_per_purpose=args.pairs,
            purposes=("cover",),
            seed=43,
        )
        export["notes"] = "cover-only · post purpose-calibration"
        json_out = _resolve(Path("docs/acceptance-records/purpose-pairwise.demo-2025-6.cover-v2.json"))
        html_out = _resolve(Path("docs/acceptance-records/purpose-pairwise.demo-2025-6.cover-v2.html"))
        _save_json(json_out, export)
        html_out.write_text(
            build_purpose_pairwise_html(export, image_base_url=spec["previewUrl"], title=spec["title"]),
            encoding="utf-8",
        )
        print(json_out, f"pairs={export['pairCount']}")
        print(html_out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
