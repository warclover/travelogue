"""kept_n · 单一计数（BE-OR-10 · 与 longshot photo_count / layoutEligible 对齐）."""

from __future__ import annotations

from typing import Any


def count_kept_n(
    trip: dict[str, Any] | None = None,
    *,
    fallback: int | None = None,
) -> int:
    """策展保留且会进入长图/杂志渲染的照片数。

    优先级：
    1. curation.cullSummary.finalLayoutEligibleCount
    2. curation.cullSummary.layoutEligibleCount
    3. 显式 fallback（如 DOM 启发式）
    4. trip.assets 中 type=image 且未 culled 的数量
    """
    if trip:
        cull = (trip.get("curation") or {}).get("cullSummary") or {}
        for key in ("finalLayoutEligibleCount", "layoutEligibleCount"):
            raw = cull.get(key)
            if raw is not None and str(raw).strip() != "":
                try:
                    return max(0, int(raw))
                except (TypeError, ValueError):
                    pass
        if fallback is not None:
            try:
                return max(0, int(fallback))
            except (TypeError, ValueError):
                pass
        assets = trip.get("assets") or []
        n = 0
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if str(asset.get("type") or "image").lower() not in ("image", "photo", ""):
                continue
            if asset.get("culled") is True or asset.get("excluded") is True:
                continue
            if str(asset.get("tier") or "").lower() in ("reject", "culled", "drop"):
                continue
            n += 1
        return n
    if fallback is not None:
        try:
            return max(0, int(fallback))
        except (TypeError, ValueError):
            return 0
    return 0
