"""Cover opening helpers: place/title de-dupe, system hook filter, cover media fit."""

from __future__ import annotations

import re

# Stub hooks from travelogue.services.narrate._build_hook (frame / pre-LLM).
# Keep legacy「碎片」patterns for old trips; also catch W1/W2「照片汇成」类模板句.
_SYSTEM_HOOK_PATTERNS = (
    re.compile(r"^\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^\d+\s*张照片汇成这一页[。．]?$"),
    re.compile(r"^.+，\d+\s*帧记录[。．]?$"),
    re.compile(r"^.+，\d+\s*张照片[。．]?$"),
    re.compile(r"^.+，\d+\s*帧留在这里[。．]?$"),
    re.compile(r"^.+，\d+\s*张照片留在这里[。．]?$"),
    re.compile(r"^.+[·•].+，慢慢翻[。．]?$"),
    re.compile(r"^在.+的(\d+天|[\d\.]+\s*[–-]\s*[\d\.]+)，\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^在.+的(\d+天|[\d\.]+\s*[–-]\s*[\d\.]+)，\d+\s*张照片汇成这一页[。．]?$"),
    re.compile(r"^.+·.+，\d+\s*张碎片拼成这一页[。．]?$"),
    re.compile(r"^.+·.+，\d+\s*张照片汇成这一页[。．]?$"),
)

_PORTRAIT_CONTAIN_AR = 1.2


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip().casefold())


def cover_place_is_distinct(place: str, title: str) -> bool:
    """False when place duplicates the magazine title (common with narrative_copy_subject)."""
    if not (place or "").strip() or not (title or "").strip():
        return bool((place or "").strip())
    return _normalize_label(place) != _normalize_label(title)


def is_system_cover_hook(hook: str) -> bool:
    text = (hook or "").strip()
    if not text:
        return False
    return any(p.match(text) for p in _SYSTEM_HOOK_PATTERNS)


def show_hook_on_cover(hook: str) -> bool:
    text = (hook or "").strip()
    if not text:
        return False
    if is_system_cover_hook(text):
        return False
    return len(text) <= 56


def cover_asset_aspect(asset: dict) -> float | None:
    try:
        w = float(asset.get("width") or 0)
        h = float(asset.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return w / h


def cover_use_contain_fit(asset: dict) -> bool:
    ar = cover_asset_aspect(asset)
    return ar is not None and ar < _PORTRAIT_CONTAIN_AR


def resolve_split_mat_title_layout(title: str) -> str:
    """split-mat cover title axis: vertical | vertical-compact | horizontal."""
    text = (title or "").strip()
    n = len(text)
    if n <= 8:
        return "vertical"
    if n <= 14:
        return "vertical-compact"
    return "horizontal"


def cover_focal_point(asset: dict) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        fx, fy = 0.5, 0.45
    return max(0.0, min(1.0, fx)), max(0.0, min(1.0, fy))
