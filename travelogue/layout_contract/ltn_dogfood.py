"""LTN dogfood AC helpers · AC-B-02 / AC-D-02 proxy / AC-D-03 / AC-D-01 checklist."""

from __future__ import annotations

from typing import Any

from travelogue.layout_contract.chapter_items import (
    resolve_longshot_mode,
    screens_to_longshot_items,
)
from travelogue.layout_contract.narrative_contract import ensure_narrative_contract
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

# Mid-chapter band for AC-D-03 (broader than peak 0.55–0.70; 「中章」).
_MID_CHAPTER_LO = 0.35
_MID_CHAPTER_HI = 0.80


def _iter_content_screens(chapters: list[dict[str, Any]]):
    for ch in chapters or []:
        if not isinstance(ch, dict):
            continue
        screens = [s for s in (ch.get("screens") or []) if isinstance(s, dict)]
        content = [
            s
            for s in screens
            if "breath" not in str(s.get("patternId") or "")
        ]
        for idx, sc in enumerate(content):
            n = len(content)
            progress = idx / max(1, n - 1) if n > 1 else 0.0
            yield ch, sc, idx, n, progress


def is_hero_mosaic_screen(screen: dict[str, Any]) -> bool:
    pid = str(screen.get("patternId") or "")
    if "mosaic" not in pid:
        return False
    if ScreenLayoutPlannerState.pattern_has_main_role(pid):
        return True
    return any(
        isinstance(sl, dict) and sl.get("role") in ("main", "hero")
        for sl in (screen.get("slots") or [])
    )


def check_ac_b02_longshot_group(
    chapters: list[dict[str, Any]],
) -> dict[str, Any]:
    """AC-B-02 · hero mosaic → longshot still readable as a group."""
    hero_screens: list[dict[str, Any]] = []
    for _ch, sc, *_rest in _iter_content_screens(chapters):
        if is_hero_mosaic_screen(sc):
            hero_screens.append(sc)

    checked = 0
    ok_n = 0
    failures: list[str] = []
    details: list[dict[str, Any]] = []
    for sc in hero_screens:
        ensure_narrative_contract(sc)
        mode = resolve_longshot_mode(sc)
        items = screens_to_longshot_items({"screens": [sc]})
        slot_aids = [
            str(sl.get("assetId"))
            for sl in (sc.get("slots") or [])
            if isinstance(sl, dict) and sl.get("assetId")
        ]
        checked += 1
        row: dict[str, Any] = {
            "screenId": sc.get("screenId"),
            "patternId": sc.get("patternId"),
            "mode": mode,
            "itemCount": len(items),
        }
        ok = False
        if mode == "flatten":
            failures.append(f"{sc.get('screenId')}: unexpected flatten on hero mosaic")
        elif mode == "preserve_stack":
            if (
                len(items) == 1
                and items[0].get("type") == "media-row"
                and items[0].get("rowLayout") == "preserve-stack"
                and list(items[0].get("assetIds") or []) == slot_aids
                and ("一组" in str(items[0].get("groupMark") or ""))
            ):
                ok = True
            else:
                failures.append(f"{sc.get('screenId')}: preserve_stack item malformed")
        elif mode == "representative_badge":
            if (
                len(items) == 1
                and items[0].get("type") == "media-card"
                and items[0].get("groupBadge")
            ):
                ok = True
            else:
                failures.append(f"{sc.get('screenId')}: representative badge missing")
        row["ok"] = ok
        details.append(row)
        if ok:
            ok_n += 1

    return {
        "ac": "AC-B-02",
        "ok": checked > 0 and ok_n == checked and not failures,
        "heroMosaicCount": checked,
        "passed": ok_n,
        "failures": failures,
        "details": details,
        "notes": (
            []
            if checked
            else ["no hero mosaic screens — sample ineligible for AC-B-02"]
        ),
    }


def check_ac_d03_hero_mid_chapter(
    chapters: list[dict[str, Any]],
    *,
    min_ratio: float = 0.60,
) -> dict[str, Any]:
    """AC-D-03 · share of hero mosaics whose progress falls in mid-chapter band."""
    positions: list[float] = []
    for _ch, sc, _idx, _n, progress in _iter_content_screens(chapters):
        if is_hero_mosaic_screen(sc):
            positions.append(progress)
    if not positions:
        return {
            "ac": "AC-D-03",
            "ok": None,
            "skipped": True,
            "ratio": None,
            "heroMosaicCount": 0,
            "notes": ["no hero mosaic — AC-D-03 N/A"],
        }
    mid = sum(1 for p in positions if _MID_CHAPTER_LO <= p <= _MID_CHAPTER_HI)
    ratio = round(mid / len(positions), 6)
    return {
        "ac": "AC-D-03",
        "ok": ratio >= min_ratio,
        "skipped": False,
        "ratio": ratio,
        "minRatio": min_ratio,
        "midBand": [_MID_CHAPTER_LO, _MID_CHAPTER_HI],
        "heroMosaicCount": len(positions),
        "midCount": mid,
        "positions": positions,
    }


def check_ac_d02_semantic_pause(
    chapters: list[dict[str, Any]],
) -> dict[str, Any]:
    """AC-D-02 proxy · L2 not painted on every screen; prefer scene/chapter cues."""
    gaps: list[str] = []
    l2_with_cue = 0
    l2_total = 0
    for ch, sc, idx, n, _p in _iter_content_screens(chapters):
        gap = str(sc.get("rhythmGap") or "").upper()
        if gap:
            gaps.append(gap)
        if gap != "L2":
            continue
        l2_total += 1
        content = [
            s
            for s in (ch.get("screens") or [])
            if isinstance(s, dict) and "breath" not in str(s.get("patternId") or "")
        ]
        prev_scene = content[idx - 1].get("sceneId") if idx > 0 and idx <= len(content) else None
        if (
            sc.get("sceneId")
            or (prev_scene and prev_scene != sc.get("sceneId"))
            or idx == 0
            or idx == n - 1
        ):
            l2_with_cue += 1
    if not gaps:
        return {
            "ac": "AC-D-02",
            "ok": None,
            "skipped": True,
            "notes": ["no rhythmGap fields — run after D1 assign"],
        }
    uniform = len(set(gaps)) == 1 and gaps[0] == "L1"
    all_l2 = len(set(gaps)) == 1 and gaps[0] == "L2"
    l2_ratio = round(l2_total / len(gaps), 6)
    ok = (not uniform) and (not all_l2) and (
        l2_total == 0 or l2_with_cue >= max(1, l2_total // 2)
    )
    return {
        "ac": "AC-D-02",
        "ok": ok,
        "skipped": False,
        "gapCounts": {g: gaps.count(g) for g in sorted(set(gaps))},
        "l2Total": l2_total,
        "l2WithCue": l2_with_cue,
        "l2Ratio": l2_ratio,
        "uniformL1": uniform,
    }


def rhythm_proxy_score(chapters: list[dict[str, Any]]) -> dict[str, Any]:
    """AC-D-01 engineering proxy (0–10). Human blind ≥7 remains authoritative."""
    d02 = check_ac_d02_semantic_pause(chapters)
    d03 = check_ac_d03_hero_mid_chapter(chapters)
    score = 5.5  # PRD baseline
    notes: list[str] = ["proxy only — AC-D-01 requires human blind ≥7"]
    if d02.get("ok") is True:
        score += 1.0
    elif d02.get("ok") is False:
        score -= 0.5
        notes.append("D02 proxy failed")
    if d03.get("ok") is True:
        score += 1.0
    elif d03.get("ok") is False:
        score -= 0.5
        notes.append("D03 failed")
    # Role diversity bonus
    roles = set()
    for _ch, sc, *_r in _iter_content_screens(chapters):
        ensure_narrative_contract(sc)
        roles.add(str(sc.get("narrativeRole") or ""))
    if len(roles) >= 3:
        score += 0.5
    score = round(min(10.0, max(0.0, score)), 2)
    return {
        "ac": "AC-D-01",
        "ok": None,
        "humanRequired": True,
        "proxyScore": score,
        "proxyPassHint": score >= 7.0,
        "notes": notes,
        "roleDiversity": len(roles),
    }


def evaluate_dogfood_trip(trip: dict[str, Any]) -> dict[str, Any]:
    chapters = list(trip.get("chapters") or [])
    b02 = check_ac_b02_longshot_group(chapters)
    d02 = check_ac_d02_semantic_pause(chapters)
    d03 = check_ac_d03_hero_mid_chapter(chapters)
    d01 = rhythm_proxy_score(chapters)
    # Machine gate: B-02 must pass when sample eligible; D-03 when not skipped.
    machine_ok = True
    if b02.get("heroMosaicCount", 0) > 0:
        machine_ok = machine_ok and bool(b02.get("ok"))
    if d03.get("skipped") is not True and d03.get("ok") is not None:
        machine_ok = machine_ok and bool(d03.get("ok"))
    if d02.get("skipped") is not True and d02.get("ok") is not None:
        machine_ok = machine_ok and bool(d02.get("ok"))
    return {
        "tripId": trip.get("tripId"),
        "machineOk": machine_ok,
        "AC-B-02": b02,
        "AC-D-01": d01,
        "AC-D-02": d02,
        "AC-D-03": d03,
    }
