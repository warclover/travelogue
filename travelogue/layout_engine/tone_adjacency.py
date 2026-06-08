"""Adjacent-screen tone penalty · LSE-CAP-04 look-back-1 (§4.5.4)."""

from __future__ import annotations

from travelogue.curation.layout_scoring import screen_dominant_tone
from travelogue.media.color_metrics import delta_e_cie76


def _screen_mean_luma(screen: dict, assets_by_id: dict[str, dict]) -> float | None:
    values: list[float] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        asset = assets_by_id.get(str(aid)) or {}
        try:
            values.append(float(asset.get("meanLuma")))
        except (TypeError, ValueError):
            pass
    if not values:
        return None
    return sum(values) / len(values)


def _hard_cut_exempt(
    prev_screen: dict,
    candidate: dict,
    assets_by_id: dict[str, dict],
    *,
    gap_seconds: float = 3600.0,
    luma_delta: float = 0.35,
) -> bool:
    """Day/night or indoor/outdoor hard-cut exemption (AC-P17-18)."""
    prev_luma = _screen_mean_luma(prev_screen, assets_by_id)
    cand_luma = _screen_mean_luma(candidate, assets_by_id)
    luma_jump = (
        prev_luma is not None
        and cand_luma is not None
        and abs(prev_luma - cand_luma) >= luma_delta
    )
    prev_ts = None
    cand_ts = None
    for screen, holder in ((prev_screen, "prev"), (candidate, "cand")):
        del holder
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if not aid:
                continue
            asset = assets_by_id.get(str(aid)) or {}
            ts = asset.get("takenAt")
            if ts:
                if screen is prev_screen:
                    prev_ts = ts
                else:
                    cand_ts = ts
                break
    time_jump = False
    if prev_ts and cand_ts:
        try:
            from datetime import datetime

            p = datetime.fromisoformat(str(prev_ts).replace("Z", "+00:00"))
            c = datetime.fromisoformat(str(cand_ts).replace("Z", "+00:00"))
            time_jump = abs((c - p).total_seconds()) >= gap_seconds
        except (TypeError, ValueError):
            time_jump = False
    return bool(luma_jump and time_jump)


def adjacent_tone_penalty(
    prev_screen: dict | None,
    candidate: dict,
    assets_by_id: dict[str, dict],
) -> float:
    """Return penalty 0..1 for look-back-1 ΔE / luminance jump."""
    if not prev_screen:
        return 0.0
    if _hard_cut_exempt(prev_screen, candidate, assets_by_id):
        return 0.0
    ta = screen_dominant_tone(prev_screen, assets_by_id)
    tb = screen_dominant_tone(candidate, assets_by_id)
    if ta and tb:
        de = delta_e_cie76(ta, tb)
        if de >= 40.0:
            return 0.85
        if de >= 25.0:
            return 0.45
        if de >= 15.0:
            return 0.20
    prev_luma = _screen_mean_luma(prev_screen, assets_by_id)
    cand_luma = _screen_mean_luma(candidate, assets_by_id)
    if prev_luma is not None and cand_luma is not None:
        delta = abs(prev_luma - cand_luma)
        if delta >= 0.35:
            return 0.70
        if delta >= 0.20:
            return 0.35
    return 0.0
