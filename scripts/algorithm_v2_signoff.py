"""Algorithm V2 acceptance record helpers (R0' blind review + automated gates).

Usage:
  python scripts/algorithm_v2_signoff.py --init-template
  python scripts/algorithm_v2_signoff.py --score-automated --write
  python scripts/algorithm_v2_signoff.py --from-json docs/acceptance-records/algorithm-v2-signoff.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_kendall_module():
    path = ROOT / "scripts" / "cover_scoring_v2_kendall.py"
    spec = importlib.util.spec_from_file_location("cover_scoring_v2_kendall", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
DEFAULT_SIGNOFF = ROOT / "docs" / "acceptance-records" / "algorithm-v2-signoff.json"
KENDALL_FIXTURE = ROOT / "tests" / "fixtures" / "cover_v2_kendall_albums.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pairs_from_kendall(albums_path: Path) -> list[dict]:
    spec = _load(albums_path)
    albums = spec if isinstance(spec, list) else spec.get("albums") or []
    kendall = _load_kendall_module()
    pairs: list[dict] = []
    for album in albums:
        assets = kendall._load_album_assets(album)
        if not assets:
            continue
        layout = album.get("exportLayout") or album.get("export_layout") or "mobile"
        pairs.append(
            {
                "albumId": album.get("albumId") or album.get("id"),
                "exportLayout": layout,
                "assets": assets,
            }
        )
    return pairs


def _album_rows(albums_path: Path) -> list[dict]:
    kendall = _load_kendall_module()
    _load_album_assets = kendall._load_album_assets
    eval_album = kendall.eval_album
    rank_ids = kendall.rank_ids

    spec = _load(albums_path)
    albums = spec if isinstance(spec, list) else spec.get("albums") or []
    rows: list[dict] = []
    for album in albums:
        assets = _load_album_assets(album)
        if not assets:
            continue
        layout = album.get("exportLayout") or album.get("export_layout") or "mobile"
        v1_top = rank_ids(assets, export_layout=layout, version="v1")
        v2_top = rank_ids(assets, export_layout=layout, version="v2")
        eval_row = eval_album(assets, export_layout=layout)
        rows.append(
            {
                "albumId": album.get("albumId") or album.get("id"),
                "exportLayout": layout,
                "tags": album.get("tags") or [],
                "assetCount": len(assets),
                "v1CoverAssetId": v1_top[0] if v1_top else None,
                "v2CoverAssetId": v2_top[0] if v2_top else None,
                "coverChanged": eval_row.get("coverChanged"),
                "kendallTau": eval_row.get("kendallTau"),
                "v1Top3": eval_row.get("v1Top3"),
                "v2Top3": eval_row.get("v2Top3"),
                "judgeVerdict": None,
                "judgeReasonTags": [],
                "notes": "Fill judgeVerdict=A|B|C after blind human review (v2 vs v1 cover).",
            }
        )
    return rows


def init_template(*, albums_path: Path, out_path: Path) -> dict:
    rows = _album_rows(albums_path)
    return {
        "recordId": "algorithm-v2-signoff",
        "version": "1",
        "scoringVersion": "v2",
        "instructions": (
            "Blind review: compare v2 cover (candidate) vs v1 cover (baseline) per album. "
            "Verdict A=v2 better, B=tie, C=v1 better. Automated gates in `automated`."
        ),
        "targets": {
            "aM1": {"kendallTauMin": 0.85, "albumCount": 10},
            "aM3": {"aRateMin": 6, "abRateMin": 9, "totalAlbums": 10},
            "aM7": {"maxCoverChanges": 3, "totalAlbums": 10},
        },
        "automated": None,
        "albums": rows,
        "pairs": _pairs_from_kendall(albums_path),
        "notes": (
            "Synthetic albums from cover_v2_kendall_albums.json until trips/mao land. "
            "Replace albums[] with real tripDir entries from cover-selection-albums.json."
        ),
    }


def score_automated(*, albums_path: Path) -> dict:
    kendall = _load_kendall_module()
    _load_album_assets = kendall._load_album_assets
    eval_album = kendall.eval_album

    spec = _load(albums_path)
    albums = spec if isinstance(spec, list) else spec.get("albums") or []
    rows = []
    for album in albums:
        assets = _load_album_assets(album)
        if not assets:
            continue
        layout = album.get("exportLayout") or album.get("export_layout") or "mobile"
        row = eval_album(assets, export_layout=layout)
        row["albumId"] = album.get("albumId") or album.get("id")
        rows.append(row)
    taus = [r["kendallTau"] for r in rows if r.get("kendallTau") is not None]
    cover_changes = sum(1 for r in rows if r.get("coverChanged"))
    mean_tau = round(sum(taus) / len(taus), 4) if taus else None
    return {
        "source": str(albums_path.relative_to(ROOT)),
        "albumCount": len(rows),
        "meanKendallTau": mean_tau,
        "coverChanges": cover_changes,
        "gates": {
            "aM1": mean_tau is not None and mean_tau >= 0.85,
            "aM7": cover_changes <= 3,
        },
        "rows": rows,
    }


def validate_signoff(data: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    auto = data.get("automated") or {}
    targets = data.get("targets") or {}
    a_m1 = targets.get("aM1") or {}
    a_m7 = targets.get("aM7") or {}
    mean_tau = auto.get("meanKendallTau")
    if mean_tau is not None and mean_tau < float(a_m1.get("kendallTauMin", 0.85)):
        issues.append(f"A-M1 failed: mean Kendall τ={mean_tau}")
    cover_changes = auto.get("coverChanges")
    if cover_changes is not None and cover_changes > int(a_m7.get("maxCoverChanges", 3)):
        issues.append(f"A-M7 failed: coverChanges={cover_changes}")
    albums = data.get("albums") or []
    judged = [a for a in albums if a.get("judgeVerdict")]
    if judged:
        a_count = sum(1 for a in judged if a.get("judgeVerdict") == "A")
        ab_count = sum(1 for a in judged if a.get("judgeVerdict") in ("A", "B"))
        a_m3 = targets.get("aM3") or {}
        if a_count < int(a_m3.get("aRateMin", 6)):
            issues.append(f"A-M3 failed: A rate={a_count}/{len(judged)}")
        if ab_count < int(a_m3.get("abRateMin", 9)):
            issues.append(f"A-M3 failed: A+B rate={ab_count}/{len(judged)}")
    return not issues, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Algorithm V2 signoff record")
    parser.add_argument("--init-template", action="store_true", help="write signoff JSON template")
    parser.add_argument("--score-automated", action="store_true", help="compute automated gates")
    parser.add_argument("--from-json", type=Path, help="validate existing signoff record")
    parser.add_argument("--albums", type=Path, default=KENDALL_FIXTURE)
    parser.add_argument("--out", type=Path, default=DEFAULT_SIGNOFF)
    parser.add_argument("--write", action="store_true", help="persist updates to --out")
    args = parser.parse_args()

    if args.init_template:
        payload = init_template(albums_path=args.albums, out_path=args.out)
        if args.score_automated or args.write:
            payload["automated"] = score_automated(albums_path=args.albums)
        if args.write:
            _save(args.out, payload)
            print(f"wrote {args.out}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.score_automated:
        summary = score_automated(albums_path=args.albums)
        if args.write and args.out.is_file():
            data = _load(args.out)
            data["automated"] = summary
            _save(args.out, data)
            print(f"updated automated gates in {args.out}")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if args.from_json:
        data = _load(args.from_json)
        ok, issues = validate_signoff(data)
        print(json.dumps({"ok": ok, "issues": issues}, indent=2, ensure_ascii=False))
        return 0 if ok else 1

    parser.error("specify --init-template, --score-automated, or --from-json")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
