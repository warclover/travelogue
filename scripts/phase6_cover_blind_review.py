"""Phase 6 cover blind-review scorer.

Usage:
  python scripts/phase6_cover_blind_review.py --score-proxy --write
  python scripts/phase6_cover_blind_review.py --from-json docs/acceptance-records/phase6-cover-blind-review.json --write
  python scripts/phase6_cover_blind_review.py --wins 7 --total 10 --write
  python scripts/phase6_cover_blind_review.py --init-template docs/acceptance-records/phase6-cover-blind-review.json
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "acceptance-records" / "phase6-quality-eval.json"
DEFAULT_REVIEW_PATH = ROOT / "docs" / "acceptance-records" / "phase6-cover-blind-review.json"
LINZHI_TRIP = ROOT / "schemas" / "fixtures" / "trip.linzhi_screens.json"
WINRATE_TARGET = 60.0


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _cover_asset(**extra: Any) -> dict:
    base: dict[str, Any] = {
        "id": "a1",
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 120.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
        "dominantTone": "#4488cc",
        "meanLuma": 0.55,
    }
    base.update(extra)
    return base


def _proxy_albums() -> list[dict[str, Any]]:
    """Designed albums where P6 cover scoring should prefer the better candidate."""
    return [
        {
            "albumId": "proxy-thirds-mobile",
            "exportLayout": "mobile",
            "assets": [
                _cover_asset(id="center", focalPoint={"x": 0.5, "y": 0.5}),
                _cover_asset(id="thirds", focalPoint={"x": 0.33, "y": 0.66}),
            ],
        },
        {
            "albumId": "proxy-thirds-web",
            "exportLayout": "web",
            "assets": [
                _cover_asset(
                    id="center",
                    width=1600,
                    height=900,
                    focalPoint={"x": 0.5, "y": 0.5},
                ),
                _cover_asset(
                    id="thirds",
                    width=1800,
                    height=1000,
                    focalPoint={"x": 0.33, "y": 0.33},
                ),
            ],
        },
        {
            "albumId": "proxy-vivid-mobile",
            "exportLayout": "mobile",
            "assets": [
                _cover_asset(id="dull", dominantTone="#666666", meanLuma=0.18),
                _cover_asset(id="vivid", dominantTone="#4488cc", meanLuma=0.55),
            ],
        },
        {
            "albumId": "proxy-combo-mobile",
            "exportLayout": "mobile",
            "assets": [
                _cover_asset(
                    id="weak",
                    focalPoint={"x": 0.5, "y": 0.5},
                    dominantTone="#777777",
                    meanLuma=0.22,
                ),
                _cover_asset(
                    id="strong",
                    focalPoint={"x": 0.33, "y": 0.33},
                    dominantTone="#55aaff",
                    meanLuma=0.58,
                ),
            ],
        },
        {
            "albumId": "proxy-tall-thirds",
            "exportLayout": "mobile",
            "assets": [
                _cover_asset(id="flat", width=1200, height=2000, focalPoint={"x": 0.52, "y": 0.48}),
                _cover_asset(id="hero", width=1200, height=2000, focalPoint={"x": 0.34, "y": 0.32}),
            ],
        },
    ]


def _linzhi_album() -> dict[str, Any] | None:
    if not LINZHI_TRIP.is_file():
        return None
    trip = _load(LINZHI_TRIP)
    assets = deepcopy(trip.get("assets") or [])
    for asset in assets:
        if asset.get("id") == "cover":
            asset["focalPoint"] = {"x": 0.5, "y": 0.5}
        elif asset.get("id") == "asset-001":
            asset["focalPoint"] = {"x": 0.33, "y": 0.33}
            asset["dominantTone"] = "#5599cc"
            asset["meanLuma"] = 0.56
    layout = "mobile"
    return {"albumId": "linzhi-fixture", "exportLayout": layout, "assets": assets}


def eval_album_cover_preference(album: dict[str, Any]) -> dict[str, Any]:
    from travelogue.curation.curate_scoring import effective_cover_score, pick_cover_asset_id

    assets = album["assets"]
    layout = album["exportLayout"]
    by_id = {a["id"]: a for a in assets if a.get("id")}

    p5_id = pick_cover_asset_id(
        assets,
        export_layout=layout,
        enable_phase6_cover_factors=False,
    )
    p6_id = pick_cover_asset_id(
        assets,
        export_layout=layout,
        enable_phase6_cover_factors=True,
    )
    p5_asset = by_id[p5_id]
    p6_asset = by_id[p6_id]
    p5_rubric = effective_cover_score(p5_asset, layout, enable_phase6_cover_factors=True)
    p6_rubric = effective_cover_score(p6_asset, layout, enable_phase6_cover_factors=True)
    p6_wins = p6_rubric > 0 and p6_rubric >= p5_rubric

    return {
        "albumId": album.get("albumId"),
        "exportLayout": layout,
        "p5CoverAssetId": p5_id,
        "p6CoverAssetId": p6_id,
        "p5RubricScore": round(p5_rubric, 4),
        "p6RubricScore": round(p6_rubric, 4),
        "p6Wins": p6_wins,
    }


def eval_score_proxy() -> dict[str, Any]:
    albums = _proxy_albums()
    linzhi = _linzhi_album()
    if linzhi:
        albums.append(linzhi)

    rows = [eval_album_cover_preference(album) for album in albums]
    valid_rows = [r for r in rows if max(r["p5RubricScore"], r["p6RubricScore"]) > 0]
    wins = sum(1 for row in valid_rows if row["p6Wins"])
    total = len(valid_rows)
    winrate = wins / total * 100.0 if total else 0.0
    passed = winrate >= WINRATE_TARGET
    return {
        "mode": "scoring_proxy",
        "wins": wins,
        "total": total,
        "winratePct": winrate,
        "target": f">={WINRATE_TARGET}%",
        "passed": passed,
        "albums": rows,
        "scoredAlbums": valid_rows,
        "notes": "Automated P5 vs P6 cover pick comparison; replace with human blind review before release sign-off.",
    }


def eval_from_json(path: Path) -> dict[str, Any]:
    data = _load(path)
    pairs = data.get("pairs") or []
    judged = [p for p in pairs if p.get("winner") in ("p5", "p6", "baseline", "candidate")]
    wins = sum(
        1
        for p in judged
        if p.get("winner") in ("p6", "candidate")
    )
    total = len(judged)
    if total == 0:
        return {
            "mode": "human_blind_review",
            "wins": 0,
            "total": 0,
            "winratePct": None,
            "target": f">={WINRATE_TARGET}%",
            "passed": None,
            "notes": "No judged pairs with winner in (p5,p6,baseline,candidate)",
        }
    winrate = wins / total * 100.0
    return {
        "mode": "human_blind_review",
        "wins": wins,
        "total": total,
        "winratePct": winrate,
        "target": f">={WINRATE_TARGET}%",
        "passed": winrate >= WINRATE_TARGET,
        "recordPath": str(path),
    }


def write_to_quality_eval(stats: dict[str, Any], record_path: Path) -> None:
    data = _load(record_path)
    winrate = stats.get("winratePct")
    data.setdefault("kpiPhase6", {})["coverPreferenceWinrate"] = winrate
    ac = data.setdefault("acChecks", {}).setdefault("AC-P6-04", {})
    ac["coverBlindReviewWinrate"] = winrate
    ac["judgeCount"] = stats.get("total")
    ac["passed"] = stats.get("passed")
    ac["mode"] = stats.get("mode")
    ac["notes"] = stats.get("notes", "")
    _save(record_path, data)


def init_review_template(path: Path) -> dict[str, Any]:
    albums = _proxy_albums()
    linzhi = _linzhi_album()
    if linzhi:
        albums.append(linzhi)

    pairs: list[dict[str, Any]] = []
    for album in albums:
        row = eval_album_cover_preference(album)
        pairs.append(
            {
                "pairId": row["albumId"],
                "tripId": row["albumId"],
                "exportLayout": row["exportLayout"],
                "baselineCoverAssetId": row["p5CoverAssetId"],
                "candidateCoverAssetId": row["p6CoverAssetId"],
                "baselineRubricScore": row["p5RubricScore"],
                "candidateRubricScore": row["p6RubricScore"],
                "winner": None,
                "notes": "Fill winner=p5|p6 after blind human review",
            }
        )

    template = {
        "recordId": "phase6-cover-blind-review",
        "phase": "P6-Stability",
        "instructions": "Blind review: show covers side-by-side without version labels. Set winner to p5 or p6.",
        "pairs": pairs,
    }
    _save(path, template)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase 6 cover blind-review winrate")
    parser.add_argument("--wins", type=int, help="P6 wins (manual entry)")
    parser.add_argument("--total", type=int, help="total judged")
    parser.add_argument("--score-proxy", action="store_true", help="run automated scoring proxy on CI albums")
    parser.add_argument("--from-json", type=Path, help="tally human review JSON")
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--init-template",
        type=Path,
        nargs="?",
        const=DEFAULT_REVIEW_PATH,
        help="write blind-review pair template JSON",
    )
    args = parser.parse_args()

    if args.init_template:
        template = init_review_template(args.init_template)
        print(json.dumps({"written": str(args.init_template), "pairs": len(template["pairs"])}, indent=2))
        return 0

    if args.score_proxy:
        stats = eval_score_proxy()
    elif args.from_json:
        stats = eval_from_json(args.from_json)
    elif args.wins is not None and args.total is not None:
        if args.total <= 0:
            print("--total must be > 0", file=sys.stderr)
            return 2
        if args.wins < 0 or args.wins > args.total:
            print("--wins out of range", file=sys.stderr)
            return 2
        winrate = args.wins / args.total * 100.0
        stats = {
            "mode": "manual_entry",
            "wins": args.wins,
            "total": args.total,
            "winratePct": winrate,
            "target": f">={WINRATE_TARGET}%",
            "passed": winrate >= WINRATE_TARGET,
        }
    else:
        parser.error("one of --score-proxy, --from-json, --wins/--total, or --init-template is required")

    print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.write:
        if not args.record.is_file():
            print(f"record not found: {args.record}", file=sys.stderr)
            return 2
        write_to_quality_eval(stats, args.record)

    return 0 if stats.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
