"""AC-SC-00 · recruit general/group blind-review rows (v4 gap fill)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.aesthetic_blind_review import (  # noqa: E402
    build_blind_review_html,
    build_review_row,
    review_stratum_for_asset,
    shuffle_blind_rows,
)

DEFAULT_CORPUS = ROOT / "docs/acceptance-records/aesthetic-alignment-corpus.merged.v4.json"
DEFAULT_LABELS = ROOT / "docs/acceptance-records/aesthetic-human-labels.merged.v4.json"
RECORDS = ROOT / "docs/acceptance-records"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _labeled_ids(labels_doc: dict) -> set[str]:
    return {str(r.get("assetId") or "") for r in (labels_doc.get("rows") or []) if r.get("assetId")}


def collect_candidates(
    corpus_path: Path,
    *,
    labeled: set[str],
    stratum: str,
) -> list[dict]:
    spec = _load(corpus_path)
    out: list[dict] = []
    for trip in spec.get("trips") or []:
        if trip.get("role") == "hold_out":
            continue
        trip_id = str(trip.get("tripId") or "")
        trip_dir = ROOT / str(trip.get("tripDir") or f"trips/{trip_id}")
        trip_path = trip_dir / "trip.json"
        if not trip_path.is_file():
            continue
        trip_json = _load(trip_path)
        for asset in trip_json.get("assets") or []:
            aid = str(asset.get("id") or "")
            if not aid or aid in labeled:
                continue
            if review_stratum_for_asset(asset) != stratum:
                continue
            tagged = dict(asset)
            tagged["_tripId"] = trip_id
            tagged["_tripDir"] = str(trip.get("tripDir") or f"trips/{trip_id}").replace("\\", "/")
            out.append(tagged)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recruit AC-SC-00 general/group labels")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--general", type=int, default=16)
    parser.add_argument("--group", type=int, default=1)
    parser.add_argument("--seed", type=int, default=46)
    args = parser.parse_args(argv)

    labels_doc = _load(args.labels if args.labels.is_absolute() else ROOT / args.labels)
    labeled = _labeled_ids(labels_doc)
    rng = random.Random(args.seed)

    rows: list[dict] = []
    for stratum, quota in (("general", args.general), ("group", args.group)):
        pool = collect_candidates(
            args.corpus if args.corpus.is_absolute() else ROOT / args.corpus,
            labeled=labeled,
            stratum=stratum,
        )
        rng.shuffle(pool)
        picked = pool[:quota]
        for asset in picked:
            rows.append(
                build_review_row(
                    asset,
                    trip_id=str(asset.get("_tripId") or ""),
                    trip_dir=str(asset.get("_tripDir") or ""),
                    display_order=0,
                )
            )
            labeled.add(str(asset.get("id") or ""))

    rows = shuffle_blind_rows(rows, seed=args.seed)
    export = {
        "version": "1",
        "exportedAt": datetime.now(UTC).isoformat(),
        "purpose": "AC-SC-00 recruit · general/group gap fill",
        "targetGeneral": args.general,
        "targetGroup": args.group,
        "sampleCount": len(rows),
        "stratumCounts": {
            "general": sum(1 for r in rows if r.get("stratum") == "general"),
            "group": sum(1 for r in rows if r.get("stratum") == "group"),
        },
        "rows": rows,
        "notes": "人工盲评后 merge 进 aesthetic-human-labels.merged.v4.json 并重跑 signoff",
    }

    json_path = RECORDS / "aesthetic-blind-export.sc00-recruit.v4.json"
    html_path = RECORDS / "aesthetic-blind-review.sc00-recruit.v4.html"
    _save(json_path, export)
    html_path.write_text(
        build_blind_review_html(export, default_image_base_url="", title="AC-SC-00 · general/group 补标"),
        encoding="utf-8",
    )
    print(json_path, "rows=", len(rows), export["stratumCounts"])
    print(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
