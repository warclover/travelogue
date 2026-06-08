"""LSE-CAP-15 chapter highlight window detection + scorer boost (§4.5.13)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from travelogue.curation.asset_subject import asset_has_person
from travelogue.layout_engine.quality_features import QualityPool, build_quality_pool

_highlight_windows_var: ContextVar[tuple[frozenset[str], ...] | None] = ContextVar(
    "lse_highlight_windows",
    default=None,
)


def highlight_window_score(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    quality: QualityPool | None = None,
) -> float:
    if not asset_ids:
        return 0.0
    pool = quality or build_quality_pool(list(assets_map.values()))
    scores: list[float] = []
    for aid in asset_ids:
        q = pool.for_asset(str(aid))
        bonus = 0.12 if asset_has_person(assets_map.get(str(aid), {})) else 0.0
        scores.append(q.sharp_pct + q.aesthetic_pct + bonus)
    return sum(scores) / len(scores)


def detect_highlight_windows(
    asset_ids: list[str],
    assets_map: dict[str, dict],
    *,
    window_sizes: tuple[int, ...] = (5, 8, 12),
    max_windows: int = 2,
    quality: QualityPool | None = None,
) -> tuple[frozenset[str], ...]:
    """Top sliding windows by highlight_score (non-overlapping greedy)."""
    if len(asset_ids) < min(window_sizes, default=5):
        return ()
    pool = quality or build_quality_pool(list(assets_map.values()))
    candidates: list[tuple[float, int, int, frozenset[str]]] = []
    for size in window_sizes:
        if size > len(asset_ids):
            continue
        for i in range(0, len(asset_ids) - size + 1):
            window = asset_ids[i : i + size]
            score = highlight_window_score(window, assets_map, quality=pool)
            candidates.append((score, i, i + size, frozenset(window)))
    candidates.sort(key=lambda t: (-t[0], t[1]))
    picked: list[frozenset[str]] = []
    occupied: list[tuple[int, int]] = []
    for _score, start, end, key in candidates:
        if len(picked) >= max(0, max_windows):
            break
        if any(not (end <= s or start >= e) for s, e in occupied):
            continue
        picked.append(key)
        occupied.append((start, end))
    return tuple(picked)


def begin_chapter_highlight_windows(windows: tuple[frozenset[str], ...]) -> None:
    _highlight_windows_var.set(windows)


def clear_chapter_highlight_windows() -> None:
    _highlight_windows_var.set(None)


def current_highlight_boost(
    asset_ids: list[str],
    *,
    default_boost: float = 1.25,
) -> float:
    """Return boost multiplier when exact window matches a detected highlight."""
    windows = _highlight_windows_var.get()
    if not windows:
        return 1.0
    key = frozenset(str(a) for a in asset_ids if a)
    if key in windows:
        return max(1.0, float(default_boost))
    return 1.0


def highlight_windows_from_pack(pack_raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = (pack_raw or {}).get("highlight_windows") if isinstance(pack_raw, dict) else {}
    if not isinstance(raw, dict):
        return {"enabled": False, "boost": 1.25, "window_sizes": (5, 8, 12), "max_windows": 2}
    sizes_raw = raw.get("window_sizes") or [5, 8, 12]
    sizes = tuple(int(x) for x in sizes_raw)
    return {
        "enabled": bool(raw.get("enabled", False)),
        "boost": float(raw.get("boost", 1.25)),
        "window_sizes": sizes,
        "max_windows": int(raw.get("max_windows_per_chapter", raw.get("max_windows", 2))),
    }
