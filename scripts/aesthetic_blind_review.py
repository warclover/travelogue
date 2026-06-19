"""Human aesthetic alignment · blind review + SRCC baseline (PRD-AA · M0).

Usage:
  python scripts/aesthetic_blind_review.py --init-corpus docs/acceptance-records/aesthetic-alignment-corpus.json
  python scripts/aesthetic_blind_review.py --export-corpus docs/acceptance-records/aesthetic-alignment-corpus.json --write docs/acceptance-records/aesthetic-blind-export.json
  python scripts/aesthetic_blind_review.py --init-labels docs/acceptance-records/aesthetic-blind-export.json --write docs/acceptance-records/aesthetic-human-labels.json
  python scripts/aesthetic_blind_review.py --srcc docs/acceptance-records/aesthetic-human-labels.json
  python scripts/aesthetic_blind_review.py --srcc docs/acceptance-records/aesthetic-human-labels.json --compare-purposes
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.aesthetic_blind_review import (  # noqa: E402
    all_eligible_for_review,
    build_blind_review_html,
    build_review_row,
    compare_predicted_keys,
    init_corpus_template,
    init_labels_from_export,
    sample_assets_for_review,
    shuffle_blind_rows,
    srcc_report,
)
from travelogue.curation.aesthetic_purpose_blind import export_pairwise_pairs  # noqa: E402


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_trip_assets(trip_dir: Path) -> list[dict]:
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        raise FileNotFoundError(trip_path)
    trip = _load_json(trip_path)
    return list(trip.get("assets") or [])


def cmd_export_corpus(corpus_path: Path) -> dict[str, Any]:
    spec = _load_json(_resolve_path(corpus_path))
    target = int(spec.get("targetTotal") or 150)
    seed = int(spec.get("seed") or 42)
    quotas = spec.get("strataQuotas") or None
    all_assets: list[dict] = []
    trip_meta: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for trip in spec.get("trips") or []:
        trip_id = str(trip.get("tripId") or "trip")
        trip_dir_raw = str(trip.get("tripDir") or "").strip()
        if not trip_dir_raw:
            errors.append({"tripId": trip_id, "error": "missing tripDir"})
            continue
        trip_dir = _resolve_path(Path(trip_dir_raw))
        try:
            assets = _load_trip_assets(trip_dir)
        except FileNotFoundError as exc:
            errors.append({"tripId": trip_id, "error": str(exc)})
            continue
        stratum_override = trip.get("stratumOverride")
        for asset in assets:
            tagged = dict(asset)
            tagged["_tripId"] = trip_id
            tagged["_tripDir"] = trip_dir_raw.replace("\\", "/")
            if stratum_override:
                tagged["_stratumOverride"] = str(stratum_override)
            all_assets.append(tagged)
        trip_meta.append(
            {
                "tripId": trip_id,
                "tripDir": trip_dir_raw,
                "assetCount": len(assets),
                "tags": list(trip.get("tags") or []),
            }
        )

    export_mode = str(spec.get("exportMode") or "sample").strip().lower()
    if export_mode == "all_eligible":
        sampled = all_eligible_for_review(all_assets)
    else:
        sampled = sample_assets_for_review(
            all_assets,
            target_n=target,
            strata_quotas=quotas,
            seed=seed,
        )
    rows: list[dict[str, Any]] = []
    for asset in sampled:
        rows.append(
            build_review_row(
                asset,
                trip_id=str(asset.get("_tripId") or ""),
                trip_dir=str(asset.get("_tripDir") or ""),
                display_order=0,
                stratum_override=asset.get("_stratumOverride"),
            )
        )
    rows = shuffle_blind_rows(rows, seed=seed)

    stratum_counts: dict[str, int] = {}
    for row in rows:
        s = str(row.get("stratum") or "general")
        stratum_counts[s] = stratum_counts.get(s, 0) + 1

    return {
        "version": "1",
        "exportedAt": datetime.now(UTC).isoformat(),
        "corpusSource": str(corpus_path),
        "targetTotal": target,
        "seed": seed,
        "sampleCount": len(rows),
        "stratumCounts": stratum_counts,
        "trips": trip_meta,
        "errors": errors,
        "notes": "Review images by displayOrder. Fill humanScore in labels JSON (1–5 or 0–1).",
        "rows": rows,
    }


def cmd_srcc(labels_path: Path, *, compare_purposes: bool) -> dict[str, Any]:
    raw = _load_json(_resolve_path(labels_path))
    rows = raw if isinstance(raw, list) else list(raw.get("rows") or [])
    report: dict[str, Any] = {
        "source": str(labels_path),
        "frozen": bool(raw.get("frozen")) if isinstance(raw, dict) else False,
        **srcc_report(rows, by_stratum=True),
    }
    if compare_purposes:
        report["purposeComparison"] = compare_predicted_keys(rows)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aesthetic alignment blind review (M0)")
    parser.add_argument("--init-corpus", type=Path, metavar="PATH")
    parser.add_argument("--export-corpus", type=Path, metavar="CORPUS_JSON")
    parser.add_argument("--init-labels", type=Path, metavar="EXPORT_JSON")
    parser.add_argument("--srcc", type=Path, metavar="LABELS_JSON")
    parser.add_argument("--compare-purposes", action="store_true")
    parser.add_argument("--export-pairwise", action="store_true", help="GAP-13 · export stratified A/B pairs")
    parser.add_argument("--pairs-per-stratum", type=int, default=15)
    parser.add_argument("--write", type=Path, default=None)
    parser.add_argument("--write-html", type=Path, default=None, help="Write browser blind-review page")
    parser.add_argument(
        "--image-base-url",
        type=str,
        default="",
        help="Optional HTTP base for HTML reviewer; default uses ../../trips/<id> (no Studio required)",
    )
    parser.add_argument(
        "--no-relative-images",
        action="store_true",
        help="Disable ../../trips/ relative image URLs (requires --image-base-url or Studio)",
    )
    parser.add_argument("--html-title", type=str, default="审美盲评")
    args = parser.parse_args(argv)

    out: dict[str, Any] | None = None

    if args.init_corpus:
        out = init_corpus_template()
        path = _resolve_path(args.init_corpus)
        _save_json(path, out)
        print(path)
        return 0

    if args.export_corpus:
        out = cmd_export_corpus(args.export_corpus)
    elif args.init_labels:
        export = _load_json(_resolve_path(args.init_labels))
        out = init_labels_from_export(export)
    elif args.srcc:
        out = cmd_srcc(args.srcc, compare_purposes=args.compare_purposes)
        if args.export_pairwise:
            labels_raw = _load_json(_resolve_path(args.srcc))
            rows = labels_raw if isinstance(labels_raw, list) else list(labels_raw.get("rows") or [])
            out["pairwise"] = export_pairwise_pairs(rows, pairs_per_stratum=args.pairs_per_stratum)
    else:
        parser.error("Provide --init-corpus, --export-corpus, --init-labels, or --srcc")
        return 2

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        write_path = _resolve_path(args.write)
        _save_json(write_path, out)
        print(write_path)
    else:
        print(text)

    if args.write_html:
        if out is None or not args.export_corpus:
            parser.error("--write-html requires --export-corpus")
            return 2
        html_path = _resolve_path(args.write_html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(
            build_blind_review_html(
                out,
                default_image_base_url=args.image_base_url,
                use_relative_image_urls=not args.no_relative_images,
                title=args.html_title,
            ),
            encoding="utf-8",
        )
        print(html_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
