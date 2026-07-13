"""Bookends closing blind-review export skeleton (PRD §14.1 · BE-BE-11).

Exports paired stimuli: cover thumbnail + old heuristic vs Bookends closing.
Does NOT run the human study — freezes machine-side candidates for AC-BE-40/41.

Usage:
  python scripts/bookends_closing_blind_export.py --init-albums
  python scripts/bookends_closing_blind_export.py --trip-dir trips/demo-xxx --out .cache/bookends-blind/demo.json
  python scripts/bookends_closing_blind_export.py --albums docs/acceptance-records/bookends-closing-albums.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALBUMS = ROOT / "docs" / "acceptance-records" / "bookends-closing-albums.json"
DEFAULT_SIGNOFF = ROOT / "docs" / "acceptance-records" / "bookends-closing-signoff.json"


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def init_albums_template(path: Path = DEFAULT_ALBUMS) -> dict:
    data = {
        "version": "1",
        "notes": (
            "B0 baseline freeze for Bookends closing blind review. "
            "Fill tripDir when local trips exist. Synthetic fixtures listed in ACCEPTANCE."
        ),
        "protocol": {
            "question": "哪边封底更有收束/回望（不是更好看）",
            "mustShowCoverThumbnail": True,
            "minJudges": 3,
            "minAlbums": 10,
        },
        "albums": [
            {
                "albumId": "opening-v6-fit",
                "tripDir": "",
                "fixtureRef": "tests/unit/curation/test_cover_styles_v6_golden.py",
                "tags": ["opening", "v6"],
            },
            {
                "albumId": "closing-unused",
                "tripDir": "",
                "fixtureRef": "tests/unit/cover_engine/test_bookends_dogfood_b2a.py::df-01",
                "tags": ["closing", "unused"],
            },
            {
                "albumId": "closing-tiny-degraded",
                "tripDir": "",
                "fixtureRef": "tests/unit/cover_engine/test_bookends_dogfood_b2a.py::df-03-tiny",
                "tags": ["closing", "degraded", "colophon"],
            },
            {
                "albumId": "closing-portrait-h3",
                "tripDir": "",
                "fixtureRef": "tests/unit/cover_engine/test_bookends_closing_pairing.py::test_pair_h3",
                "tags": ["closing", "portrait", "PAIR-H3"],
            },
            {
                "albumId": "placeholder-local-trip",
                "tripDir": "trips/",
                "tags": ["local"],
            },
        ],
    }
    _save(path, data)
    return data


def init_signoff_template(path: Path = DEFAULT_SIGNOFF) -> dict:
    data = {
        "version": "1",
        "targets": {
            "closingPreferBookendsMinRate": 0.60,
            "coverARateMin": "freeze-from-cover-selection-signoff",
            "totalAlbums": 10,
            "minJudges": 3,
        },
        "albums": [],
        "notes": (
            "Per album: sideA=legacy heuristic, sideB=bookends; "
            "randomize left/right for judges; record degraded, portraitCover, abstain."
        ),
    }
    _save(path, data)
    return data


def _legacy_closing_id(trip: dict, assets: dict[str, dict]) -> str | None:
    """Old heuristic without cover reuse (post-B2a fail-open path)."""
    from travelogue.domain.closing_view import _resolve_closing_no_cover_fallback

    return _resolve_closing_no_cover_fallback(trip, assets, prefer_landscape=True)


def _bookends_closing_id(trip: dict) -> tuple[str | None, bool]:
    from travelogue.cover_engine.api import resolve_closing

    # Work on a shallow copy of curation to avoid mutating caller mid-export
    trip = dict(trip)
    trip["curation"] = dict(trip.get("curation") or {})
    trip["curation"].pop("closingAssetId", None)
    trip["curation"].pop("bookendsLock", None)
    decision = resolve_closing(trip, layout=trip.get("exportLayout") or "web", force=True)
    return decision.closing_asset_id, bool(decision.degraded)


def export_trip_pair(trip_dir: Path) -> dict[str, Any]:
    trip_path = trip_dir / "trip.json"
    if not trip_path.is_file():
        raise FileNotFoundError(trip_path)
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    assets = {
        str(a.get("id")): a
        for a in (trip.get("assets") or [])
        if isinstance(a, dict) and a.get("id")
    }
    cover_id = str(trip.get("coverAssetId") or "")
    legacy = _legacy_closing_id(trip, assets)
    bookends_id, degraded = _bookends_closing_id(trip)
    return {
        "tripId": trip.get("tripId") or trip_dir.name,
        "tripDir": str(trip_dir),
        "coverAssetId": cover_id or None,
        "legacyClosingAssetId": legacy,
        "bookendsClosingAssetId": bookends_id,
        "degraded": degraded,
        "portraitCover": _is_portrait(assets.get(cover_id) if cover_id else None),
        "sameChoice": legacy == bookends_id,
        "protocolHint": "哪边封底更有收束/回望（不是更好看）",
    }


def _is_portrait(asset: dict | None) -> bool:
    if not asset:
        return False
    try:
        w = float(asset.get("width") or 0)
        h = float(asset.get("height") or 0)
        return h > w > 0
    except (TypeError, ValueError):
        return False


def export_albums(albums_path: Path, out_dir: Path) -> list[dict]:
    data = json.loads(albums_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for album in data.get("albums") or []:
        trip_dir = str(album.get("tripDir") or "").strip()
        if not trip_dir:
            rows.append(
                {
                    "albumId": album.get("albumId"),
                    "skipped": True,
                    "reason": "no tripDir",
                    "fixtureRef": album.get("fixtureRef"),
                }
            )
            continue
        path = ROOT / trip_dir if not Path(trip_dir).is_absolute() else Path(trip_dir)
        if not (path / "trip.json").is_file():
            rows.append(
                {
                    "albumId": album.get("albumId"),
                    "skipped": True,
                    "reason": f"missing {path / 'trip.json'}",
                }
            )
            continue
        row = export_trip_pair(path)
        row["albumId"] = album.get("albumId")
        row["tags"] = album.get("tags") or []
        rows.append(row)
        _save(out_dir / f"{album.get('albumId') or path.name}.json", row)
    _save(out_dir / "index.json", {"version": "1", "rows": rows})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-albums", action="store_true")
    parser.add_argument("--init-signoff", action="store_true")
    parser.add_argument("--albums", type=Path, default=None)
    parser.add_argument("--trip-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / ".cache" / "bookends-blind")
    args = parser.parse_args(argv)

    if args.init_albums:
        init_albums_template()
        print(f"wrote {DEFAULT_ALBUMS}")
        return 0
    if args.init_signoff:
        init_signoff_template()
        print(f"wrote {DEFAULT_SIGNOFF}")
        return 0
    if args.trip_dir:
        row = export_trip_pair(args.trip_dir)
        out = args.out
        if out.suffix.lower() == ".json":
            _save(out, row)
        else:
            out.mkdir(parents=True, exist_ok=True)
            _save(out / f"{row['tripId']}.json", row)
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0
    albums = args.albums or DEFAULT_ALBUMS
    if not albums.is_file():
        print(f"missing albums file: {albums}; run --init-albums", file=sys.stderr)
        return 2
    rows = export_albums(albums, args.out if args.out.suffix.lower() != ".json" else args.out.parent)
    print(f"exported {len(rows)} rows → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
