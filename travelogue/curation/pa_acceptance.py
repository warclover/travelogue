"""PA · offline acceptance helpers (SRCC + blind-review export)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.aesthetic_score import aesthetic_overall, build_aesthetic_explain


def _rank_data(values: list[float]) -> list[float]:
    """Average ranks for ties (Spearman)."""
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # 1-based ranks
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_srcc(human: list[float], predicted: list[float]) -> float | None:
    """Spearman rank correlation; ``None`` when insufficient data."""
    if len(human) != len(predicted) or len(human) < 3:
        return None
    pairs = [(float(h), float(p)) for h, p in zip(human, predicted, strict=True)]
    if len({h for h, _ in pairs}) < 2 or len({p for _, p in pairs}) < 2:
        return None
    hr = _rank_data([h for h, _ in pairs])
    pr = _rank_data([p for _, p in pairs])
    n = float(len(pairs))
    mean_h = sum(hr) / n
    mean_p = sum(pr) / n
    num = sum((h - mean_h) * (p - mean_p) for h, p in zip(hr, pr, strict=True))
    den_h = sum((h - mean_h) ** 2 for h in hr) ** 0.5
    den_p = sum((p - mean_p) ** 2 for p in pr) ** 0.5
    if den_h <= 0 or den_p <= 0:
        return None
    return num / (den_h * den_p)


def srcc_from_label_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute SRCC from label rows with ``humanScore`` + ``predictedOverall``."""
    human: list[float] = []
    predicted: list[float] = []
    used = 0
    for row in rows:
        try:
            h = float(row["humanScore"])
            p = float(row.get("predictedOverall", row.get("overall")))
        except (KeyError, TypeError, ValueError):
            continue
        human.append(h)
        predicted.append(p)
        used += 1
    srcc = spearman_srcc(human, predicted)
    return {
        "sampleCount": used,
        "srcc": None if srcc is None else round(srcc, 4),
    }


def _top_by_score(
    assets: list[dict],
    score_fn,
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    ranked: list[tuple[float, dict]] = []
    for asset in assets:
        if asset.get("type") == "video":
            continue
        try:
            score = float(score_fn(asset))
        except (TypeError, ValueError):
            continue
        ranked.append((score, asset))
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("id") or "")))
    out: list[dict[str, Any]] = []
    for score, asset in ranked[:limit]:
        aid = str(asset.get("id") or "")
        row: dict[str, Any] = {
            "assetId": aid,
            "score": round(score, 4),
            "overall": aesthetic_overall(asset),
        }
        explain = build_aesthetic_explain(asset, limit=3)
        if explain:
            row["explainTop3"] = explain
        out.append(row)
    return out


def export_pa_blind_review(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    bucket: list[str] | None = None,
) -> dict[str, Any]:
    """Export U-COVER / U-HERO / U-SOLO top picks for human blind review."""
    from travelogue.config import get_config
    from travelogue.curation.curate_scoring import (
        build_cover_layout_review,
        hero_score,
        median_sharpness,
        pick_chapter_hero,
        pick_cover_asset_id,
    )
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.curation.solo_scoring import (
        pick_solo_asset_id,
        solo_score,
        sort_ids_by_solo_score,
    )

    cfg = get_config()
    cs = cfg.curate.cover_scoring
    p6 = cs.enable_phase6_factors
    pool = [a for a in assets if a.get("layoutEligible", True) is not False]
    cover_id = pick_cover_asset_id(
        pool,
        export_layout=export_layout,
        featured_weight=cfg.curate.featured_weight,
        enable_phase6_cover_factors=p6,
        cover_scoring=cs,
    )
    cover_review = build_cover_layout_review(
        pool,
        cover_id,
        export_layout=export_layout,
        featured_weight=cfg.curate.featured_weight,
        enable_phase6_cover_factors=p6,
        cover_scoring=cs,
    )
    med_sharp = median_sharpness(pool)
    aspects = {str(a["id"]): aspect_kind_for_asset(a) for a in pool if a.get("id")}
    assets_by_id = {str(a["id"]): a for a in pool if a.get("id")}
    hero_bucket = bucket or [aid for aid in assets_by_id if aspects.get(aid) in ("landscape", "panorama")]
    hero_id = pick_chapter_hero(
        hero_bucket,
        assets_by_id,
        median_sharp=med_sharp,
        featured_weight=cfg.curate.featured_weight,
    )
    solo_candidates = hero_bucket or list(assets_by_id.keys())
    solo_id = pick_solo_asset_id(
        solo_candidates,
        assets_by_id,
        chapter_peer_ids=list(assets_by_id.keys()),
        exclude={cover_id} if cover_id else set(),
    )
    solo_ranked_ids = sort_ids_by_solo_score(
        solo_candidates,
        assets_by_id,
        exclude={cover_id} if cover_id else set(),
    )
    return {
        "exportLayout": export_layout,
        "cover": {
            "coverAssetId": cover_id,
            "scoreRankedTop3": cover_review.get("scoreRankedTop3"),
            "coverExplain": cover_review.get("coverExplain"),
        },
        "hero": {
            "heroAssetId": hero_id,
            "top3": _top_by_score(
                [assets_by_id[aid] for aid in hero_bucket if aid in assets_by_id],
                lambda a: hero_score(a, median_sharp=med_sharp),
            ),
        },
        "solo": {
            "soloAssetId": solo_id,
            "top3": _top_by_score(
                [assets_by_id[aid] for aid in solo_ranked_ids[:10] if aid in assets_by_id],
                lambda a: solo_score(
                    a,
                    peer_assets=list(assets_by_id.values()),
                    exclude_ids={cover_id} if cover_id else set(),
                ),
            ),
        },
    }
