"""M6 self-heal: retry before legacy when winner score is below threshold (Phase 15 · S3)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from travelogue.config import MosaicConfig
from travelogue.curation.layout_planner import AspectKind
from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic.scorer import score_candidate

_STABLE_PATTERN_IDS = frozenset(
    (
        *MOSAIC_3_PATTERN_IDS,
        *MOSAIC_4_PATTERN_IDS,
        *MOSAIC_5_PATTERN_IDS,
        *MOSAIC_6_PATTERN_IDS,
        *MOSAIC_8_PATTERN_IDS,
        *MOSAIC_9_PATTERN_IDS,
    )
)

if TYPE_CHECKING:
    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState


def _tightened_cfg(cfg: MosaicConfig) -> MosaicConfig:
    boosted = {
        k: min(1.0, float(v) * 1.35) for k, v in (cfg.penalties or {}).items()
    }
    return replace(cfg, penalties=boosted)


def _asset_drop_penalty(
    asset_id: str,
    *,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    cfg: MosaicConfig,
) -> float:
    asset = assets_map.get(asset_id) or {}
    if asset.get("featured"):
        return -1.0
    from travelogue.layout_engine.mosaic.scorer import _face_crop_penalty, _main_quality_penalty

    fake_screen = {
        "patternId": "screen-portrait-1",
        "slots": [{"assetId": asset_id, "role": "main", "fit": "cover"}],
    }
    return max(
        _face_crop_penalty(fake_screen, assets_map),
        _main_quality_penalty(fake_screen, assets_map),
    )


def try_self_heal_pick(
    scored: list[tuple[ScreenCandidate, float, list[str], dict[str, float]]],
    *,
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None,
    trip_photo_total: int,
    burst_seconds: float,
    min_score: float,
) -> tuple[ScreenCandidate, float, list[str], str, list[str], dict[str, float]] | None:
    """
    Return (winner, score, reasons, step, dropped_ids) when self-heal succeeds.
    """
    if not cfg.self_heal_enabled or not scored:
        return None

    winner_score = scored[0][1]
    if winner_score >= min_score:
        return None

    degrade_floor = min_score * 0.85
    for cand, score, reasons, penalties in sorted(scored, key=lambda t: (-t[1], t[0].pattern_id)):
        if cand.pattern_id in _STABLE_PATTERN_IDS and score >= degrade_floor:
            if score < min_score or cand.pattern_id != scored[0][0].pattern_id:
                return cand, score, reasons, "degrade_stable_pattern", [], dict(penalties)

    tight_cfg = _tightened_cfg(cfg)
    best: tuple[ScreenCandidate, float, list[str], dict[str, float]] | None = None
    for cand, _, _, _ in scored:
        sr = score_candidate(
            cand.screen,
            aspects=aspects,
            assets_by_id=assets_map,
            cfg=tight_cfg,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            burst_seconds=burst_seconds,
        )
        if sr.total >= min_score and (best is None or sr.total > best[1]):
            best = (cand, sr.total, sr.reason_codes, dict(sr.penalties))
    if best is not None:
        return best[0], best[1], best[2], "tightened_rescore", [], best[3]

    if cfg.allow_drop and len(asset_ids) > 2:
        penalties = [
            (_asset_drop_penalty(aid, aspects=aspects, assets_map=assets_map, cfg=cfg), aid)
            for aid in asset_ids
        ]
        droppable = [(p, aid) for p, aid in penalties if p >= 0]
        if droppable:
            droppable.sort(reverse=True)
            worst_pen, drop_id = droppable[0]
            if worst_pen >= 0.45:
                max_drop = max(1, int(len(asset_ids) * cfg.max_drop_ratio))
                if max_drop >= 1:
                    from travelogue.layout_engine.mosaic.candidates import generate_window_candidates

                    remaining = [a for a in asset_ids if a != drop_id]
                    size = len(remaining)
                    if size in cfg.enabled_window_sizes:
                        sub = generate_window_candidates(
                            remaining,
                            aspects,
                            assets_map,
                            cfg=cfg,
                            burst_seconds=burst_seconds,
                        )
                        if sub:
                            sub_scored: list[
                                tuple[ScreenCandidate, float, list[str], dict[str, float]]
                            ] = []
                            for c in sub:
                                sr = score_candidate(
                                    c.screen,
                                    aspects=aspects,
                                    assets_by_id=assets_map,
                                    cfg=cfg,
                                    layout_state=layout_state,
                                    trip_photo_total=trip_photo_total,
                                    burst_seconds=burst_seconds,
                                )
                                sub_scored.append(
                                    (c, sr.total, sr.reason_codes, dict(sr.penalties))
                                )
                            sub_scored.sort(key=lambda t: (-t[1], t[0].pattern_id))
                            sub_winner, sub_score, _, sub_pen = sub_scored[0]
                            if sub_score >= min_score:
                                return (
                                    sub_winner,
                                    sub_score,
                                    ["R_SELF_HEAL_DROP"],
                                    "drop_worst_asset",
                                    [drop_id],
                                    dict(sub_pen),
                                )
    return None
