"""
Web screens layout engine (layoutEngine=screens).

See docs/web端模板.prd and docs/web端模板升级计划.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from travelogue.curation.layout_planner import (
    _effective_profile,
    _is_std_landscape,
    _is_std_portrait,
)
from travelogue.media.image_ops import AspectKind

LayoutEngine = Literal["legacy", "screens"]
LayoutFit = Literal["cover", "contain"]
SlotRole = Literal["portrait", "landscape"]

LAYOUT_ENGINE_LEGACY: LayoutEngine = "legacy"
LAYOUT_ENGINE_SCREENS: LayoutEngine = "screens"
LAYOUT_ENGINE_VERSION_SCREENS = "screens-2"
MAX_SLOTS_PER_SCREEN = 9

PATTERN_PORTRAIT_1_LANDSCAPE_2 = "screen-portrait-1-landscape-2"

_GRID_SIZES = (9, 6, 4, 3, 2, 1)

PATTERN_GRID_CLASS: dict[str, str] = {
    "screen-portrait-1": "layout-screen__grid--1col",
    "screen-portrait-2": "layout-screen__grid--2col",
    "screen-portrait-3": "layout-screen__grid--3col",
    "screen-portrait-4": "layout-screen__grid--2x2",
    "screen-portrait-6": "layout-screen__grid--3x2",
    "screen-portrait-9": "layout-screen__grid--3x3",
    PATTERN_PORTRAIT_1_LANDSCAPE_2: "layout-screen__grid--portrait-left-2landscape",
    "screen-landscape-1": "layout-screen__grid--1col",
    "screen-landscape-2": "layout-screen__grid--landscape-stack-2",
    "screen-landscape-3": "layout-screen__grid--landscape-stack-3",
    "screen-landscape-4": "layout-screen__grid--2x2",
    "screen-landscape-6": "layout-screen__grid--3x2",
    "screen-landscape-9": "layout-screen__grid--3x3",
    "screen-square-1": "layout-screen__grid--1col",
    "screen-square-2": "layout-screen__grid--2col",
    "screen-square-3": "layout-screen__grid--3col",
    "screen-square-4": "layout-screen__grid--2x2",
    "screen-square-6": "layout-screen__grid--3x2",
    "screen-square-9": "layout-screen__grid--3x3",
    "screen-panorama-1": "layout-screen__grid--1col",
    "screen-tall-1": "layout-screen__grid--1col",
}

# Multi-column grids in 16:9 create portrait-shaped slots — only for portrait family.
_LANDSCAPE_GRID_SIZES = (9, 6, 4)
_PORTRAIT_COLUMN_GRID_SIZES = (9, 6, 3, 2, 1)


def grid_class_for_pattern(pattern_id: str) -> str:
    return PATTERN_GRID_CLASS.get(pattern_id, "layout-screen__grid--1col")


def resolve_layout_engine(trip: dict, *, override: str | None = None) -> LayoutEngine:
    raw = override or trip.get("layoutEngine") or LAYOUT_ENGINE_LEGACY
    if raw not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        return LAYOUT_ENGINE_LEGACY
    return raw  # type: ignore[return-value]


def screens_layout_active(trip: dict, *, override: str | None = None) -> bool:
    if resolve_layout_engine(trip, override=override) != LAYOUT_ENGINE_SCREENS:
        return False
    export_layout = trip.get("exportLayout", "auto")
    if export_layout == "auto":
        return True
    return _effective_profile(export_layout) == "web"  # type: ignore[arg-type]


def _default_fits(pattern_id: str, n: int) -> list[LayoutFit]:
    if pattern_id in ("screen-tall-1", "screen-panorama-1", "screen-square-1"):
        return ["contain"] * n
    if pattern_id == "screen-portrait-1":
        return ["cover"] * n
    if pattern_id == PATTERN_PORTRAIT_1_LANDSCAPE_2:
        return ["cover"] * n
    return ["cover"] * n


def _pattern_family(pattern_id: str) -> str:
    if pattern_id.startswith("screen-portrait"):
        return "portrait"
    if pattern_id.startswith("screen-landscape"):
        return "landscape"
    if pattern_id.startswith("screen-square"):
        return "square"
    if pattern_id.startswith("screen-panorama"):
        return "panorama"
    if pattern_id.startswith("screen-tall"):
        return "tall"
    return "landscape"


def _slot_allowed_in_pattern(aid: str, pattern_id: str, aspects: dict[str, AspectKind]) -> bool:
    kind = aspects.get(aid, "square")
    fam = _pattern_family(pattern_id)
    if fam == "portrait":
        return kind in ("portrait", "tall")
    if fam == "landscape":
        return kind in ("landscape", "panorama", "square")
    if fam == "panorama":
        return kind == "panorama"
    if fam == "tall":
        return kind == "tall"
    if fam == "square":
        return kind == "square"
    return True


def _filter_ids_for_pattern(
    asset_ids: list[str],
    pattern_id: str,
    aspects: dict[str, AspectKind],
) -> list[str]:
    return [aid for aid in asset_ids if _slot_allowed_in_pattern(aid, pattern_id, aspects)]


def _make_screen(
    pattern_id: str,
    asset_ids: list[str] | None = None,
    *,
    screen_id: str,
    slots: list[dict] | None = None,
    fits: list[LayoutFit] | None = None,
    tone: dict | None = None,
    aspects: dict[str, AspectKind] | None = None,
) -> dict:
    if slots is None:
        ids = list(asset_ids or [])
        if aspects is not None:
            ids = _filter_ids_for_pattern(ids, pattern_id, aspects)
        fit_list = fits or _default_fits(pattern_id, len(ids))
        slots = []
        for idx, aid in enumerate(ids):
            fit: LayoutFit = fit_list[idx] if idx < len(fit_list) else fit_list[-1]
            slots.append({"assetId": aid, "slot": idx, "fit": fit})
    return {
        "screenId": screen_id,
        "patternId": pattern_id,
        "tone": tone,
        "slots": slots,
    }


def _make_mixed_portrait_landscape_screen(
    portrait_id: str,
    landscape_ids: list[str],
    *,
    screen_id: str = "",
) -> dict:
    return _make_screen(
        PATTERN_PORTRAIT_1_LANDSCAPE_2,
        screen_id=screen_id,
        slots=[
            {"assetId": portrait_id, "slot": 0, "fit": "cover", "role": "portrait"},
            {"assetId": landscape_ids[0], "slot": 1, "fit": "cover", "role": "landscape"},
            {"assetId": landscape_ids[1], "slot": 2, "fit": "cover", "role": "landscape"},
        ],
    )


def _family_kind(k: AspectKind) -> str:
    if k == "panorama":
        return "panorama"
    if k == "tall":
        return "tall"
    if k == "square":
        return "square"
    if _is_std_portrait(k):
        return "portrait"
    if _is_std_landscape(k):
        return "landscape"
    return "landscape"


def _is_std_portrait_id(aid: str, aspects: dict[str, AspectKind]) -> bool:
    return _family_kind(aspects.get(aid, "square")) == "portrait"


def _is_landscape_id(aid: str, aspects: dict[str, AspectKind]) -> bool:
    return _family_kind(aspects.get(aid, "square")) == "landscape"


def _pattern_id(family: str, count: int) -> str:
    if family == "panorama":
        return "screen-panorama-1"
    if family == "tall":
        return "screen-portrait-1"
    if count in (1, 2, 3, 4, 6, 9):
        return f"screen-{family}-{count}"
    if count >= 7:
        return f"screen-{family}-9"
    return f"screen-{family}-1"


def _parse_taken_ts(asset: dict) -> float | None:
    raw = asset.get("takenAt")
    if not raw:
        return None
    try:
        text = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(text).timestamp()
    except (TypeError, ValueError):
        return None


def _time_near_chain(
    asset_ids: list[str],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    """True when all known takenAt timestamps span ≤ burst_seconds (or EXIF missing)."""
    stamps = [_parse_taken_ts(assets.get(aid, {})) for aid in asset_ids]
    valid = [t for t in stamps if t is not None]
    if len(valid) < 2:
        return True
    return max(valid) - min(valid) <= burst_seconds


def burst_group_map(
    asset_ids: list[str],
    assets: dict[str, dict],
    aspects: dict[str, AspectKind],
    *,
    burst_seconds: float = 3.0,
) -> dict[str, int]:
    """Assign burst group ids from takenAt proximity + same aspect family."""
    groups: dict[str, int] = {}
    gid = 0
    last_ts: float | None = None
    last_family: str | None = None
    for aid in asset_ids:
        fam = _family_kind(aspects.get(aid, "square"))
        ts = _parse_taken_ts(assets.get(aid, {}))
        if (
            last_ts is not None
            and ts is not None
            and last_family == fam
            and abs(ts - last_ts) <= burst_seconds
        ):
            groups[aid] = gid
        else:
            gid += 1
            groups[aid] = gid
        if ts is not None:
            last_ts = ts
        last_family = fam
    return groups


def _same_burst_group(
    asset_ids: list[str],
    burst_groups: dict[str, int],
) -> bool:
    if len(asset_ids) < 2:
        return False
    g0 = burst_groups.get(asset_ids[0])
    return g0 is not None and all(burst_groups.get(a) == g0 for a in asset_ids)


def _pick_grid_count(
    run_len: int,
    family: str,
    *,
    burst_run: bool = False,
    portrait_heavy: bool = False,
) -> int:
    """Pick largest grid ≤ run_len (landscape: 4/6/9 only; portrait: column grids)."""
    cap = min(run_len, MAX_SLOTS_PER_SCREEN)
    if family == "landscape":
        sizes = _LANDSCAPE_GRID_SIZES
        preferred: list[int] = []
        if burst_run and cap >= 4:
            preferred.extend([9, 4])
        else:
            preferred.extend([9, 6, 4])
        for size in preferred:
            if size <= cap:
                return size
        for size in sizes:
            if size <= cap:
                return size
        return 1

    preferred = []
    if burst_run and cap >= 4:
        preferred.extend([9, 4])
    if portrait_heavy and family == "portrait":
        preferred.extend([9, 6, 3])
    sizes = _PORTRAIT_COLUMN_GRID_SIZES if family == "portrait" else _GRID_SIZES
    for size in preferred:
        if size in sizes and size <= cap:
            return size
    for size in sizes:
        if size <= cap:
            return size
    return 1


def _run_length(remaining: list[str], aspects: dict[str, AspectKind]) -> tuple[str, int]:
    if not remaining:
        return "landscape", 0
    fam = _family_kind(aspects.get(remaining[0], "square"))
    n = 1
    while n < len(remaining) and _family_kind(aspects.get(remaining[n], "square")) == fam:
        n += 1
    return fam, n


def _can_mixed_p1_l2(
    portrait_id: str,
    landscape_ids: list[str],
    aspects: dict[str, AspectKind],
    assets: dict[str, dict],
    *,
    burst_seconds: float,
) -> bool:
    if len(landscape_ids) != 2:
        return False
    if not _is_std_portrait_id(portrait_id, aspects):
        return False
    if not all(_is_landscape_id(lid, aspects) for lid in landscape_ids):
        return False
    return _time_near_chain(
        [portrait_id, landscape_ids[0], landscape_ids[1]],
        assets,
        burst_seconds=burst_seconds,
    )


def _flush_portrait_pending(
    pending: list[str],
    aspects: dict[str, AspectKind],
) -> list[dict]:
    """Emit portrait-3 / portrait-2 / cover portrait-1 for buffered std portraits only."""
    screens: list[dict] = []
    buf = [a for a in pending if _is_std_portrait_id(a, aspects)]
    overflow = [a for a in pending if a not in buf]
    pending.clear()
    pending.extend(overflow)
    while len(buf) >= 3:
        screens.append(
            _make_screen("screen-portrait-3", buf[:3], screen_id="", aspects=aspects)
        )
        buf = buf[3:]
    if len(buf) == 2:
        screens.append(_make_screen("screen-portrait-2", buf, screen_id="", aspects=aspects))
    elif len(buf) == 1:
        # 单张竖图：cover 满屏，避免 contain 信箱（PRD）
        screens.append(
            _make_screen(
                "screen-portrait-1",
                buf,
                screen_id="",
                aspects=aspects,
                fits=["cover"],
            )
        )
    return screens


def _plan_one_screen(
    remaining: list[str],
    aspects: dict[str, AspectKind],
    *,
    burst_groups: dict[str, int] | None = None,
    portrait_heavy: bool = False,
) -> tuple[dict | None, int]:
    if not remaining:
        return None, 0

    family, run_len = _run_length(remaining, aspects)

    if family == "panorama":
        return _make_screen("screen-panorama-1", [remaining[0]], screen_id=""), 1

    if family == "tall":
        return _make_screen("screen-tall-1", [remaining[0]], screen_id=""), 1

    if family == "portrait":
        return None, 0

    if family == "landscape" and run_len in (2, 3):
        n = run_len
        pattern = _pattern_id("landscape", n)
        return (
            _make_screen(pattern, remaining[:n], screen_id="", aspects=aspects),
            n,
        )

    burst_groups = burst_groups or {}
    probe = remaining[: min(run_len, MAX_SLOTS_PER_SCREEN)]
    burst_run = _same_burst_group(probe, burst_groups) if len(probe) >= 4 else False

    n = _pick_grid_count(
        run_len,
        family,
        burst_run=burst_run,
        portrait_heavy=portrait_heavy,
    )
    ids = remaining[:n]
    pattern = _pattern_id(family, n)
    return _make_screen(pattern, ids, screen_id="", aspects=aspects), n


CHAPTER_HERO_MIN_ASSETS = 5


def _pick_chapter_hero(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> tuple[str, str] | None:
    """Best landscape/panorama for opening 16:9 hero screen (web editorial rhythm)."""
    from travelogue.curation.curate import _cover_score

    best_id = ""
    best_score = 0.0
    best_kind: AspectKind = "landscape"
    for aid in asset_ids:
        kind = aspects.get(aid, "square")
        if kind not in ("landscape", "panorama"):
            continue
        asset = assets_map.get(aid) or {}
        score = _cover_score(asset, "web")
        if score > best_score:
            best_score = score
            best_id = aid
            best_kind = kind
    if not best_id:
        return None
    pat = "screen-panorama-1" if best_kind == "panorama" else "screen-landscape-1"
    return best_id, pat


def _sort_asset_ids_by_taken(
    asset_ids: list[str],
    assets: dict[str, dict],
) -> list[str]:
    def key(aid: str) -> str:
        return str(assets.get(aid, {}).get("takenAt") or "")

    return sorted(asset_ids, key=key)


def _collect_asset_ids_from_chapter(ch: dict) -> list[str]:
    ids: list[str] = []
    for it in ch.get("items", []):
        itype = it.get("type")
        if itype == "media-card":
            ids.append(it["assetId"])
        elif itype in ("media-row", "media-scroll"):
            ids.extend(it.get("assetIds") or [])
    return ids


def plan_screens_for_chapter(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    chapter_id: str = "ch",
    max_per_screen: int = MAX_SLOTS_PER_SCREEN,
    assets: dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
) -> list[dict]:
    """
    Map ordered asset ids → screens[] (one pattern per screen; reset after each screen).

    Std portrait: prefer portrait-3 / portrait-2, then screen-portrait-1-landscape-2
    (竖左 + 双横右, takenAt ≤ burst_seconds), else cover portrait-1 fallback.
    """
    summary = orientation_summary or {}
    portrait_heavy = summary.get("portrait", 0) > summary.get("landscape", 0)
    mix_gap = mixed_proximity_seconds if mixed_proximity_seconds is not None else burst_seconds

    assets_map: dict[str, dict] = assets or {}
    ids = _sort_asset_ids_by_taken(list(asset_ids), assets_map)
    hero_preface: list[dict] = []
    if len(ids) >= CHAPTER_HERO_MIN_ASSETS and assets_map:
        hero = _pick_chapter_hero(ids, aspects, assets_map)
        if hero:
            hid, pat = hero
            hero_preface.append(_make_screen(pat, [hid], screen_id=""))
            ids = [aid for aid in ids if aid != hid]
    burst_groups: dict[str, int] = {}
    if assets_map:
        burst_groups = burst_group_map(ids, assets_map, aspects, burst_seconds=burst_seconds)

    screens: list[dict] = []
    pending_portraits: list[str] = []
    i = 0
    seq = 0

    def _assign_id(screen: dict) -> None:
        nonlocal seq
        seq += 1
        screen["screenId"] = f"{chapter_id}-sc-{seq:02d}"

    def _append(screen: dict) -> None:
        _assign_id(screen)
        screens.append(screen)

    def _try_mixed_at(portrait_id: str, l1: str, l2: str) -> bool:
        if not _can_mixed_p1_l2(
            portrait_id, [l1, l2], aspects, assets_map, burst_seconds=mix_gap
        ):
            return False
        _append(_make_mixed_portrait_landscape_screen(portrait_id, [l1, l2]))
        return True

    while i < len(ids):
        if len(pending_portraits) == 1 and i + 1 < len(ids):
            p_id = pending_portraits[0]
            l1, l2 = ids[i], ids[i + 1]
            if _try_mixed_at(p_id, l1, l2):
                pending_portraits.clear()
                i += 2
                continue

        if i + 2 < len(ids):
            a, b, c = ids[i], ids[i + 1], ids[i + 2]
            if _is_std_portrait_id(a, aspects) and _is_landscape_id(b, aspects) and _is_landscape_id(
                c, aspects
            ):
                if _try_mixed_at(a, b, c):
                    i += 3
                    continue
            if _is_landscape_id(a, aspects) and _is_landscape_id(b, aspects) and _is_std_portrait_id(
                c, aspects
            ):
                if _try_mixed_at(c, a, b):
                    i += 3
                    continue

        fam = _family_kind(aspects.get(ids[i], "square"))

        if fam == "portrait":
            run_len = 1
            while (
                i + run_len < len(ids)
                and _family_kind(aspects.get(ids[i + run_len], "square")) == "portrait"
            ):
                run_len += 1
            for aid in ids[i : i + run_len]:
                pending_portraits.append(aid)
            i += run_len
            while len(pending_portraits) >= 3:
                batch = [a for a in pending_portraits[:3] if _is_std_portrait_id(a, aspects)]
                if len(batch) >= 3:
                    _append(
                        _make_screen(
                            "screen-portrait-3", batch[:3], screen_id="", aspects=aspects
                        )
                    )
                    del pending_portraits[:3]
                else:
                    break
            if len(pending_portraits) == 1 and i + 1 < len(ids):
                p_id = pending_portraits[0]
                l1, l2 = ids[i], ids[i + 1]
                if _try_mixed_at(p_id, l1, l2):
                    pending_portraits.clear()
                    i += 2
                    continue
            if len(pending_portraits) == 2:
                pair = [a for a in pending_portraits if _is_std_portrait_id(a, aspects)]
                if len(pair) == 2:
                    _append(
                        _make_screen("screen-portrait-2", pair, screen_id="", aspects=aspects)
                    )
                pending_portraits.clear()
            continue

        if pending_portraits:
            if len(pending_portraits) == 1 and fam == "landscape" and i + 1 < len(ids):
                if _try_mixed_at(pending_portraits[0], ids[i], ids[i + 1]):
                    pending_portraits.clear()
                    i += 2
                    continue
            for sc in _flush_portrait_pending(pending_portraits, aspects):
                _append(sc)

        if fam == "tall":
            _append(_make_screen("screen-tall-1", [ids[i]], screen_id="", aspects=aspects))
            i += 1
            continue

        chunk = ids[i : i + max_per_screen]
        screen, consumed = _plan_one_screen(
            chunk,
            aspects,
            burst_groups=burst_groups,
            portrait_heavy=portrait_heavy,
        )
        if not screen or consumed < 1:
            i += 1
            continue
        _append(screen)
        i += consumed

    if pending_portraits:
        for sc in _flush_portrait_pending(pending_portraits, aspects):
            _append(sc)

    if hero_preface:
        reordered: list[dict] = []
        seq = 0
        for sc in hero_preface + screens:
            seq += 1
            sc = dict(sc)
            sc["screenId"] = f"{chapter_id}-sc-{seq:02d}"
            reordered.append(sc)
        return reordered

    return screens


def attach_screens_day_buckets(
    chapters: list[dict],
    day_buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    *,
    assets: list[dict] | dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
) -> list[dict]:
    """
    Plan screens on each day bucket (full takenAt sequence), assign to chapters
    by the chapter that owns each screen's first asset.
    """
    assets_by_id: dict[str, dict] = {}
    if isinstance(assets, dict):
        assets_by_id = assets
    elif isinstance(assets, list):
        assets_by_id = {a["id"]: a for a in assets if a.get("id")}

    asset_to_ch: dict[str, str] = {}
    out: list[dict] = []
    for ch in chapters:
        ch = dict(ch)
        for aid in _collect_asset_ids_from_chapter(ch):
            asset_to_ch[aid] = ch.get("id", "ch")
        ch["screens"] = []
        out.append(ch)

    ch_by_id = {ch["id"]: ch for ch in out}
    seq_per_ch: dict[str, int] = {}
    gallery_asset_ids: set[str] = set()
    for ch in out:
        if ch.get("patternId") == "gallery":
            gallery_asset_ids.update(_collect_asset_ids_from_chapter(ch))

    for ch in out:
        if ch.get("patternId") != "gallery":
            continue
        aids = _collect_asset_ids_from_chapter(ch)
        if not aids:
            continue
        sorted_aids = _sort_asset_ids_by_taken(aids, assets_by_id)
        gal_screens = plan_screens_for_chapter(
            sorted_aids,
            aspects,
            chapter_id=ch["id"],
            assets=assets_by_id or None,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
        )
        ch["screens"] = gal_screens

    for bucket in day_buckets:
        filtered = [a for a in bucket if a not in gallery_asset_ids]
        if not filtered:
            continue
        bucket = filtered
        if not bucket:
            continue
        bucket_screens = plan_screens_for_chapter(
            bucket,
            aspects,
            chapter_id="day",
            assets=assets_by_id or None,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
        )
        for sc in bucket_screens:
            slots = sc.get("slots") or []
            if not slots:
                continue
            ch_id = asset_to_ch.get(slots[0]["assetId"])
            if not ch_id or ch_id not in ch_by_id:
                continue
            seq_per_ch[ch_id] = seq_per_ch.get(ch_id, 0) + 1
            screen = dict(sc)
            screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[ch_id]:02d}"
            ch_by_id[ch_id]["screens"].append(screen)

    return out


def attach_screens_to_chapters(
    chapters: list[dict],
    aspects: dict[str, AspectKind],
    *,
    assets: list[dict] | dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
    plan_scope: str | None = None,
    day_buckets: list[list[str]] | None = None,
) -> list[dict]:
    """Add screens[] to each chapter (per-chapter or per-day bucket scope)."""
    from travelogue.config import default_screen_plan_scope

    scope = (plan_scope or default_screen_plan_scope()).strip().lower()
    if scope == "day" and day_buckets:
        return attach_screens_day_buckets(
            chapters,
            day_buckets,
            aspects,
            assets=assets,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
        )

    assets_by_id: dict[str, dict] = {}
    if isinstance(assets, dict):
        assets_by_id = assets
    elif isinstance(assets, list):
        assets_by_id = {a["id"]: a for a in assets if a.get("id")}

    out: list[dict] = []
    for ch in chapters:
        ch = dict(ch)
        asset_ids = _collect_asset_ids_from_chapter(ch)

        if asset_ids:
            ch["screens"] = plan_screens_for_chapter(
                asset_ids,
                aspects,
                chapter_id=ch.get("id", "ch"),
                assets=assets_by_id or None,
                burst_seconds=burst_seconds,
                mixed_proximity_seconds=mixed_proximity_seconds,
                orientation_summary=orientation_summary,
            )
        else:
            ch["screens"] = []
        out.append(ch)
    return out


def gallery_chapter_uses_screens_not_scroll(chapter: dict, *, layout_engine: str) -> bool:
    """Gallery chapters: screens engine uses mosaic screens, not media-scroll in render."""
    return layout_engine == LAYOUT_ENGINE_SCREENS and chapter.get("patternId") == "gallery"
