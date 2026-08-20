"""Select a magazine series and compute overflow cap (D-PFM-13 / D-PFM-21)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


def photo_span(series: Mapping[str, Any]) -> tuple[int, int]:
    raw = series.get("photo_span") or series.get("photoSpan") or [0, 0]
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        lo, hi = int(raw[0] or 0), int(raw[1] or 0)
        if hi < lo:
            lo, hi = hi, lo
        return lo, hi
    return 0, 0


PAGE_COUNT_CHIPS: tuple[int, ...] = (8, 12, 16, 20, 24, 28, 32)
PAGE_COUNT_SNAP_HINT = "非标准页数 · 按 {n} 页靠档"


def page_count_of(series: Mapping[str, Any]) -> int:
    return int(series.get("pageCount") or series.get("page_count") or 0)


def snap_to_chip(raw: int, *, max_pages: int = 32) -> int:
    """Nearest 4-multiple chip in 8…max_pages. Ties go down (D-PFM-13)."""
    chips = [c for c in PAGE_COUNT_CHIPS if c <= int(max_pages)]
    if not chips:
        return int(max_pages)
    n = int(raw)
    return min(chips, key=lambda c: (abs(c - n), c))


def snap_user_page_count(
    requested: int,
    catalog: Sequence[Mapping[str, Any]],
    *,
    max_pages: int = 32,
) -> tuple[int, str | None]:
    """Chip-snap, then nearest catalog SKU. Hint when used ≠ requested (AC-PFM-12)."""
    chip = snap_to_chip(int(requested), max_pages=max_pages)
    available = sorted(
        {
            page_count_of(s)
            for s in catalog
            if 0 < page_count_of(s) <= int(max_pages)
        }
    )
    used = chip
    if available and chip not in available:
        used = min(available, key=lambda c: (abs(c - chip), c))
    hint = PAGE_COUNT_SNAP_HINT.format(n=used) if used != int(requested) else None
    return used, hint


def _version(series: Mapping[str, Any]) -> int:
    try:
        return int(series.get("version") or 0)
    except (TypeError, ValueError):
        return 0


def _pick_latest(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        rows,
        key=lambda s: (_version(s), str(s.get("id") or "")),
        reverse=True,
    )
    return dict(ranked[0])


@dataclass(frozen=True)
class SeriesChoice:
    series: dict[str, Any]
    kept_n: int
    cap: int
    upgraded: bool
    capped: bool

    @property
    def overflow_count(self) -> int:
        return max(0, self.kept_n - self.cap)

    @property
    def overflow_resolution(self) -> str | None:
        if self.overflow_count <= 0:
            return None
        if self.upgraded and self.capped:
            return "tier_upgraded_then_capped"
        if self.upgraded:
            return "tier_upgraded"
        return "capped"


def select_series(
    catalog: Sequence[Mapping[str, Any]],
    *,
    kept_n: int,
    density: str = "standard",
    page_count: int | None = None,
    page_count_source: str = "auto",
    max_pages: int = 32,
) -> SeriesChoice | None:
    """Pick one series. ``None`` only when the catalog is empty after filters."""
    density_key = str(density or "standard").strip().lower() or "standard"
    candidates = [
        dict(s)
        for s in catalog
        if str(s.get("density") or "standard").strip().lower() == density_key
    ]
    if not candidates:
        candidates = [dict(s) for s in catalog]
    if not candidates:
        return None

    source = str(page_count_source or "auto").strip().lower()
    if source == "user" and page_count:
        pinned = [s for s in candidates if page_count_of(s) == int(page_count)]
        if not pinned:
            return None
        hit = _pick_latest(pinned)
        _, hi = photo_span(hit)
        cap = min(int(kept_n), hi) if hi > 0 else int(kept_n)
        return SeriesChoice(
            series=hit,
            kept_n=int(kept_n),
            cap=max(0, cap),
            upgraded=False,
            capped=int(kept_n) > cap,
        )

    ranked = sorted(candidates, key=lambda s: (page_count_of(s), str(s.get("id") or "")))
    initial = None
    for s in ranked:
        lo, _hi = photo_span(s)
        if lo <= kept_n:
            initial = s
            break
    if initial is None:
        initial = ranked[0]

    _, initial_hi = photo_span(initial)
    if kept_n <= initial_hi or initial_hi <= 0:
        cap = kept_n if initial_hi <= 0 else min(kept_n, initial_hi)
        return SeriesChoice(
            series=dict(initial),
            kept_n=int(kept_n),
            cap=max(0, cap),
            upgraded=False,
            capped=kept_n > cap,
        )

    upgraded_hit = None
    for s in ranked:
        pc = page_count_of(s)
        if pc <= page_count_of(initial) or pc > int(max_pages):
            continue
        _lo, hi = photo_span(s)
        if kept_n <= hi:
            upgraded_hit = s
            break
    if upgraded_hit is not None:
        _lo, hi = photo_span(upgraded_hit)
        return SeriesChoice(
            series=dict(upgraded_hit),
            kept_n=int(kept_n),
            cap=min(kept_n, hi),
            upgraded=True,
            capped=False,
        )

    ceiling = [s for s in ranked if 0 < page_count_of(s) <= int(max_pages)] or ranked
    top = ceiling[-1]
    _lo, hi = photo_span(top)
    cap = min(kept_n, hi) if hi > 0 else kept_n
    return SeriesChoice(
        series=dict(top),
        kept_n=int(kept_n),
        cap=max(0, cap),
        upgraded=page_count_of(top) > page_count_of(initial),
        capped=kept_n > cap,
    )


def groups_from_assets(
    assets: Sequence[Mapping[str, Any]] | None,
    buckets: Sequence[Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """Preserve shot-group order. Solo assets (no id) become their own group."""
    groups: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}
    if assets:
        for raw in assets:
            aid = str(raw.get("id") or raw.get("assetId") or "").strip()
            if not aid:
                continue
            gid = str(raw.get("shotGroupId") or "").strip() or f"solo-{aid}"
            kind = str(raw.get("shotGroupKind") or "scene").strip() or "scene"
            rec = index.get(gid)
            if rec is None:
                rec = {"id": gid, "kind": kind, "asset_ids": []}
                index[gid] = rec
                groups.append(rec)
            rec["asset_ids"].append(aid)
        return groups
    for i, bucket in enumerate(buckets or ()):
        ids = [str(x).strip() for x in bucket if str(x).strip()]
        if ids:
            groups.append({"id": f"bucket-{i}", "kind": "scene", "asset_ids": ids})
    return groups
