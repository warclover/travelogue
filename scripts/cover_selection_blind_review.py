"""Cover selection blind-review helper (cover-selection-plan v0.2 · S0).

Usage:
  python scripts/cover_selection_blind_review.py --init-albums docs/acceptance-records/cover-selection-albums.json
  python scripts/cover_selection_blind_review.py --init-signoff docs/acceptance-records/cover-selection-signoff.json
  python scripts/cover_selection_blind_review.py --trip-dir trips/demo-xxx --export-layout mobile
  python scripts/cover_selection_blind_review.py --assets-json path/to/assets.json --album-id sample-01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALBUMS = ROOT / "docs" / "acceptance-records" / "cover-selection-albums.json"
DEFAULT_SIGNOFF = ROOT / "docs" / "acceptance-records" / "cover-selection-signoff.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def init_albums_template(path: Path) -> dict:
    data = {
        "version": "1",
        "notes": "Freeze before R0. Fill albumId, tripDir or assets path, tags for stratified stats.",
        "albums": [
            {
                "albumId": "mao",
                "tripDir": "trips/mao",
                "tags": ["portrait_heavy", "featured"],
                "exportLayout": "mobile",
            },
            {
                "albumId": "maomi",
                "tripDir": "trips/maomi",
                "tags": ["mixed"],
                "exportLayout": "mobile",
            },
            {
                "albumId": "placeholder-landscape",
                "tripDir": "",
                "tags": ["landscape"],
                "exportLayout": "mobile",
            },
        ],
    }
    _save(path, data)
    return data


def init_signoff_template(path: Path) -> dict:
    data = {
        "version": "1",
        "targets": {
            "m1": {"aRateMin": 6, "abRateMin": 9, "totalAlbums": 10},
            "m2": {"aRateMin": 7, "abRateMin": 9, "totalAlbums": 10},
            "portraitSubset": {"aRateMin": 5, "totalAlbums": 6},
        },
        "albums": [],
        "notes": "Per album: judge A|B|C, reasonTags, scoreRankedTop3 from export (not coverCandidates order).",
    }
    _save(path, data)
    return data


def _load_trip_assets(trip_dir: Path) -> list[dict]:
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        raise FileNotFoundError(trip_path)
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    return list(trip.get("assets") or [])


def eval_album(
    album_id: str,
    assets: list[dict],
    *,
    export_layout: str = "mobile",
) -> dict[str, Any]:
    from travelogue.config import get_config
    from travelogue.curation.curate_scoring import (
        build_cover_layout_review,
        pick_cover_asset_id,
    )

    cfg = get_config()
    cs = cfg.curate.cover_scoring
    p6 = cs.enable_phase6_factors
    cover_id = pick_cover_asset_id(
        assets,
        export_layout=export_layout,
        featured_weight=cfg.curate.featured_weight,
        enable_phase6_cover_factors=p6,
        cover_scoring=cs,
    )
    review = build_cover_layout_review(
        assets,
        cover_id,
        export_layout=export_layout,
        featured_weight=cfg.curate.featured_weight,
        enable_phase6_cover_factors=p6,
        cover_scoring=cs,
    )
    return {
        "albumId": album_id,
        "exportLayout": export_layout,
        "coverAssetId": cover_id,
        "scoreRankedTop3": review.get("scoreRankedTop3"),
        "scoreRankedTop10": review.get("scoreRankedTop10"),
        "personTagRatio": review.get("personTagRatio"),
        "personDemoteApplied": review.get("personDemoteApplied"),
        "featuredPoolOnly": review.get("featuredPoolOnly"),
        "coverExplain": review.get("coverExplain"),
        "judgeVerdict": None,
        "judgeReasonTags": [],
    }


def export_from_albums_json(path: Path) -> dict[str, Any]:
    spec = _load(path)
    rows: list[dict[str, Any]] = []
    for album in spec.get("albums") or []:
        album_id = str(album.get("albumId") or "album")
        layout = str(album.get("exportLayout") or "mobile")
        trip_dir_raw = str(album.get("tripDir") or "").strip()
        assets_path = str(album.get("assetsJson") or "").strip()
        if trip_dir_raw:
            assets = _load_trip_assets((ROOT / trip_dir_raw).resolve())
        elif assets_path:
            raw = _load((ROOT / assets_path).resolve() if not Path(assets_path).is_absolute() else Path(assets_path))
            assets = raw if isinstance(raw, list) else list(raw.get("assets") or [])
        else:
            rows.append({"albumId": album_id, "error": "missing tripDir or assetsJson"})
            continue
        rows.append(eval_album(album_id, assets, export_layout=layout))
    return {"source": str(path), "albums": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cover selection blind-review export")
    parser.add_argument("--init-albums", type=Path, metavar="PATH")
    parser.add_argument("--init-signoff", type=Path, metavar="PATH")
    parser.add_argument("--albums-json", type=Path, default=None)
    parser.add_argument("--trip-dir", type=Path, default=None)
    parser.add_argument("--assets-json", type=Path, default=None)
    parser.add_argument("--album-id", type=str, default="album")
    parser.add_argument("--export-layout", type=str, default="mobile")
    parser.add_argument("--write", type=Path, default=None, help="Write export JSON to path")
    args = parser.parse_args(argv)

    if args.init_albums:
        init_albums_template(args.init_albums)
        print(args.init_albums)
        return 0
    if args.init_signoff:
        init_signoff_template(args.init_signoff)
        print(args.init_signoff)
        return 0

    if args.albums_json:
        out = export_from_albums_json(args.albums_json)
    elif args.trip_dir:
        assets = _load_trip_assets(args.trip_dir.resolve())
        out = {"albums": [eval_album(args.album_id, assets, export_layout=args.export_layout)]}
    elif args.assets_json:
        raw = _load(args.assets_json.resolve())
        assets = raw if isinstance(raw, list) else list(raw.get("assets") or [])
        out = {"albums": [eval_album(args.album_id, assets, export_layout=args.export_layout)]}
    else:
        parser.error("Provide --albums-json, --trip-dir, or --assets-json (or --init-*)")
        return 2

    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        _save(args.write, out)
        print(args.write)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
