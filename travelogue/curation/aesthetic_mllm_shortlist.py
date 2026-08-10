"""AA · MLLM shortlist / blend / oracle · ACP M4 / D-ACP-16.

Business logic that depends on curation scoring & album profile. Single-image
vision scoring is delegated to ``travelogue.ai.agents.aesthetic_mllm_adapter``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from travelogue.ai.agents.aesthetic_mllm_adapter import (
    mllm_cache_key,
    mllm_cache_path,
    score_image_with_mllm,
)
from travelogue.config import AestheticConfig, AestheticMllmConfig
from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset
from travelogue.curation.aesthetic_score import purpose_overall, refresh_aesthetic_ml_blend
from travelogue.curation.album_profile import (
    album_profile_for_trip,
    effective_priority_strata,
    stratum_preference_for_trip,
)

_log = logging.getLogger(__name__)


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _log.debug("mllm cache read skipped for %s", path, exc_info=True)
        return {}
    return raw if isinstance(raw, dict) else {}


def _save_cache(path: Path, cache: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _rank_mllm_candidates(
    assets: list[dict],
    purpose: str,
    *,
    cfg: AestheticConfig,
    priority_strata: frozenset[str],
) -> list[tuple[float, dict]]:
    ranked: list[tuple[float, dict]] = []
    for asset in assets:
        if asset.get("type", "image") == "video":
            continue
        aid = str(asset.get("id") or "")
        if not aid:
            continue
        val = purpose_overall(asset, purpose, cfg=cfg)  # type: ignore[arg-type]
        if val is None:
            continue
        ranked.append((float(val), asset))

    def sort_key(t: tuple[float, dict]) -> tuple[int, float, str]:
        score, asset = t
        if priority_strata:
            stratum = review_stratum_for_asset(asset)
            in_priority = 0 if stratum in priority_strata else 1
            return (in_priority, -score, str(asset.get("id") or ""))
        return (0, -score, str(asset.get("id") or ""))

    ranked.sort(key=sort_key)
    return ranked


def build_mllm_shortlist(
    assets: list[dict],
    *,
    cfg: AestheticConfig,
    album_profile: dict | None = None,
    trip: dict | None = None,
) -> list[tuple[str, dict, str]]:
    """Return ``(asset_id, asset, purpose)`` tuples for MLLM scoring."""
    mllm = cfg.mllm
    if not mllm.enabled:
        return []
    if album_profile is None and trip is not None:
        album_profile = album_profile_for_trip(trip)
    preference = stratum_preference_for_trip(trip) if trip is not None else "auto"
    priority_strata = effective_priority_strata(album_profile, preference=preference)
    k = max(1, int(mllm.shortlist_k))
    out: list[tuple[str, dict, str]] = []
    seen: set[str] = set()
    for purpose in mllm.shortlist_purposes:
        ranked = _rank_mllm_candidates(
            assets, purpose, cfg=cfg, priority_strata=priority_strata
        )
        for _, asset in ranked[:k]:
            aid = str(asset["id"])
            if aid in seen:
                continue
            seen.add(aid)
            out.append((aid, asset, purpose))
            if len(out) >= int(mllm.max_calls_per_trip):
                return out
    return out[: int(mllm.max_calls_per_trip)]


def _write_mllm_fields(asset: dict, result: dict[str, Any]) -> None:
    q = asset.setdefault("quality", {})
    ae = q.setdefault("aesthetic", {})
    sig = ae.setdefault("signals", {})
    if isinstance(sig, dict):
        sig["mllmScore"] = float(result["score"])
        sig["mllmModel"] = str(result.get("model") or "")
        sig["mllmShortlist"] = str(result.get("purpose") or "")
    critique = result.get("critique")
    if critique:
        ae["critique"] = str(critique)


def apply_aesthetic_mllm_scores(
    assets: list[dict],
    *,
    trip_dir: Path,
    cfg: AestheticConfig | None = None,
    trip: dict | None = None,
) -> dict[str, Any]:
    """Score shortlist with vision LLM; fail-open when disabled or errors."""
    cfg = cfg or AestheticConfig()
    mllm = cfg.mllm
    report: dict[str, Any] = {
        "enabled": mllm.enabled,
        "scored": 0,
        "cached": 0,
        "failed": 0,
        "skipped": 0,
        "calls": 0,
    }
    if not mllm.enabled:
        return report

    shortlist = build_mllm_shortlist(assets, cfg=cfg, trip=trip)
    if not shortlist:
        return report

    cache_path = mllm_cache_path(trip_dir)
    cache = _load_cache(cache_path) if mllm.cache else {}
    cache_dirty = False
    provider = mllm.provider or "dashscope"

    for aid, asset, purpose in shortlist:
        del aid  # used for shortlist identity only
        key = mllm_cache_key(asset, model=str(mllm.model), rubric=str(mllm.rubric))
        if mllm.cache and key in cache:
            hit = cache[key]
            if isinstance(hit, dict) and hit.get("score") is not None:
                _write_mllm_fields(asset, hit)
                refresh_aesthetic_ml_blend(asset, cfg=cfg)
                report["cached"] += 1
                report["scored"] += 1
                continue

        report["calls"] += 1
        result = score_image_with_mllm(
            asset,
            trip_dir=trip_dir,
            purpose=purpose,
            cfg=mllm,
            provider=provider,
            cache=cache if mllm.cache else None,
            trip=trip,
        )
        if result is None:
            report["failed"] += 1
            continue
        _write_mllm_fields(asset, result)
        refresh_aesthetic_ml_blend(asset, cfg=cfg)
        report["scored"] += 1
        cache_dirty = True

    if cache_dirty and mllm.cache:
        _save_cache(cache_path, cache)
    return report


def apply_mllm_oracle_from_labels(
    assets: list[dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
) -> dict[str, Any]:
    """Offline oracle upper-bound: human labels as ``mllmScore`` on shortlist only."""
    from travelogue.curation.aesthetic_blind_review import normalize_human_score

    cfg = cfg or AestheticConfig(mllm=AestheticMllmConfig(enabled=True))
    labels_by_id = {str(r.get("assetId") or ""): r for r in label_rows if r.get("assetId")}
    shortlist = build_mllm_shortlist(assets, cfg=cfg)
    report: dict[str, Any] = {
        "mode": "oracle-human",
        "shortlistCount": len(shortlist),
        "scored": 0,
        "missingLabel": 0,
    }
    for aid, asset, purpose in shortlist:
        row = labels_by_id.get(aid)
        if not row or row.get("humanScore") is None:
            report["missingLabel"] += 1
            continue
        try:
            score = normalize_human_score(row["humanScore"])
        except (TypeError, ValueError):
            report["missingLabel"] += 1
            continue
        _write_mllm_fields(
            asset,
            {
                "score": round(score, 4),
                "critique": "oracle from human label",
                "model": "oracle-human",
                "purpose": purpose,
            },
        )
        refresh_aesthetic_ml_blend(asset, cfg=cfg)
        report["scored"] += 1
    return report
