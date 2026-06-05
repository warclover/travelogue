"""Cover scoring V2 pairwise calibration (Phase D · v2.1).

Usage:
  python scripts/cover_scoring_calibrate.py --export-features docs/acceptance-records/algorithm-v2-signoff.json
  python scripts/cover_scoring_calibrate.py --fit-proxy --albums tests/fixtures/cover_v2_kendall_albums.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FEATURE_KEYS = (
    "layout_fit",
    "media",
    "sharpness",
    "color",
    "thirds",
    "person",
    "face_bbox",
    "date_confidence",
)


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def export_feature_matrix(signoff_path: Path) -> dict:
    from travelogue.curation.cover_scoring_v2 import extract_cover_features

    data = json.loads(signoff_path.read_text(encoding="utf-8"))
    pairs = data.get("pairs") or []
    out_rows: list[dict] = []
    for pair in pairs:
        assets = pair.get("assets") or []
        if not assets:
            continue
        layout = pair.get("exportLayout") or "mobile"
        for asset in assets:
            aid = asset.get("id")
            if not aid:
                continue
            feats = extract_cover_features(asset, layout, assets)
            out_rows.append({"albumId": pair.get("albumId"), "assetId": aid, "features": feats})
    return {"rows": out_rows, "pairCount": len(pairs), "rowCount": len(out_rows)}


def _feature_row(features: dict[str, float]) -> list[float]:
    return [float(features.get(k, 0.0)) for k in FEATURE_KEYS]


def _logit_from_features(features: dict[str, float], weights: list[float]) -> float:
    row = _feature_row(features)
    return sum(w * f for w, f in zip(weights, row, strict=True))


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


def build_proxy_pairwise(albums_path: Path) -> list[dict]:
    """Top-1 vs rank-2/3 within each album (v2 ranking) for proxy calibration."""
    from travelogue.curation.cover_scoring_v2 import extract_cover_features
    from travelogue.curation.curate_scoring import score_ranked_cover_ids

    spec = json.loads(albums_path.read_text(encoding="utf-8"))
    albums = spec if isinstance(spec, list) else spec.get("albums") or []
    out: list[dict] = []
    for album in albums:
        assets = _load_album_assets(album)
        if len(assets) < 2:
            continue
        layout = album.get("exportLayout") or album.get("export_layout") or "mobile"
        ranked = score_ranked_cover_ids(
            assets,
            export_layout=layout,
            scoring_version="v2",
            limit=min(3, len(assets)),
        )
        if len(ranked) < 2:
            continue
        winner_id = str(ranked[0]["assetId"])
        winner_feats = extract_cover_features(
            next(a for a in assets if a["id"] == winner_id),
            layout,
            assets,
        )
        for row in ranked[1:]:
            loser_id = str(row["assetId"])
            loser = next(a for a in assets if a["id"] == loser_id)
            loser_feats = extract_cover_features(loser, layout, assets)
            out.append(
                {
                    "albumId": album.get("albumId") or album.get("id"),
                    "winnerId": winner_id,
                    "loserId": loser_id,
                    "winnerFeatures": winner_feats,
                    "loserFeatures": loser_feats,
                }
            )
    return out


def fit_bradley_terry(
    comparisons: list[dict],
    *,
    steps: int = 800,
    lr: float = 0.05,
    layout_cap: float = 0.20,
) -> dict:
    """Logistic on feature deltas with non-negative weights."""
    if not comparisons:
        return {"weights": {}, "loss": None, "comparisons": 0}

    n = len(FEATURE_KEYS)
    weights = [1.0 / n] * n
    best_loss = float("inf")
    best_weights = list(weights)

    for _ in range(steps):
        grad = [0.0] * n
        loss = 0.0
        for cmp in comparisons:
            wf = cmp["winnerFeatures"]
            lf = cmp["loserFeatures"]
            delta = [
                float(wf.get(k, 0.0)) - float(lf.get(k, 0.0)) for k in FEATURE_KEYS
            ]
            logit_diff = sum(w * d for w, d in zip(weights, delta, strict=True))
            p = _sigmoid(logit_diff)
            loss -= math.log(max(p, 1e-9))
            coeff = p - 1.0
            for i, d in enumerate(delta):
                grad[i] += coeff * d

        if loss < best_loss:
            best_loss = loss
            best_weights = list(weights)

        scale = max(len(comparisons), 1)
        for i in range(n):
            weights[i] -= lr * grad[i] / scale
            weights[i] = max(0.0, weights[i])
        if FEATURE_KEYS[0] == "layout_fit":
            weights[0] = min(weights[0], layout_cap)
        total = sum(weights) or 1.0
        weights = [w / total for w in weights]

    return {
        "weights": {k: round(w, 4) for k, w in zip(FEATURE_KEYS, best_weights, strict=True)},
        "loss": round(best_loss, 4),
        "comparisons": len(comparisons),
    }


def loo_pairwise_accuracy(comparisons: list[dict]) -> dict:
    """Leave-one-album-out proxy accuracy (D-M1 skeleton)."""
    if not comparisons:
        return {"accuracy": None, "folds": 0}
    by_album: dict[str, list[dict]] = {}
    for cmp in comparisons:
        by_album.setdefault(str(cmp.get("albumId") or ""), []).append(cmp)

    correct = 0
    total = 0
    folds = 0
    for holdout_album in by_album:
        train = [c for c in comparisons if str(c.get("albumId") or "") != holdout_album]
        test = by_album[holdout_album]
        if not train or not test:
            continue
        fit = fit_bradley_terry(train, steps=400)
        w = [fit["weights"].get(k, 0.0) for k in FEATURE_KEYS]
        folds += 1
        for cmp in test:
            delta = [
                float(cmp["winnerFeatures"].get(k, 0.0)) - float(cmp["loserFeatures"].get(k, 0.0))
                for k in FEATURE_KEYS
            ]
            logit_diff = sum(wi * d for wi, d in zip(w, delta, strict=True))
            total += 1
            if logit_diff >= 0:
                correct += 1

    acc = round(correct / total, 4) if total else None
    return {
        "accuracy": acc,
        "correct": correct,
        "total": total,
        "folds": folds,
        "gateD_M1": acc is not None and acc >= 0.70,
    }


def fit_proxy(albums_path: Path) -> dict:
    comparisons = build_proxy_pairwise(albums_path)
    fit = fit_bradley_terry(comparisons)
    loo = loo_pairwise_accuracy(comparisons)
    return {"fit": fit, "loo": loo, "albumsPath": str(albums_path.relative_to(ROOT))}


def main() -> int:
    parser = argparse.ArgumentParser(description="Cover V2 calibration utilities")
    parser.add_argument("--export-features", type=Path, help="signoff JSON with pair assets")
    parser.add_argument("--fit-proxy", action="store_true", help="proxy Bradley-Terry on album fixture")
    parser.add_argument(
        "--albums",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "cover_v2_kendall_albums.json",
    )
    parser.add_argument("--out", type=Path, help="write JSON report")
    args = parser.parse_args()

    if args.export_features:
        path = args.export_features
        if not path.is_file():
            print(f"not found: {path}", file=sys.stderr)
            return 2
        payload = export_feature_matrix(path)
    elif args.fit_proxy:
        if not args.albums.is_file():
            print(f"albums not found: {args.albums}", file=sys.stderr)
            return 2
        payload = fit_proxy(args.albums)
    else:
        parser.error("specify --export-features or --fit-proxy")

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
