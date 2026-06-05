"""Compute Kendall tau between cover scoring v1 and v2 on album fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _kendall_tau(rank_a: list[str], rank_b: list[str]) -> float:
    common = [x for x in rank_a if x in rank_b]
    n = len(common)
    if n < 2:
        return 1.0
    pos_a = {aid: i for i, aid in enumerate(rank_a)}
    pos_b = {aid: i for i, aid in enumerate(rank_b)}
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            a_i, a_j = common[i], common[j]
            da = pos_a[a_i] - pos_a[a_j]
            db = pos_b[a_i] - pos_b[a_j]
            if da * db > 0:
                concordant += 1
            elif da * db < 0:
                discordant += 1
    denom = concordant + discordant
    if denom == 0:
        return 1.0
    return (concordant - discordant) / denom


def rank_ids(assets: list[dict], *, export_layout: str, version: str) -> list[str]:
    from travelogue.curation.curate_scoring import score_ranked_cover_ids

    rows = score_ranked_cover_ids(
        assets,
        export_layout=export_layout,
        scoring_version=version,
        limit=len(assets),
    )
    return [str(row["assetId"]) for row in rows]


def eval_album(assets: list[dict], *, export_layout: str = "mobile") -> dict:
    v1 = rank_ids(assets, export_layout=export_layout, version="v1")
    v2 = rank_ids(assets, export_layout=export_layout, version="v2")
    tau = _kendall_tau(v1, v2)
    return {
        "exportLayout": export_layout,
        "kendallTau": round(tau, 4),
        "v1Top3": v1[:3],
        "v2Top3": v2[:3],
        "coverChanged": (v1[0] if v1 else "") != (v2[0] if v2 else ""),
    }


def _load_album_assets(album: dict) -> list[dict]:
    assets = album.get("assets")
    if isinstance(assets, list) and assets:
        return assets
    trip_dir = album.get("tripDir") or album.get("trip_dir")
    if not trip_dir:
        return []
    trip_path = (ROOT / str(trip_dir) / "trip.json").resolve()
    if not trip_path.is_file():
        return []
    trip = json.loads(trip_path.read_text(encoding="utf-8"))
    return list(trip.get("assets") or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Kendall tau v1 vs v2 cover ranking")
    parser.add_argument("--albums", type=Path, help="JSON list of {assets: [...]}")
    parser.add_argument("--layout", default="mobile", choices=("mobile", "web"))
    parser.add_argument(
        "--write-report",
        type=Path,
        nargs="?",
        const=ROOT / "docs" / "reports" / "algorithm-v2-kendall.md",
        help="write markdown report (default path under docs/reports/)",
    )
    args = parser.parse_args()

    default_fixture = ROOT / "tests" / "fixtures" / "cover_v2_kendall_albums.json"
    albums_path = (
        args.albums
        or default_fixture
        if default_fixture.is_file()
        else ROOT / "docs" / "acceptance-records" / "cover-selection-albums.json"
    )
    if not albums_path.is_file():
        print(f"albums file not found: {albums_path}", file=sys.stderr)
        return 2

    spec = json.loads(albums_path.read_text(encoding="utf-8"))
    if isinstance(spec, list):
        albums = spec
    else:
        albums = spec.get("albums") or []
    rows = []
    for album in albums:
        assets = _load_album_assets(album)
        if not assets:
            continue
        layout = album.get("exportLayout") or album.get("export_layout") or args.layout
        row = eval_album(assets, export_layout=layout)
        row["albumId"] = album.get("albumId") or album.get("id")
        row["assetCount"] = len(assets)
        rows.append(row)

    taus = [r["kendallTau"] for r in rows if r.get("kendallTau") is not None]
    summary = {
        "albums": len(rows),
        "meanKendallTau": round(sum(taus) / len(taus), 4) if taus else None,
        "coverChanges": sum(1 for r in rows if r.get("coverChanged")),
        "rows": rows,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.write_report:
        lines = [
            "# Algorithm V2 · Kendall τ Report",
            "",
            f"- Source: `{albums_path.relative_to(ROOT)}`",
            f"- Albums: **{summary['albums']}**",
            f"- Mean Kendall τ: **{summary['meanKendallTau']}** (gate A-M1 ≥ 0.85)",
            f"- Cover changes (top-1): **{summary['coverChanges']}** (gate A-M7 ≤ 3/10)",
            "",
            "> 故意 v1/v2 排序反转（如 `dateConfidence=low` 高清晰度图）不计入本报告；见 `test_v2_demotes_low_date_confidence_vs_v1`。",
            "",
            "| albumId | τ | coverChanged | v1Top3 | v2Top3 |",
            "|---------|---|--------------|--------|--------|",
        ]
        for row in rows:
            lines.append(
                f"| {row.get('albumId', '')} | {row.get('kendallTau')} | "
                f"{row.get('coverChanged')} | {row.get('v1Top3')} | {row.get('v2Top3')} |"
            )
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"report: {args.write_report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
