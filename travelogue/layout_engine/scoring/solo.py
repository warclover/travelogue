"""U-SOLO · single-image emphasis scoring (PA-T09).

Picks photos suited for full-screen / cross-page emphasis. Formula (design §3.3):

    solo_score = overall × (0.5 + 0.5·lighting) × (0.6 + 0.4·negSpace)
                 × uniqueness × (1 − dup_penalty)

Fail-open: missing aesthetic fields fall back to neutral multipliers; excluded
ids (cover / chapter hero) score 0.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall

_aesthetic = __import__(
    "travelogue.curation.aesthetic_score",
    fromlist=["aesthetic_dim", "asset_aesthetic", "purpose_overall"],
)
aesthetic_dim = _aesthetic.aesthetic_dim
asset_aesthetic = _aesthetic.asset_aesthetic
purpose_overall = _aesthetic.purpose_overall
from travelogue.media.color_metrics import delta_e_cie76, triangular_score
from travelogue.media.quality import asset_sharpness

_SOLO_FACTOR_LABELS: dict[str, str] = {
    "overall": "总体美感",
    "lighting": "光影",
    "negative_space": "留白",
    "uniqueness": "色调独特性",
    "duplicate": "重复惩罚",
}


def _resolve_solo_enabled(enabled: bool | None) -> bool:
    if enabled is not None:
        return enabled
    try:
        from travelogue.config import get_config

        return get_config().aesthetic.enabled
    except Exception:
        return False


def negative_space_factor(asset: dict) -> float:
    """0.6 + 0.4·negSpace — enough margin for overlay copy."""
    ae = asset_aesthetic(asset)
    if ae and isinstance(ae.get("signals"), dict):
        raw = ae["signals"].get("negativeSpace")
        if raw is not None:
            return 0.6 + 0.4 * float(raw)
    box = asset.get("salientBox")
    if isinstance(box, dict):
        try:
            area = float(box.get("w", 0.0)) * float(box.get("h", 0.0))
        except (TypeError, ValueError):
            area = 0.0
        if area > 0:
            ns = triangular_score(area, low=0.02, peak=0.25, high=0.75)
            return 0.6 + 0.4 * ns
    return 0.6 + 0.4 * 0.5


def lighting_factor(asset: dict) -> float:
    """0.5 + 0.5·lighting dim."""
    lighting = aesthetic_dim(asset, "lighting")
    val = 0.5 if lighting is None else float(lighting)
    return 0.5 + 0.5 * val


def tone_uniqueness(asset: dict, peer_assets: list[dict]) -> float:
    """Higher when dominant tone differs from chapter peers (ΔE76 proxy)."""
    tone = asset.get("dominantTone")
    if not isinstance(tone, str) or not tone.startswith("#"):
        return 0.5
    aid = asset.get("id")
    peer_tones: list[str] = []
    for peer in peer_assets:
        if peer.get("id") == aid:
            continue
        pt = peer.get("dominantTone")
        if isinstance(pt, str) and pt.startswith("#"):
            peer_tones.append(pt)
    if not peer_tones:
        return 1.0
    scores: list[float] = []
    for pt in peer_tones:
        de = delta_e_cie76(tone, pt)
        if de >= 120.0:
            scores.append(0.85)
        elif de < 15.0:
            scores.append(0.15 + 0.15 * (de / 15.0))
        else:
            scores.append(triangular_score(de, low=15.0, peak=55.0, high=120.0))
    return sum(scores) / len(scores)


def duplicate_penalty(
    asset: dict,
    *,
    used_asset_ids: set[str] | None = None,
    exclude_ids: set[str] | None = None,
    assets_by_id: Mapping[str, dict] | None = None,
) -> float:
    """Return penalty in [0, 1]; 1 means exclude entirely."""
    aid = str(asset.get("id") or "")
    if exclude_ids and aid in exclude_ids:
        return 1.0
    used = used_asset_ids or set()
    if aid in used:
        return 0.6
    burst = asset.get("burstGroupId")
    if burst and assets_by_id:
        for uid in used:
            other = assets_by_id.get(uid) or {}
            if other.get("burstGroupId") == burst:
                return 0.4
    return 0.0


def solo_score(
    asset: dict,
    *,
    peer_assets: list[dict] | None = None,
    used_asset_ids: set[str] | None = None,
    exclude_ids: set[str] | None = None,
    assets_by_id: Mapping[str, dict] | None = None,
    aesthetic_enabled: bool | None = None,
) -> float:
    aid = str(asset.get("id") or "")
    if exclude_ids and aid in exclude_ids:
        return 0.0

    if not _resolve_solo_enabled(aesthetic_enabled):
        return aesthetic_overall(asset) or 0.5

    overall = purpose_overall(asset, "solo")
    if overall is None:
        overall = aesthetic_overall(asset)
    base = overall if overall is not None else 0.5

    peers = list(peer_assets or [])
    if not peers and assets_by_id:
        peers = [
            assets_by_id[k]
            for k in assets_by_id
            if k != aid and isinstance(assets_by_id.get(k), dict)
        ]

    dup = duplicate_penalty(
        asset,
        used_asset_ids=used_asset_ids,
        exclude_ids=exclude_ids,
        assets_by_id=assets_by_id,
    )
    return (
        base
        * lighting_factor(asset)
        * negative_space_factor(asset)
        * tone_uniqueness(asset, peers)
        * (1.0 - dup)
    )


def pick_solo_asset_id(
    candidate_ids: list[str],
    assets_by_id: Mapping[str, dict],
    *,
    chapter_peer_ids: list[str] | None = None,
    exclude: set[str] | None = None,
    used_solo_ids: set[str] | None = None,
    aesthetic_enabled: bool | None = None,
) -> str | None:
    """Best U-SOLO candidate; sharpness tiebreak."""
    if not candidate_ids:
        return None
    exclude = exclude or set()
    peers = [
        assets_by_id[aid]
        for aid in (chapter_peer_ids or [])
        if aid in assets_by_id
    ]
    best_id: str | None = None
    best_score = -1.0
    best_sharp = -1.0
    for aid in candidate_ids:
        if aid in exclude:
            continue
        asset = assets_by_id.get(aid)
        if not asset:
            continue
        score = solo_score(
            asset,
            peer_assets=peers,
            used_asset_ids=used_solo_ids,
            exclude_ids=exclude,
            assets_by_id=assets_by_id,
            aesthetic_enabled=aesthetic_enabled,
        )
        sharp = asset_sharpness(asset)
        if score > best_score or (score == best_score and sharp > best_sharp):
            best_score = score
            best_sharp = sharp
            best_id = aid
    if best_id:
        return best_id
    for aid in candidate_ids:
        if aid not in exclude:
            return aid
    return None


def sort_ids_by_solo_score(
    asset_ids: list[str],
    assets_by_id: Mapping[str, dict],
    *,
    chapter_peer_ids: list[str] | None = None,
    exclude: set[str] | None = None,
    used_solo_ids: set[str] | None = None,
    aesthetic_enabled: bool | None = None,
) -> list[str]:
    peers = [
        assets_by_id[aid]
        for aid in (chapter_peer_ids or list(assets_by_id.keys()))
        if aid in assets_by_id
    ]
    exclude = exclude or set()

    def _key(aid: str) -> tuple[float, float]:
        asset = assets_by_id.get(aid, {})
        return (
            solo_score(
                asset,
                peer_assets=peers,
                used_asset_ids=used_solo_ids,
                exclude_ids=exclude,
                assets_by_id=assets_by_id,
                aesthetic_enabled=aesthetic_enabled,
            ),
            asset_sharpness(asset),
        )

    return sorted(asset_ids, key=_key, reverse=True)


def build_solo_explain(
    asset: dict,
    *,
    peer_assets: list[dict] | None = None,
    exclude_ids: set[str] | None = None,
    aesthetic_enabled: bool | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Top readable factors for solo score (mirrors ``build_cover_explain``)."""
    if exclude_ids and str(asset.get("id") or "") in exclude_ids:
        return []
    factors: list[tuple[str, float]] = []
    overall = aesthetic_overall(asset)
    if overall is not None and overall != 0.5:
        factors.append(("overall", overall))
    lit = lighting_factor(asset)
    if abs(lit - 0.75) > 0.05:
        factors.append(("lighting", lit))
    neg = negative_space_factor(asset)
    if abs(neg - 0.8) > 0.05:
        factors.append(("negative_space", neg))
    peers = peer_assets or []
    uniq = tone_uniqueness(asset, peers)
    if abs(uniq - 0.5) > 0.08:
        factors.append(("uniqueness", uniq))
    dup = duplicate_penalty(asset, exclude_ids=exclude_ids)
    if dup > 0.05:
        factors.append(("duplicate", 1.0 - dup))
    ranked = sorted(factors, key=lambda item: abs(item[1] - 0.5), reverse=True)
    out: list[dict[str, Any]] = []
    for code, value in ranked[:limit]:
        label = _SOLO_FACTOR_LABELS.get(code, code)
        direction = "突出" if value >= 0.55 else ("中等" if value >= 0.4 else "偏弱")
        out.append(
            {
                "code": code,
                "label": label,
                "score": round(float(value), 3),
                "reason": f"{label}表现{direction}",
            }
        )
    return out
